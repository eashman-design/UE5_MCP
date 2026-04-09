import httpx
from typing import Any


class EditorConnectionError(Exception):
    """Raised when the plugin HTTP server cannot be reached."""


class EditorError(Exception):
    """Raised when the plugin returns ok=false."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class EditorClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        try:
            r = await self._client.get(path, params=params)
            return self._unwrap(r)
        except httpx.ConnectError as e:
            raise EditorConnectionError(
                "Cannot reach UE5 editor. Is the plugin running and the editor open?"
            ) from e

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            r = await self._client.post(path, json=body)
            return self._unwrap(r)
        except httpx.ConnectError as e:
            raise EditorConnectionError(
                "Cannot reach UE5 editor. Is the plugin running and the editor open?"
            ) from e

    def _unwrap(self, response: httpx.Response) -> dict[str, Any]:
        payload = response.json()
        if not payload.get("ok"):
            raise EditorError(
                message=payload.get("error", "Unknown error"),
                code=payload.get("code", "UNKNOWN"),
            )
        return payload.get("data", {})

    async def aclose(self) -> None:
        await self._client.aclose()
