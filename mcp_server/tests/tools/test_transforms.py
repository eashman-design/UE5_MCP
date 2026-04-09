import pytest
import httpx
from ue5_mcp.tools.transforms import handle
from ue5_mcp.client import EditorError


@pytest.mark.asyncio
async def test_get_transform_success(mock_editor, editor_client):
    mock_editor.post("/transform/get").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"location": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]},
    }))
    result = await handle("get_actor_transform", editor_client, {"name": "Floor"})
    assert "location" in result[0].text


@pytest.mark.asyncio
async def test_get_transform_not_found(mock_editor, editor_client):
    mock_editor.post("/transform/get").mock(return_value=httpx.Response(200, json={
        "ok": False, "error": "Actor 'Bogus' not found.", "code": "ACTOR_NOT_FOUND",
    }))
    with pytest.raises(EditorError) as exc_info:
        await handle("get_actor_transform", editor_client, {"name": "Bogus"})
    assert exc_info.value.code == "ACTOR_NOT_FOUND"
