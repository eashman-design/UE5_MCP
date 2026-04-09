# ROADMAP.md — UE5-MCP

> Living document. Claude Code checks off tasks as they are completed and may add or reorder
> tasks as the project evolves. Phases and milestones can be changed — this is not locked.

> **Maintenance rules for Claude Code:**
> - Check off tasks with [x] immediately when complete — don't batch updates
> - If a task is split into smaller pieces mid-session, replace it with the subtasks
> - If new tasks are discovered, add them to the appropriate milestone
> - If scope changes make a task obsolete, strike it out with ~~ ~~ and add a note
> - Never delete tasks — mark them obsolete instead so progress history is preserved
> - Reorder tasks within a milestone if sequencing changes — move completed ones to top

---

## Phase 1 — Plugin Scaffold
_Establish the C++ plugin skeleton that compiles clean for both editor and console targets, with the subsystem lifecycle wired up and the HTTP server listening on port 8765._

### Milestone 1.1 — Repository Layout
- [ ] Create repo root directory structure matching DESIGN.md §3 (plugin/, mcp_server/, docs/, .github/)
- [ ] Add .gitignore covering UE5 build artifacts (Binaries/, Intermediate/, .vs/, __pycache__, *.pyc, dist/, .venv/)
- [ ] Add MIT LICENSE
- [ ] Add stub README.md with project overview, install steps, and Claude Code config block

### Milestone 1.2 — Plugin Skeleton
- [ ] Create `plugin/UE5MCP/UE5MCP.uplugin` per DESIGN.md §4.2 (Editor type, Default loading phase)
- [ ] Create `UE5MCP.Build.cs` with Core/CoreUObject/Engine/Slate/Json/DeveloperSettings in unconditional block; UnrealEd/LevelEditor/HTTPServer/HTTP inside `if (Target.bBuildEditor)` guard
- [ ] Implement `FUE5MCPModule` (StartupModule/ShutdownModule log only — no real init) in `UE5MCPModule.h/.cpp`
- [ ] Add `IMPLEMENT_MODULE` and `DEFINE_LOG_CATEGORY_STATIC(LogUE5MCP, Log, All)` in module .cpp
- [ ] Verify plugin compiles for Editor target (no errors) and that console-target sweep produces no missing-include errors

### Milestone 1.3 — Settings
- [ ] Implement `UUE5MCPSettings : UDeveloperSettings` with `Port` (int32, default 8765) and `bEnableOnStartup` (bool, default true) UPROPERTY fields
- [ ] Confirm settings appear in Editor under Plugins → UE5 MCP and persist to DefaultEngine.ini

### Milestone 1.4 — Editor Subsystem Lifecycle
- [ ] Implement `UUE5MCPSubsystem : UEditorSubsystem` with Initialize/Deinitialize, StartServer/StopServer/IsServerRunning
- [ ] Wire Initialize to read `bEnableOnStartup` and conditionally call StartServer
- [ ] Wire Deinitialize to call StopServer then tear down LogCapture
- [ ] Confirm subsystem constructs and destructs cleanly on editor open/close (check Output Log)

---

## Phase 2 — HTTP Server Core
_The embedded HTTP server is running, route registration is extensible, response helpers are in place, and thread marshaling is enforced. No handlers yet — just the infrastructure every handler will depend on._

### Milestone 2.1 — HTTP Server and Route Registrar
- [ ] Implement `FUE5MCPHttpServer` with Start/Stop/IsRunning and `RegisterAllRoutes` dispatcher
- [ ] Implement `UE5MCPRouteRegistrar.h` — define the `RegisterRoutes(TSharedPtr<IHttpRouter>)` function signature contract all handler groups must satisfy
- [ ] Wire `FUE5MCPHttpServer::Start` to `FHttpServerModule::Get().GetHttpRouter(Port)` and `StartAllListeners()`; Stop to `StopAllListeners()` and Router.Reset()
- [ ] Add startup/shutdown log lines confirming port number
- [ ] Confirm HTTP server starts and `curl http://localhost:8765/` returns a 404 (router alive, no routes yet)

### Milestone 2.2 — Response Helpers
- [ ] Implement `FUE5MCPResponseHelpers` header-only struct with `BuildSuccessResponse(TSharedPtr<FJsonObject>)` and `BuildErrorResponse(FString Message, FString Code)`
- [ ] Both helpers produce `{"ok": true/false, ...}` envelope, always HTTP 200, Content-Type application/json
- [ ] Write a test route (`GET /api/v1/ping`) wired in `RegisterAllRoutes` that returns `BuildSuccessResponse` with `{"pong": true}` — used to verify the full stack before any real handlers land; remove after Phase 3 is complete

### Milestone 2.3 — Log Capture
- [ ] Implement `FUE5MCPLogCapture : FOutputDevice` with `StartCapture` (GLog->AddOutputDevice), `StopCapture` (GLog->RemoveOutputDevice), and circular buffer of 2000 lines
- [ ] `Serialize` method acquires `FCriticalSection Lock` before touching `Buffer` — called from arbitrary threads
- [ ] `GetRecentLines(int32 Count, FString Category)` acquires Lock, returns tail slice optionally filtered by category substring
- [ ] Integrate into subsystem: create LogCapture in Initialize before StartServer, StopCapture and Reset in Deinitialize

---

## Phase 3 — Tier 1 Plugin Handlers (C++)
_All 13 Tier 1 MCP tools have corresponding plugin endpoints fully implemented, thread-safe, using only BuildSuccessResponse/BuildErrorResponse, and manually verified against curl._

### Milestone 3.1 — Actor Handlers
- [ ] Implement `UE5MCPActorHandlers::RegisterRoutes` with three routes:
  - `GET /api/v1/actors/list` — iterate TActorIterator<AActor>, return array of {name, class, id} objects
  - `POST /api/v1/actors/spawn` — parse class_path/name/location/rotation from JSON body, SpawnActor via UEditorActorSubsystem or GEditor->AddActor, return {name, id} or SPAWN_FAILED/CLASS_NOT_FOUND
  - `POST /api/v1/actors/delete` — find actor by name, call GEditor->SelectActor then UEditorActorSubsystem::DeleteActors, return {deleted: name} or ACTOR_NOT_FOUND
- [ ] All three routes follow the AsyncTask(GameThread) pattern — no UObject access on HTTP thread
- [ ] Manual curl tests: list returns known actors, spawn creates a visible actor in level, delete removes it

### Milestone 3.2 — Transform Handlers
- [ ] Implement `UE5MCPTransformHandlers::RegisterRoutes` with two routes:
  - `POST /api/v1/transform/get` — find actor by name, return {location:[x,y,z], rotation:[p,y,r], scale:[x,y,z]} or ACTOR_NOT_FOUND
  - `POST /api/v1/transform/set` — find actor, apply any of location/rotation/scale that are present in body, call MarkPackageDirty, return {name}
- [ ] Vectors serialized as [X, Y, Z] float arrays; rotator as [Pitch, Yaw, Roll]
- [ ] Manual curl test: spawn an actor, get its transform, set location to [100,200,300], get again to confirm

### Milestone 3.3 — Property Handlers (Reflection)
- [ ] Implement `UE5MCPPropertyHandlers::RegisterRoutes` with two routes:
  - `POST /api/v1/property/get` — find actor, FindPropertyByName, ExportText_InContainer, return {actor_name, property_name, value, type}
  - `POST /api/v1/property/set` — find actor, FindPropertyByName, IsSupportedPropertyType check, ImportText_InContainer, return {actor_name, property_name, value}
- [ ] Implement `IsSupportedPropertyType` helper: whitelist FBoolProperty, FIntProperty, FFloatProperty, FStrProperty, FNameProperty, FStructProperty (for FVector/FRotator/FLinearColor by struct name)
- [ ] Unsupported types return UNSUPPORTED_PROPERTY_TYPE with message listing the supported set
- [ ] PROPERTY_NOT_FOUND and IMPORT_TEXT_FAILED errors per error code table in DESIGN.md §4.12
- [ ] Manual test: get/set a bool, float, FVector, and FLinearColor on a placed light actor

### Milestone 3.4 — Console Handler
- [ ] Implement `UE5MCPConsoleHandlers::RegisterRoutes` with one route:
  - `POST /api/v1/console/execute` — extract "command" string, call GEngine->Exec(World, *Command) on game thread, return {command}
- [ ] INVALID_REQUEST_BODY if "command" field missing or empty
- [ ] Manual test: `r.SetRes 1920x1080` executes without crash, check Output Log for effect

### Milestone 3.5 — PIE Handlers
- [ ] Implement `UE5MCPPIEHandlers::RegisterRoutes` with three routes:
  - `POST /api/v1/pie/start` — parse mode (selected_viewport/simulate/new_window), call GEditor->RequestPlaySession with appropriate FRequestPlaySessionParams, return {state:"running"} or PIE_ALREADY_RUNNING
  - `POST /api/v1/pie/stop` — call GEditor->RequestEndPlayMap, return {state:"stopped"} or PIE_NOT_RUNNING
  - `GET /api/v1/pie/state` — check GEditor->PlayWorld != nullptr, return {state:"running"|"stopped"|"paused"}
- [ ] Check `GEditor->IsPlaySessionRunning()` and `GEditor->IsPlaySessionPaused()` for state determination
- [ ] Manual test: start PIE, get state returns "running", stop PIE, get state returns "stopped"

### Milestone 3.6 — Screenshot Handler
- [ ] Implement `UE5MCPScreenshotHandlers::RegisterRoutes` with one route:
  - `POST /api/v1/screenshot/capture` — parse optional "filename", call FScreenshotRequest::RequestScreenshot or UAutomationBlueprintFunctionLibrary::TakeAutomationScreenshot on game thread, return {path} of saved PNG or SCREENSHOT_FAILED
- [ ] Default filename to `ue5mcp_<timestamp>.png` in project's Saved/Screenshots/ directory
- [ ] Manual test: capture returns a valid absolute path, file exists on disk and is a valid PNG

### Milestone 3.7 — Log Handler
- [ ] Implement `UE5MCPLogHandlers::RegisterRoutes(Router, LogCapture)` with one route:
  - `GET /api/v1/logs/get?count=200&category=` — call LogCapture->GetRecentLines, return {lines:[...], count:N}
- [ ] Default count to 200 if not provided; clamp to [1, 2000]
- [ ] Category param is optional; empty string returns all categories
- [ ] Manual test: execute a console command, then get logs filtered by "LogConsoleResponse" to confirm capture is working

---

## Phase 4 — Python MCP Server
_The full Python package is implemented — all 13 tools registered, client wired, Pydantic validation in place, error propagation correct, and the server connects to a live editor._

### Milestone 4.1 — Package Scaffold
- [ ] Create `mcp_server/` directory tree per DESIGN.md §3 (src/ue5_mcp/, tests/, pyproject.toml, .python-version)
- [ ] Write `pyproject.toml` per DESIGN.md §6.1 — hatchling backend, mcp>=1.0.0, httpx>=0.27.0, pydantic>=2.0.0, entry point `ue5-mcp = "ue5_mcp.__main__:main"`
- [ ] Write `.python-version` containing `3.11`
- [ ] Confirm `pip install -e .` succeeds and `ue5-mcp --help` prints usage

### Milestone 4.2 — Config and Entry Point
- [ ] Implement `Config` dataclass per DESIGN.md §6.3 with editor_port, editor_host, request_timeout, log_level fields and `from_args()` classmethod
- [ ] Implement `__main__.py` — parse Config, create server, run stdio loop
- [ ] Implement `__init__.py` with package version string

### Milestone 4.3 — Plugin HTTP Client
- [ ] Implement `EditorClient` per DESIGN.md §6.4 — wraps httpx.AsyncClient, `get()` and `post()` methods, `_unwrap()` that raises `EditorError` on `ok=false` and `EditorConnectionError` on connection failure
- [ ] `EditorConnectionError` message is human-readable for Claude (per DESIGN.md §6.7)
- [ ] `aclose()` for clean shutdown
- [ ] Unit test: `_unwrap` raises EditorError with correct code when ok=false; raises EditorConnectionError on httpx.ConnectError

### Milestone 4.4 — MCP Server Registration
- [ ] Implement `server.py` — `create_server(config)` creates MCP Server instance, `list_tools()` aggregates TOOLS from all modules, `call_tool()` dispatches to correct module handle() by checking TOOL_NAMES sets
- [ ] Raises `ValueError` for unknown tool names
- [ ] Confirm server starts, connects to running editor, and `list_tools` returns all 13 tool definitions

### Milestone 4.5 — Actor Tools
- [ ] Implement `tools/actors.py` per DESIGN.md §6.6 canonical pattern: SpawnActorInput/DeleteActorInput Pydantic models, TOOLS list with 3 Tool definitions, TOOL_NAMES set, handle() function
- [ ] Tool descriptions written for Claude's benefit — describe what the tool does and what it returns
- [ ] Unit tests in `tests/tools/test_actors.py`: success case for each of list/spawn/delete; EditorError propagation; missing required field raises ValidationError

### Milestone 4.6 — Transform Tools
- [ ] Implement `tools/transforms.py`: GetTransformInput/SetTransformInput models (name required; location/rotation/scale Optional[list[float]])
- [ ] TOOLS: `get_actor_transform`, `set_actor_transform`
- [ ] Unit tests: success round-trip, partial set (location only), ACTOR_NOT_FOUND propagation

### Milestone 4.7 — Property Tools
- [ ] Implement `tools/properties.py`: GetPropertyInput/SetPropertyInput models; all values as strings per protocol
- [ ] TOOLS: `get_property`, `set_property`; descriptions explain string format for FVector, FRotator, FLinearColor
- [ ] Unit tests: success for get and set, PROPERTY_NOT_FOUND propagation, UNSUPPORTED_PROPERTY_TYPE propagation

### Milestone 4.8 — Console, PIE, Screenshot, Log Tools
- [ ] Implement `tools/console.py`: ExecuteConsoleInput, `execute_console_command` tool
- [ ] Implement `tools/pie.py`: StartPIEInput (mode field with enum: selected_viewport/simulate/new_window), `start_pie`/`stop_pie`/`get_pie_state` tools
- [ ] Implement `tools/screenshot.py`: CaptureScreenshotInput (optional filename), `capture_screenshot` tool
- [ ] Implement `tools/logs.py`: GetLogInput (optional count int, optional category str), `get_log` tool
- [ ] Unit tests for each: success case + primary error propagation (at minimum one error test per module)

---

## Phase 5 — Integration and End-to-End Validation
_The full stack works together. Claude Code can drive the editor via the MCP tools. Known error paths are exercised and produce correct responses at the Claude level._

### Milestone 5.1 — Full Stack Smoke Test
- [ ] With UE5 Editor open and plugin running, confirm `ue5-mcp` connects via Claude Code MCP config
- [ ] Exercise all 13 tools via Claude Code in a live editor session and confirm correct results
- [ ] Confirm `EditorConnectionError` surfaces cleanly to Claude when editor is closed (plugin not reachable)

### Milestone 5.2 — Error Path Validation
- [ ] Verify ACTOR_NOT_FOUND flows correctly from plugin → Python client → Claude tool result
- [ ] Verify PIE_ALREADY_RUNNING and PIE_NOT_RUNNING produce clear Claude-readable messages
- [ ] Verify UNSUPPORTED_PROPERTY_TYPE returns the supported-types list in the error message
- [ ] Verify INVALID_REQUEST_BODY triggers correctly for malformed JSON bodies

### Milestone 5.3 — Test Suite Completeness
- [ ] All 13 tool handlers have at least one success test and one error propagation test in pytest
- [ ] `pytest --tb=short` passes with zero failures and zero warnings from project code
- [ ] Add `respx` and `pytest-asyncio` to `pyproject.toml` under `[project.optional-dependencies] dev`

---

## Phase 6 — CI, Docs, and v0.1.0 Release
_The project is releasable: CI is green, docs cover installation end-to-end, and the tool name registry is frozen._

### Milestone 6.1 — GitHub Actions
- [ ] Add `.github/workflows/python-tests.yml` — runs `pytest` on Python 3.11 on ubuntu-latest; triggers on push and PR to main
- [ ] Add `.github/workflows/python-lint.yml` — runs `ruff check` and `mypy --strict` on the mcp_server/src tree
- [ ] Both workflows pass on the main branch with zero errors

### Milestone 6.2 — Documentation
- [ ] Write `docs/installation.md` — covers plugin copy, UE5 rebuild prompt, enabling plugin, verifying HTTP server, pip install, Claude Code MCP config JSON, and the curl verification command
- [ ] Write `docs/architecture.md` — system diagram from DESIGN.md §2.1, component responsibility table, threading model explanation, HTTP API contract summary
- [ ] Write `docs/tools-reference.md` — one section per tool: name, description, input schema, example request/response, known error codes
- [ ] Finalize README.md — quick-start, feature list, link to docs/, badge for CI status

### Milestone 6.3 — v0.1.0 Tag
- [ ] Confirm all 13 tool names match DESIGN.md §7 exactly — these are frozen from this point
- [ ] Confirm plugin version in UE5MCP.uplugin is "0.1.0" and Python package version in pyproject.toml is "0.1.0"
- [ ] Tag commit as `v0.1.0` and create GitHub release with install instructions in release notes

---

## Phase 7 — Tier 2: Asset Pipeline
_Five new tools extending the plugin and MCP server for asset import, material creation/assignment, Blueprint class creation, and automation test execution._

### Milestone 7.1 — Plugin: Asset Handlers
- [ ] Add `UE5MCPAssetHandlers` with `POST /api/v1/assets/import` — use `UAutomatedAssetImportData` + `FAssetToolsModule` to import a file from an absolute disk path into a target Content Browser path
- [ ] Add `POST /api/v1/assets/create_material` — `IAssetTools::CreateAsset<UMaterial>`, set base color via `UMaterialExpressionConstant4Vector`, save package
- [ ] Add `POST /api/v1/assets/assign_material` — find actor, get `UStaticMeshComponent`, call `SetMaterial(SlotIndex, MaterialInterface)` with asset loaded via `StaticLoadObject`
- [ ] Add `POST /api/v1/blueprint/create_class` — use `FKismetEditorUtilities::CreateBlueprint` with a resolved parent UClass, save to specified Content Browser path

### Milestone 7.2 — Plugin: Automation Test Handler
- [ ] Add `POST /api/v1/automation/run` — use `FAutomationTestFramework::Get().RunSmokeTests` or `IAutomationControllerModule` to run a named test; poll or wait for completion; return {passed, failed, log:[]}
  - _Note: This is the most complex Tier 2 task. FAutomationControllerModule requires careful setup — read Engine/Source/Developer/AutomationController/ before implementing._

### Milestone 7.3 — Python: Tier 2 Tools
- [ ] Implement `tools/assets.py` — `import_asset`, `create_material`, `assign_material` tools with Pydantic models
- [ ] Implement `tools/blueprint.py` — `create_blueprint_class` tool
- [ ] Implement `tools/automation.py` — `run_automation_tests` tool
- [ ] Register all Tier 2 modules in `server.py`
- [ ] Unit tests for each Tier 2 tool (success + primary error case)

### Milestone 7.4 — Tier 2 Docs and Release
- [ ] Update `docs/tools-reference.md` with all 5 new tools
- [ ] Tag `v0.2.0`
