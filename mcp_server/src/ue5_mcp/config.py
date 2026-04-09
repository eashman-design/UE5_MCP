import argparse
from dataclasses import dataclass


@dataclass
class Config:
    editor_port: int = 8765
    editor_host: str = "localhost"
    request_timeout: float = 30.0
    log_level: str = "INFO"

    @property
    def editor_base_url(self) -> str:
        return f"http://{self.editor_host}:{self.editor_port}/api/v1"

    @classmethod
    def from_args(cls) -> "Config":
        parser = argparse.ArgumentParser(description="UE5 MCP Server")
        parser.add_argument("--editor-port", type=int, default=8765)
        parser.add_argument("--editor-host", type=str, default="localhost")
        parser.add_argument("--timeout", type=float, default=30.0)
        parser.add_argument("--log-level", type=str, default="INFO")
        args = parser.parse_args()
        return cls(
            editor_port=args.editor_port,
            editor_host=args.editor_host,
            request_timeout=args.timeout,
            log_level=args.log_level,
        )
