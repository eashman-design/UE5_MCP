import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Optional
from ue5_mcp.client import EditorClient


class GetTransformInput(BaseModel):
    name: str = Field(description="Exact name of the actor.")


class SetTransformInput(BaseModel):
    name: str = Field(description="Exact name of the actor.")
    location: Optional[list[float]] = Field(default=None, description="[X, Y, Z] in centimeters.")
    rotation: Optional[list[float]] = Field(default=None, description="[Pitch, Yaw, Roll] in degrees.")
    scale: Optional[list[float]] = Field(default=None, description="[X, Y, Z] scale.")


TOOLS: list[Tool] = [
    Tool(
        name="get_actor_transform",
        description="Get the location, rotation, and scale of a named actor in the current level.",
        inputSchema=GetTransformInput.model_json_schema(),
    ),
    Tool(
        name="set_actor_transform",
        description=(
            "Set location, rotation, and/or scale on a named actor. "
            "Any omitted fields are left unchanged."
        ),
        inputSchema=SetTransformInput.model_json_schema(),
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


async def handle(name: str, client: EditorClient, arguments: dict) -> list[TextContent]:
    if name == "get_actor_transform":
        inp = GetTransformInput.model_validate(arguments)
        data = await client.post("/transform/get", {"name": inp.name})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    if name == "set_actor_transform":
        inp = SetTransformInput.model_validate(arguments)
        body: dict = {"name": inp.name}
        if inp.location is not None:
            body["location"] = inp.location
        if inp.rotation is not None:
            body["rotation"] = inp.rotation
        if inp.scale is not None:
            body["scale"] = inp.scale
        data = await client.post("/transform/set", body)
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown transform tool: {name}")
