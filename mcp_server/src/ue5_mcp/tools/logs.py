import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Optional
from ue5_mcp.client import EditorClient


class GetLogInput(BaseModel):
    count: Optional[int] = Field(
        default=200,
        description="Number of log lines to return. Clamped to [1, 2000]. Default 200.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional category substring filter, e.g. 'LogBlueprintUserMessages'.",
    )


TOOLS: list[Tool] = [
    Tool(
        name="get_log",
        description=(
            "Retrieve recent lines from the UE5 editor output log. "
            "Optionally filter by log category substring."
        ),
        inputSchema=GetLogInput.model_json_schema(),
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


async def handle(name: str, client: EditorClient, arguments: dict) -> list[TextContent]:
    if name == "get_log":
        inp = GetLogInput.model_validate(arguments)
        params: dict = {"count": inp.count or 200}
        if inp.category:
            params["category"] = inp.category
        data = await client.get("/logs/get", **params)
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown log tool: {name}")
