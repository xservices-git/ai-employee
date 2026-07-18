# MCP Tools Catalog

## Tong quan

Tool expose qua **Model Context Protocol (MCP)** chuan JSON-RPC. Moi tool:
- JSON schema cho input
- Risk level (low/medium/high/critical)
- Timeout + rate limit
- Audit log

## 5 MCP servers

### 1. data-processing

| Tool | Risk | Description |
|---|---|---|
| `query_db` | low | SELECT parameterized |
| `insert_record` | medium | INSERT single |
| `update_record` | high | UPDATE theo ID |
| `delete_record` | critical | DELETE (can approval) |
| `bulk_import` | high | Import CSV |
| `export_report` | low | Export CSV/Excel |
| `validate_data` | low | Validate schema |

**Safety:**
- Chi SELECT (hoac INSERT/UPDATE/DELETE tuong ung tool)
- KHONG cho `DROP`, `TRUNCATE`, `ALTER`
- KHONG cho `;` trong SQL (1 statement)
- Whitelist tables neu config

### 2. communication

| Tool | Risk | Description |
|---|---|---|
| `send_email` | high | Gui email that (can approval) |
| `create_draft` | medium | Tao draft (khong gui) |
| `send_sms` | high | Gui SMS |
| `send_teams` | high | Gui Teams |
| `create_meeting` | medium | Tao calendar event |

**Safety:**
- Max 10 recipients
- PII detection truoc khi gui
- Recipient whitelist (neu config)
- Rate limit: 100 emails/hour/user

### 3. file-operations

| Tool | Risk | Description |
|---|---|---|
| `read_file` | low | Doc file trong workspace |
| `write_file` | medium | Ghi file |
| `search_files` | low | Tim file theo glob/regex |
| `convert_format` | medium | PDF->text, DOCX->text |
| `delete_file` | high | Xoa file (can approval) |
| `move_file` | medium | Di chuyen file |

**Safety:**
- Chi truy cap `WORKSPACE_DIR`
- KHONG `..` (path traversal blocked)
- Max file size: 100MB
- Protected: `.env`, `*.key`, `*.pem`

### 4. scheduling

| Tool | Risk | Description |
|---|---|---|
| `create_event` | medium | Tao event |
| `check_calendar` | low | Xem lich |
| `set_reminder` | low | Tao reminder |
| `find_slot` | low | Tim slot trong |
| `cancel_event` | high | Huy event (can approval) |

### 5. web-research

| Tool | Risk | Description |
|---|---|---|
| `web_search` | low | Search web |
| `fetch_url` | low | Fetch URL -> markdown |
| `summarize_text` | low | Summarize |
| `translate` | low | Dich |

**Safety:**
- Domain whitelist (khong fetch .onion, localhost)
- Max page size: 5MB
- Timeout: 30s
- Cache 1h

## Tool Registry (YAML)

```yaml
# domain_configs/tools.yaml
tools:
  - name: query_db
    server: data-processing
    risk: low
    timeout_sec: 10
    rate_limit: {per_user: 1000, per_hour: true}
    requires_approval: false
    description: "Read-only DB query"

  - name: send_email
    server: communication
    risk: high
    timeout_sec: 30
    rate_limit: {per_user: 100, per_hour: true}
    requires_approval: true
    description: "Send email via SMTP"
    approval_reason: "External communication"
```

## Implementation

Moi server = 1 Python process, dung `mcp` package:

```python
from mcp.server import Server
server = Server("data-processing")

@server.tool()
async def query_db(sql: str, params: list = None, max_rows: int = 1000) -> list[dict]:
    # Validate (1 statement, khong DROP/TRUNCATE/ALTER)
    if any(kw in sql.upper() for kw in ["DROP", "TRUNCATE", "ALTER", ";"]):
        raise ValueError("Forbidden SQL keyword")
    async with db.connect() as conn:
        rows = await conn.execute(sql, params or [])
        return [dict(r) for r in rows.fetchmany(max_rows)]
```

## So voi spec cu

| Kha canh | Spec cu | Spec moi |
|---|---|---|
| So servers | 5 | 5 (giong) |
| So tools | ~20 | ~20 (giong) |
| Risk levels | 4 | 4 (giong) |
| Custom tool? | Co | KHONG - chi 5 servers chuan |
