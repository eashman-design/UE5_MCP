import pytest
import respx
from ue5_mcp.client import EditorClient


@pytest.fixture
def mock_editor():
    """Mocks the plugin HTTP server. Use as a context manager or fixture."""
    with respx.mock(base_url="http://localhost:8765/api/v1") as mock:
        yield mock


@pytest.fixture
def editor_client() -> EditorClient:
    return EditorClient("http://localhost:8765/api/v1", timeout=5.0)
