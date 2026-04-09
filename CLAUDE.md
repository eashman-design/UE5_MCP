# CLAUDE.md — UE5-MCP

Authoritative guide for Claude Code working on this repo. Read DESIGN.md for full details — this file surfaces the rules you are most likely to forget or violate.

---

## What This Project Is

UE5-MCP gives Claude Code (and any MCP client) programmatic control over a running Unreal Engine 5.5 Editor via:

```
Claude Code → MCP stdio → Python ue5_mcp package → HTTP :8765 → UE5 C++ Plugin → UE5 Editor APIs
```

Two components:
- **`plugin/UE5MCP/`** — C++ UE5 editor plugin. Embedded HTTP server. All UObject work happens here.
- **`mcp_server/`** — Python package. Translates MCP tool calls to HTTP requests. Zero UE5 knowledge.

---

## THE Most Important Rule: Threading

**All UObject access must happen on the game thread.** FHttpServerModule delivers requests on a background thread pool. Every handler must dispatch via `AsyncTask`:

```cpp
Router->BindRoute(FHttpPath(TEXT("/api/v1/actors/list")), EHttpServerRequestVerbs::VERB_GET,
    [](const FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
    {
        // HTTP thread — do NOT touch UObjects here
        AsyncTask(ENamedThreads::GameThread, [OnComplete]()
        {
            // Game thread — safe to access GEditor, UWorld, AActor, etc.
            UWorld* World = GEditor->GetEditorWorldContext().World();
            // ... do work ...
            OnComplete(FUE5MCPResponseHelpers::BuildSuccessResponse(DataObj));
        });
        return true; // accept the request; OnComplete called async
    }
);
```

Violating this causes crashes that are hard to reproduce. No exceptions, no special cases.

---

## 9 Other Non-Negotiable Rules (DESIGN.md §9)

1. Every plugin response uses `BuildSuccessResponse` or `BuildErrorResponse` — never hand-construct JSON.
2. HTTP status is always **200**. `"ok": false` is how errors are signaled, not 4xx/5xx.
3. `OnComplete` is called **exactly once** per request. Leaking it hangs clients; calling twice is UB.
4. All editor-only `Build.cs` deps inside `if (Target.bBuildEditor)`. All editor-only includes inside `#if WITH_EDITOR`. Console builds must compile clean.
5. Tool names are **frozen after v0.1.0**. Renaming = breaking change = major version bump.
6. `get_property`/`set_property` only support: `bool`, `int32`, `float`, `FString`, `FName`, `FVector`, `FRotator`, `FLinearColor`. Anything else → `UNSUPPORTED_PROPERTY_TYPE`.
7. Python client does **not retry** on `EditorError`. Only optionally retries `EditorConnectionError`.
8. Log capture uses `GLog->AddOutputDevice` only — never read log files from disk (locked on Windows).
9. `FUE5MCPLogCapture::Serialize` always acquires `Lock` before touching `Buffer`.

---

## Error Code Reference (DESIGN.md §4.12)

| Code | Meaning |
|---|---|
| `NO_WORLD` | Editor world not available |
| `ACTOR_NOT_FOUND` | Named actor not in current world |
| `CLASS_NOT_FOUND` | UClass could not be resolved |
| `PROPERTY_NOT_FOUND` | Property not on actor class |
| `UNSUPPORTED_PROPERTY_TYPE` | Outside Tier 1 type set |
| `IMPORT_TEXT_FAILED` | Value string parse failed |
| `PIE_ALREADY_RUNNING` | PIE start requested but already active |
| `PIE_NOT_RUNNING` | PIE stop requested but not active |
| `SCREENSHOT_FAILED` | Viewport capture failed |
| `INVALID_REQUEST_BODY` | JSON malformed or missing required fields |
| `SPAWN_FAILED` | SpawnActor returned null |
| `INTERNAL_ERROR` | Unexpected failure — check Output Log |

---

## Tool Name Registry (DESIGN.md §7) — Frozen at v0.1.0

| MCP Tool | Plugin Endpoint | Tier |
|---|---|---|
| `list_actors` | `GET /api/v1/actors/list` | 1 |
| `spawn_actor` | `POST /api/v1/actors/spawn` | 1 |
| `delete_actor` | `POST /api/v1/actors/delete` | 1 |
| `get_actor_transform` | `POST /api/v1/transform/get` | 1 |
| `set_actor_transform` | `POST /api/v1/transform/set` | 1 |
| `get_property` | `POST /api/v1/property/get` | 1 |
| `set_property` | `POST /api/v1/property/set` | 1 |
| `execute_console_command` | `POST /api/v1/console/execute` | 1 |
| `start_pie` | `POST /api/v1/pie/start` | 1 |
| `stop_pie` | `POST /api/v1/pie/stop` | 1 |
| `get_pie_state` | `GET /api/v1/pie/state` | 1 |
| `capture_screenshot` | `POST /api/v1/screenshot/capture` | 1 |
| `get_log` | `GET /api/v1/logs/get` | 1 |

---

## File Map

```
plugin/UE5MCP/
  UE5MCP.uplugin
  Source/UE5MCP/
    UE5MCP.Build.cs
    Public/
      UE5MCPModule.h          # IModuleInterface — intentionally minimal
      UE5MCPSettings.h        # UDeveloperSettings — Port, bEnableOnStartup
    Private/
      UE5MCPModule.cpp
      UE5MCPSettings.cpp
      Subsystem/
        UE5MCPSubsystem.h/cpp # UEditorSubsystem — lifecycle owner, starts HTTP server
      HttpServer/
        UE5MCPHttpServer.h/cpp      # Owns IHttpRouter, calls RegisterAllRoutes
        UE5MCPRouteRegistrar.h      # Documents the RegisterRoutes convention
        UE5MCPResponseHelpers.h     # BuildSuccessResponse / BuildErrorResponse
      Handlers/
        UE5MCPActorHandlers.h/cpp       # list/spawn/delete — Phase 3
        UE5MCPTransformHandlers.h/cpp   # get/set transform — Phase 3
        UE5MCPPropertyHandlers.h/cpp    # get/set property — Phase 3
        UE5MCPConsoleHandlers.h/cpp     # execute console — Phase 3
        UE5MCPPIEHandlers.h/cpp         # start/stop/state PIE — Phase 3
        UE5MCPScreenshotHandlers.h/cpp  # capture screenshot — Phase 3
        UE5MCPLogHandlers.h/cpp         # get log lines — Phase 3
      Logging/
        UE5MCPLogCapture.h/cpp    # FOutputDevice circular buffer, thread-safe

mcp_server/
  pyproject.toml              # hatchling, mcp>=1.0, httpx>=0.27, pydantic>=2
  .python-version             # 3.11
  src/ue5_mcp/
    __init__.py               # version string
    __main__.py               # entry point: parse Config, create_server, run_stdio
    config.py                 # Config dataclass + from_args()
    client.py                 # EditorClient, EditorError, EditorConnectionError
    server.py                 # create_server(): list_tools + call_tool dispatch
    tools/
      actors.py               # list_actors, spawn_actor, delete_actor — COMPLETE
      transforms.py           # get_actor_transform, set_actor_transform
      properties.py           # get_property, set_property
      console.py              # execute_console_command
      pie.py                  # start_pie, stop_pie, get_pie_state
      screenshot.py           # capture_screenshot
      logs.py                 # get_log
    models/
      requests.py             # reserved — models live in tool files
      responses.py            # reserved
  tests/
    conftest.py               # mock_editor (respx), editor_client fixtures
    tools/
      test_actors.py          # 4 tests: success x3 + EditorError propagation
      test_transforms.py
      test_properties.py
      test_console.py
```

---

## ROADMAP Status

- **Phase 1** (Plugin Scaffold): Milestones 1.1–1.4 — scaffold complete, compile unverified
- **Phase 2** (HTTP Server Core): Milestones 2.1–2.3 — scaffold complete, functionality unimplemented
- **Phase 3** (Tier 1 Handlers): All handler .cpp files are stubs — `// TODO: Phase 3`
- **Phase 4** (Python MCP Server): Scaffold + actors.py fully complete; other tool modules are stubs
- **Phase 5** (Integration): Not started
- **Phase 6** (CI/Docs/Release): CI workflows written; doc content is stub headings
- **Phase 7** (Tier 2): Not started

---

## Git Workflow

- Remote: `git@github.com:eashman-design/UE5_MCP.git` (SSH only — never HTTPS)
- Default branch: `main`
- **Use GitHub MCP tools** (`mcp__github__*`) for all GitHub operations: creating PRs, listing issues, pushing files, etc. Do not use `gh` CLI.
- Commit with `git commit` via Bash for local commits, then push with `git push`.

---

## Python Dev Setup

```bash
cd mcp_server
pip install -e ".[dev]"   # installs mcp, httpx, pydantic + pytest, respx, pytest-asyncio
ue5-mcp --help            # verify entry point works
pytest --tb=short         # run test suite
```

---

## Verify the Full Stack

With UE5 Editor open and plugin loaded:

```bash
curl http://localhost:8765/api/v1/actors/list
# Expected: {"ok":true,"data":{"actors":[...]}}
```

Claude Code MCP config (`~/.claude/claude_desktop_config.json`):

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

---

## Adding a New Handler (Pattern)

1. Create `plugin/.../Handlers/UE5MCPXxxHandlers.h` and `.cpp` with `namespace UE5MCPXxxHandlers { void RegisterRoutes(TSharedPtr<IHttpRouter>); }`
2. Call `UE5MCPXxxHandlers::RegisterRoutes(Router)` in `UE5MCPHttpServer::RegisterAllRoutes`
3. Add `#include "Handlers/UE5MCPXxxHandlers.h"` to `UE5MCPHttpServer.cpp`
4. Add corresponding tool module in `mcp_server/src/ue5_mcp/tools/xxx.py` following the `actors.py` pattern
5. Import and add to `all_tool_modules` in `server.py`
