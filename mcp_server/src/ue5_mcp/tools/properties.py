import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Any
from ue5_mcp.client import EditorClient


class GetPropertyInput(BaseModel):
    actor_name: str = Field(description="Exact name of the actor.")
    property_name: str = Field(description="Name of the UPROPERTY to read.")


class SetPropertyInput(BaseModel):
    actor_name: str = Field(description="Exact name of the actor.")
    property_name: str = Field(description="Name of the UPROPERTY to write.")
    value: str = Field(
        description=(
            "Value as string. Formats: bool='true'/'false', int='42', float='3.14', "
            "FVector='X=1.0 Y=2.0 Z=3.0', FRotator='P=0.0 Y=90.0 R=0.0', "
            "FLinearColor='(R=1.0,G=0.5,B=0.0,A=1.0)'"
        )
    )


TOOLS: list[Tool] = [
    Tool(
        name="get_property",
        description=(
            "Read a UPROPERTY from a named actor via UE5 reflection. "
            "Supported types: bool, int32, float, FString, FName, FVector, FRotator, FLinearColor."
        ),
        inputSchema=GetPropertyInput.model_json_schema(),
    ),
    Tool(
        name="set_property",
        description=(
            "Write a UPROPERTY on a named actor via UE5 reflection. "
            "Value must be a string in the format the engine expects (see field description)."
        ),
        inputSchema=SetPropertyInput.model_json_schema(),
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


async def handle(name: str, client: EditorClient, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "get_property":
        inp = GetPropertyInput.model_validate(arguments)
        data = await client.post("/property/get", {
            "actor_name": inp.actor_name,
            "property_name": inp.property_name,
        })
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    if name == "set_property":
        inp = SetPropertyInput.model_validate(arguments)
        data = await client.post("/property/set", {
            "actor_name": inp.actor_name,
            "property_name": inp.property_name,
            "value": inp.value,
        })
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown property tool: {name}")
