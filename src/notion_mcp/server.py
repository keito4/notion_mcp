from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
import logging
from typing import Any, Sequence

from .tools.handlers import TOOL_HANDLERS
from .api.notion import NotionClient
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('notion_mcp')

server = Server("notion-todo")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(
        name=key,
        description=tool["description"],
        inputSchema=tool["inputSchema"]
    ) for key, tool in TOOL_HANDLERS.items()]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | EmbeddedResource]:
    if not isinstance(arguments, dict):
        return [TextContent(type="text", text="Invalid arguments, must be an object")]

    if name not in TOOL_HANDLERS:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    handler = TOOL_HANDLERS[name]["handler"]
    try:
        return await handler(arguments)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return [
            TextContent(
                type="text",
                text=f"An unexpected error occurred: {str(e)}"
            )
        ]


async def main():
    """Main entry point for the server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
