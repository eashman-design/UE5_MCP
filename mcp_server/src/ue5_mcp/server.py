from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import Any
from ue5_mcp.config import Config
from ue5_mcp.client import EditorClient
import ue5_mcp.tools.actors as actors_tools
import ue5_mcp.tools.transforms as transform_tools
import ue5_mcp.tools.properties as property_tools
import ue5_mcp.tools.console as console_tools
import ue5_mcp.tools.pie as pie_tools
import ue5_mcp.tools.screenshot as screenshot_tools
import ue5_mcp.tools.logs as logs_tools


def create_server(config: Config) -> Server:
    server = Server("ue5-mcp")
    client = EditorClient(config.editor_base_url, config.request_timeout)

    all_tool_modules = [
        actors_tools,
        transform_tools,
        property_tools,
        console_tools,
        pie_tools,
        screenshot_tools,
        logs_tools,
    ]

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        for module in all_tool_modules:
            tools.extend(module.TOOLS)
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        for module in all_tool_modules:
            if name in module.TOOL_NAMES:
                return await module.handle(name, client, arguments)
        raise ValueError(f"Unknown tool: {name}")

    return server
