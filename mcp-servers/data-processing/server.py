"""Data processing MCP server.

Provides tools: query_db, insert_record, update_record, delete_record, bulk_import, export_report, validate_data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp.server import Server
from mcp.types import TextContent, Tool

from core.common.config import get_settings
from core.common.logging import get_logger

logger = get_logger(__name__)

server = Server("data-processing")
settings = get_settings()


@server.tool()
async def query_db(sql: str, params: list | None = None, max_rows: int = 1000) -> list[dict]:
    """Execute a parameterized SQL query (SELECT only).

    Args:
        sql: SQL query with ? placeholders
        params: Query parameters
        max_rows: Maximum rows to return
    """
    logger.info("mcp_data.query_db", sql_preview=sql[:100])
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries allowed in query_db")
    if ";" in sql.rstrip(";"):
        raise ValueError("Multiple statements not allowed")

    # M1 stub: return mock data
    return [
        {"id": 1, "name": "Sample row 1", "sql": sql[:50]},
        {"id": 2, "name": "Sample row 2", "params": params or []},
    ][:max_rows]


@server.tool()
async def insert_record(table: str, data: dict) -> dict:
    """Insert a record into a table.

    Args:
        table: Table name
        data: Column-value mapping
    """
    logger.info("mcp_data.insert", table=table, keys=list(data.keys()))
    return {"success": True, "table": table, "inserted": data, "id": "stub_id"}


@server.tool()
async def update_record(table: str, record_id: str | int, data: dict) -> dict:
    """Update a record by ID.

    Args:
        table: Table name
        record_id: Record ID
        data: New column values
    """
    logger.info("mcp_data.update", table=table, record_id=record_id)
    return {"success": True, "table": table, "record_id": record_id, "updated": data}


@server.tool()
async def delete_record(table: str, record_id: str | int) -> dict:
    """Delete a record by ID. HIGH RISK.

    Args:
        table: Table name
        record_id: Record ID
    """
    logger.warning("mcp_data.delete", table=table, record_id=record_id)
    return {"success": True, "table": table, "deleted": record_id}


@server.tool()
async def bulk_import(table: str, csv_path: str) -> dict:
    """Bulk import CSV to table.

    Args:
        table: Target table
        csv_path: Path to CSV file
    """
    logger.info("mcp_data.bulk_import", table=table, csv_path=csv_path)
    return {"success": True, "imported_rows": 0, "table": table, "path": csv_path}


@server.tool()
async def export_report(query: str, format: str = "csv") -> dict:
    """Export query results to a file.

    Args:
        query: SQL query
        format: csv | json | xlsx
    """
    logger.info("mcp_data.export", format=format, query_preview=query[:50])
    return {
        "success": True,
        "format": format,
        "file_path": f"./workspace/exports/{format}_export.{format}",
        "row_count": 0,
    }


@server.tool()
async def validate_data(table: str, schema: dict) -> dict:
    """Validate data in a table against schema.

    Args:
        table: Table name
        schema: JSON schema dict
    """
    logger.info("mcp_data.validate", table=table, schema_keys=list(schema.keys()))
    return {"success": True, "table": table, "valid_rows": 0, "invalid_rows": 0}


if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio())
