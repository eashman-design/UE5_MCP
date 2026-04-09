import pytest
import httpx
from ue5_mcp.tools.actors import handle
from ue5_mcp.client import EditorError


@pytest.mark.asyncio
async def test_list_actors_success(mock_editor, editor_client):
    mock_editor.get("/actors/list").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"actors": [{"name": "Floor", "class": "StaticMeshActor", "id": "abc123"}]},
    }))
    result = await handle("list_actors", editor_client, {})
    assert len(result) == 1
    assert "Floor" in result[0].text


@pytest.mark.asyncio
async def test_spawn_actor_success(mock_editor, editor_client):
    mock_editor.post("/actors/spawn").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"name": "MyActor_1", "id": "def456"},
    }))
    result = await handle("spawn_actor", editor_client, {
        "class_path": "/Script/Engine.StaticMeshActor",
        "name": "MyActor_1",
    })
    assert "MyActor_1" in result[0].text


@pytest.mark.asyncio
async def test_delete_actor_success(mock_editor, editor_client):
    mock_editor.post("/actors/delete").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"deleted": "MyActor_1"},
    }))
    result = await handle("delete_actor", editor_client, {"name": "MyActor_1"})
    assert "MyActor_1" in result[0].text


@pytest.mark.asyncio
async def test_list_actors_editor_error(mock_editor, editor_client):
    mock_editor.get("/actors/list").mock(return_value=httpx.Response(200, json={
        "ok": False,
        "error": "No editor world available",
        "code": "NO_WORLD",
    }))
    with pytest.raises(EditorError) as exc_info:
        await handle("list_actors", editor_client, {})
    assert exc_info.value.code == "NO_WORLD"
