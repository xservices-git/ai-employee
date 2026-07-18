# MCP Tools Catalog

## Tổng quan

Hệ thống expose các tool qua **Model Context Protocol (MCP)** chuẩn. Mỗi tool:
- Có JSON schema cho input
- Có risk level (low/medium/high/critical)
- Có timeout
- Có rate limit
- Có audit log

## Architecture

```
┌─────────────────┐
│  Orchestrator   │
│  (Executor)     │
└────────┬────────┘
         │ MCP JSON-RPC
         ▼
┌─────────────────┐
│  MCP Registry   │  (in-process, knows all servers)
└────────┬────────┘
         │
   ┌─────┴─────┬─────────┬──────────┬──────────┐
   ▼           ▼         ▼          ▼          ▼
┌──────┐  ┌────────┐ ┌───────┐ ┌────────┐ ┌────────┐
│ data │  │ comms  │ │ file  │ │ sched  │ │ web    │
└──────┘  └────────┘ └───────┘ └────────┘ └────────┘
```

Mỗi server chạy như 1 process riêng (subprocess) hoặc 1 Docker container.

## MCP servers

### 1. data-processing
Mục đích: Query, insert, update, delete data trong databases.

| Tool | Risk | Description |
|---|---|---|
| `query_db` | low | SELECT với SQL parameterized |
| `insert_record` | medium | INSERT single record |
| `update_record` | high | UPDATE record theo ID |
| `delete_record` | critical | DELETE record (cần approval) |
| `bulk_import` | high | Import CSV vào table |
| `export_report` | low | Export data ra CSV/Excel |
| `validate_data` | low | Validate data theo schema |

**Schema ví dụ:**
```json
{
  "name": "query_db",
  "description": "Execute a parameterized SQL query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": {
        "type": "string",
        "description": "SQL query với ? placeholders"
      },
      "params": {
        "type": "array",
        "items": {"type": ["string", "number", "boolean", "null"]}
      },
      "max_rows": {
        "type": "integer",
        "default": 1000,
        "maximum": 10000
      }
    },
    "required": ["sql"]
  }
}
```

**Safety constraints:**
- Chỉ SELECT (hoặc INSERT/UPDATE/DELETE tương ứng tool)
- Không cho phép `DROP`, `TRUNCATE`, `ALTER`
- Không cho phép `;` trong SQL (chỉ 1 statement)
- Whitelist tables nếu config

### 2. communication
Mục đích: Gửi email, SMS, Teams, tạo draft.

| Tool | Risk | Description |
|---|---|---|
| `send_email` | high | Gửi email thật (cần approval) |
| `create_draft` | medium | Tạo email draft (không gửi) |
| `send_sms` | high | Gửi SMS |
| `send_teams` | high | Gửi Teams message |
| `create_meeting` | medium | Tạo calendar event |

**Schema ví dụ:**
```json
{
  "name": "send_email",
  "description": "Send an email via SMTP",
  "inputSchema": {
    "type": "object",
    "properties": {
      "to": {"type": "array", "items": {"type": "string", "format": "email"}},
      "cc": {"type": "array", "items": {"type": "string", "format": "email"}},
      "subject": {"type": "string", "maxLength": 200},
      "body": {"type": "string", "maxLength": 100000},
      "html": {"type": "boolean", "default": false},
      "attachments": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["to", "subject", "body"]
  }
}
```

**Safety constraints:**
- Tối đa 10 recipients
- PII detection trước khi gửi
- Confirm recipient có trong whitelist (nếu config)
- Rate limit: 100 emails/hour/user
- Tất cả emails gửi đi cũng lưu vào `sent_emails` table

### 3. file-operations
Mục đích: Đọc, ghi, search, convert files.

| Tool | Risk | Description |
|---|---|---|
| `read_file` | low | Đọc file trong workspace |
| `write_file` | medium | Ghi file (overwrite hoặc new) |
| `search_files` | low | Tìm file theo glob/regex |
| `convert_format` | medium | Convert PDF→text, DOCX→text, etc. |
| `delete_file` | high | Xóa file (cần approval) |
| `move_file` | medium | Di chuyển file |

**Safety constraints:**
- Chỉ truy cập thư mục `WORKSPACE_DIR` (config)
- Không truy cập `..` (path traversal blocked)
- File size limit: 100MB
- Không xóa file `.env`, `*.key`, `*.pem` (whitelist protected files)

### 4. scheduling
Mục đích: Tạo event, reminder, cron.

| Tool | Risk | Description |
|---|---|---|
| `create_event` | medium | Tạo calendar event |
| `check_calendar` | low | Xem lịch |
| `set_reminder` | low | Tạo reminder (qua cron) |
| `find_slot` | low | Tìm slot trống |
| `cancel_event` | high | Hủy event (cần approval) |

### 5. web-research
Mục đích: Search web, fetch URL, summarize, translate.

| Tool | Risk | Description |
|---|---|---|
| `web_search` | low | Search Google/Brave/DDG |
| `fetch_url` | low | Fetch URL → markdown |
| `summarize_text` | low | Summarize text dài |
| `translate` | low | Dịch text |

**Safety constraints:**
- Domain whitelist (không fetch từ .onion, localhost)
- Max page size: 5MB
- Timeout: 30s
- Cache result 1h để tránh fetch lặp
- User agent có identification (không phải bot ẩn danh)

## Tool Registry

Mỗi tool phải đăng ký trong `domain_configs/tools.yaml`:

```yaml
tools:
  - name: query_db
    server: data-processing
    risk: low
    timeout_sec: 10
    rate_limit:
      per_user: 1000
      per_hour: true
    requires_approval: false
    description: "Read-only database query"

  - name: send_email
    server: communication
    risk: high
    timeout_sec: 30
    rate_limit:
      per_user: 100
      per_hour: true
    requires_approval: true
    description: "Send email via SMTP"
    approval_reason: "External communication - verify recipient and content"
```

## MCP Server Implementation

Mỗi server là 1 Python process, dùng `mcp` package:

```python
# mcp-servers/data-processing/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

server = Server("data-processing")

@server.tool()
async def query_db(sql: str, params: list = None, max_rows: int = 1000) -> list[dict]:
    """Execute a parameterized SQL query."""
    # Safety: only SELECT
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries allowed")

    # Safety: no multiple statements
    if ";" in sql.rstrip(";"):
        raise ValueError("Multiple statements not allowed")

    # Connect and execute
    import aiosqlite
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params or []) as cursor:
            rows = await cursor.fetchmany(max_rows)
            return [dict(row) for row in rows]

if __name__ == "__main__":
    asyncio.run(server.run_stdio())
```

## Tool Call Flow

```
1. Executor decide gọi tool "query_db" với args
2. Check risk: low
3. Check rate limit: OK
4. Check approval: không cần
5. Gọi MCP server qua JSON-RPC
6. Nhận response
7. Validate response theo schema
8. Lưu vào task.result
9. Log audit
```

## Error handling

| Error type | Behavior |
|---|---|
| Timeout | Retry 1 lần, fail nếu vẫn timeout |
| Rate limit | Return 429, Executor skip task |
| Validation | Return 400 với chi tiết |
| Tool crash | Restart tool server, retry |
| Permission denied | Return 403, gợi ý user cấp quyền |

## Adding new tool

1. Tạo function trong MCP server tương ứng
2. Thêm vào `tools.yaml` registry
3. Test với `mcp-inspector`
4. Document trong docs
5. Add eval cases

## Cải tiến so với bản gốc

| Khía cảnh | Bản gốc | V3.0 |
|---|---|---|
| Protocol | Custom | MCP chuẩn |
| Risk classification | Không | 4 levels |
| Approval | Không tự động | Tự động theo risk |
| Rate limit | Không | Per user/tool |
| Audit | Không | Mọi call |
| Adding tool | Sửa core | Chỉ thêm function |
| Testing | Không | mcp-inspector + eval |
