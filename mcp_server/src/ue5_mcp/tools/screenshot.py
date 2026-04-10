import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Any, Optional
from ue5_mcp.client import EditorClient


class CaptureScreenshotInput(BaseModel):
    filename: Optional[str] = Field(
        default=None,
        description="Optional filename (without path). Defaults to ue5mcp_<timestamp>.png.",
    )


TOOLS: list[Tool] = [
    Tool(
        name="capture_screenshot",
        description=(
            "Capture a screenshot of the active viewport. "
            "Returns the absolute path to the saved PNG in Saved/Screenshots/."
        ),
        inputSchema=CaptureScreenshotInput.model_json_schema(),
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


async def handle(name: str, client: EditorClient, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "capture_screenshot":
        inp = CaptureScreenshotInput.model_validate(arguments)
        body: dict[str, Any] = {}
        if inp.filename:
            body["filename"] = inp.filename
        data = await client.post("/screenshot/capture", body)
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown screenshot tool: {name}")
