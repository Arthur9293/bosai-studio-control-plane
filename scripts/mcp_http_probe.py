from __future__ import annotations

import asyncio

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_URL = "http://127.0.0.1:8010/"
MCP_ORIGIN = "http://127.0.0.1:8010"
TARGET_TOOL = "query_loki_logs"


async def main() -> None:
    # The MCP Python SDK currently does not synthesize an Origin header for
    # Streamable HTTP. The official Go MCP server security layer may reject
    # state-changing POSTs that cannot prove same-origin. Supply the exact local
    # origin while preserving the server's host/origin protection.
    async with httpx.AsyncClient(headers={"Origin": MCP_ORIGIN}) as http_client:
        async with streamable_http_client(MCP_URL, http_client=http_client) as (
            read_stream,
            write_stream,
            _get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = [tool.name for tool in tools.tools]
                print("MCP_HTTP_INITIALIZE=PASS")
                print(f"MCP_HTTP_TARGET_TOOL_PRESENT={str(TARGET_TOOL in names).lower()}")
                print(f"MCP_HTTP_TOOL_COUNT={len(names)}")


if __name__ == "__main__":
    asyncio.run(main())
