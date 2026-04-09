import pytest
import httpx
from ue5_mcp.tools.console import handle
from ue5_mcp.client import EditorError


@pytest.mark.asyncio
async def test_execute_console_success(mock_editor, editor_client):
    mock_editor.post("/console/execute").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"command": "stat fps"},
    }))
    result = await handle("execute_console_command", editor_client, {"command": "stat fps"})
    assert "stat fps" in result[0].text


@pytest.mark.asyncio
async def test_execute_console_invalid_body(mock_editor, editor_client):
    mock_editor.post("/console/execute").mock(return_value=httpx.Response(200, json={
        "ok": False, "error": "Missing 'command' field.", "code": "INVALID_REQUEST_BODY",
    }))
    with pytest.raises(EditorError) as exc_info:
        await handle("execute_console_command", editor_client, {"command": ""})
    assert exc_info.value.code == "INVALID_REQUEST_BODY"
