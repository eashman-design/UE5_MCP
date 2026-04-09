import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from ue5_mcp.client import EditorClient


class ExecuteConsoleInput(BaseModel):
    command: str = Field(description="Console command to execute in the UE5 editor.")


TOOLS: list[Tool] = [
    Tool(
        name="execute_console_command",
        description=(
            "Execute a console command in the UE5 editor. "
            "Returns the command string that was executed. Check get_log for any output."
        ),
        inputSchema=ExecuteConsoleInput.model_json_schema(),
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


async def handle(name: str, client: EditorClient, arguments: dict) -> list[TextContent]:
    if name == "execute_console_command":
        inp = ExecuteConsoleInput.model_validate(arguments)
        data = await client.post("/console/execute", {"command": inp.command})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown console tool: {name}")
