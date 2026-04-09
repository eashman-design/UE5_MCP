# UE5-MCP

Give Claude Code (and any MCP-compatible AI) direct programmatic control over a running Unreal Engine 5.5 Editor.

## Features (Tier 1 — v0.1.0)

- List, spawn, and delete actors
- Get and set actor transforms
- Get and set actor properties via UE5 reflection (bool, int, float, FString, FVector, FRotator, FLinearColor)
- Execute console commands
- Start, stop, and query PIE state
- Capture viewport screenshots
- Read the editor output log

## Architecture

```
Claude Code → MCP (stdio) → Python ue5_mcp server → HTTP :8765 → UE5 Plugin
```

See [DESIGN.md](DESIGN.md) for the full architecture and [docs/](docs/) for guides.

## Installation

### Plugin

1. Copy `plugin/UE5MCP/` into `YourProject/Plugins/`
2. Open UE5 — it will prompt to rebuild. Confirm.
3. Enable via **Edit > Plugins > UE5 MCP** if not auto-enabled.
4. Check the Output Log for: `UE5MCP HTTP server started on port 8765`

### MCP Server

```bash
pip install ue5-mcp
```

From source:

```bash
cd mcp_server
pip install -e .
```

### Verify Connection

With the editor open and plugin running:

```bash
curl http://localhost:8765/api/v1/actors/list
```

Expected: `{"ok":true,"data":{"actors":[...]}}`

### Claude Code Config

Add to your Claude Code MCP config (`~/.claude/claude_desktop_config.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "ue5": {
      "command": "ue5-mcp",
      "args": ["--editor-port", "8765"]
    }
  }
}
```

Restart Claude Code. The UE5 tool set will appear in Claude's available tools.

## License

MIT — see [LICENSE](LICENSE).
