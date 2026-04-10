import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Any, Literal
from ue5_mcp.client import EditorClient


class StartPIEInput(BaseModel):
    mode: Literal["selected_viewport", "simulate", "new_window"] = Field(
        default="selected_viewport",
        description="PIE mode: selected_viewport, simulate, or new_window.",
    )


TOOLS: list[Tool] = [
    Tool(
        name="start_pie",
        description="Start Play In Editor (PIE). Returns PIE_ALREADY_RUNNING if PIE is active.",
        inputSchema=StartPIEInput.model_json_schema(),
    ),
    Tool(
        name="stop_pie",
        description="Stop Play In Editor (PIE). Returns PIE_NOT_RUNNING if PIE is not active.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_pie_state",
        description="Get current PIE state: 'running', 'stopped', or 'paused'.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


async def handle(name: str, client: EditorClient, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "start_pie":
        inp = StartPIEInput.model_validate(arguments)
        data = await client.post("/pie/start", {"mode": inp.mode})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    if name == "stop_pie":
        data = await client.post("/pie/stop", {})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    if name == "get_pie_state":
        data = await client.get("/pie/state")
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown PIE tool: {name}")
