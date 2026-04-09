import pytest
import httpx
from ue5_mcp.tools.properties import handle
from ue5_mcp.client import EditorError


@pytest.mark.asyncio
async def test_get_property_success(mock_editor, editor_client):
    mock_editor.post("/property/get").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"actor_name": "Light1", "property_name": "Intensity", "value": "5000.0", "type": "float"},
    }))
    result = await handle("get_property", editor_client, {
        "actor_name": "Light1", "property_name": "Intensity",
    })
    assert "5000.0" in result[0].text


@pytest.mark.asyncio
async def test_get_property_unsupported_type(mock_editor, editor_client):
    mock_editor.post("/property/get").mock(return_value=httpx.Response(200, json={
        "ok": False,
        "error": "Property type 'UStaticMesh*' is not supported.",
        "code": "UNSUPPORTED_PROPERTY_TYPE",
    }))
    with pytest.raises(EditorError) as exc_info:
        await handle("get_property", editor_client, {
            "actor_name": "Mesh1", "property_name": "StaticMesh",
        })
    assert exc_info.value.code == "UNSUPPORTED_PROPERTY_TYPE"
