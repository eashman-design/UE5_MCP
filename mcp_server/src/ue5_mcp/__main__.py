import asyncio
from ue5_mcp.server import create_server
from ue5_mcp.config import Config


def main() -> None:
    config = Config.from_args()
    server = create_server(config)
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
