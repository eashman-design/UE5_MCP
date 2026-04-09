# UE5-MCP Design Document

> **Audience**: Claude Code and any contributor implementing this project.  
> **Status**: Authoritative. All implementation decisions must be consistent with this document. When in doubt, return here before writing code.

---

## 1. Project Overview

UE5-MCP is an open-source Model Context Protocol (MCP) server that gives Claude Code (and any MCP-compatible AI client) direct programmatic control over a running Unreal Engine 5 Editor instance.

The tool targets two usage modes:

- **Assisted**: Developer has the UE5 Editor and Claude Code open simultaneously. Claude acts as a co-pilot — spawning actors, tweaking properties, running PIE, capturing screenshots, reading logs.
- **Headless**: Claude Code drives the editor autonomously via terminal with no human watching the editor in real time.

Both modes use the exact same code path. The distinction is purely in how the user invokes Claude Code, not in anything this project controls.

---

## 2. Architecture

### 2.1 System Diagram

```
+---------------------------------------------+
|  Claude Code (MCP Client)                   |
|  Reads tool definitions, calls tools,       |
|  receives structured results                |
+------------------+---------------------------+
                   |  MCP protocol (JSON-RPC 2.0 over stdio)
                   v
+---------------------------------------------+
|  Python MCP Server  (ue5_mcp package)       |
|  Translates MCP tool calls -> HTTP requests |
|  Returns structured results to Claude       |
|  Process: python -m ue5_mcp                 |
+------------------+---------------------------+
                   |  HTTP REST  localhost:8765
                   v
+---------------------------------------------+
|  UE5 Editor Plugin  (UE5MCP)                |
|  C++ plugin running inside the editor       |
|  Embedded HTTP server via FHttpServerModule |
|  Dispatches all UObject work to game thread |
+------------------+---------------------------+
                   |  Internal UE5 APIs
                   v
+---------------------------------------------+
|  Unreal Engine 5.5 Editor Process           |
+---------------------------------------------+
```

### 2.2 Component Responsibilities

| Component | Owns | Does NOT own |
|---|---|---|
| UE5 Plugin | HTTP server, thread marshaling, all UObject operations, log capture, screenshot capture, PIE control | MCP protocol, tool schema, retry logic |
| Python MCP Server | MCP protocol, tool definitions, input validation (Pydantic), HTTP client to plugin | Any UE5 API knowledge, business logic |

The plugin is intentionally dumb about MCP. The MCP server is intentionally dumb about UE5 internals. The HTTP API between them is the contract.

---

## 3. Repository Structure

```
ue5-mcp/
|
+-- plugin/
|   +-- UE5MCP/                          <- Copy this entire folder to MyProject/Plugins/
|       +-- UE5MCP.uplugin
|       +-- Resources/
|       |   +-- Icon128.png
|       +-- Source/
|           +-- UE5MCP/
|               +-- UE5MCP.Build.cs
|               +-- Public/
|               |   +-- UE5MCPModule.h
|               |   +-- UE5MCPSettings.h
|               +-- Private/
|                   +-- UE5MCPModule.cpp
|                   +-- UE5MCPSettings.cpp
|                   +-- Subsystem/
|                   |   +-- UE5MCPSubsystem.h
|                   |   +-- UE5MCPSubsystem.cpp
|                   +-- HttpServer/
|                   |   +-- UE5MCPHttpServer.h
|                   |   +-- UE5MCPHttpServer.cpp
|                   |   +-- UE5MCPRouteRegistrar.h
|                   |   +-- UE5MCPResponseHelpers.h
|                   +-- Handlers/
|                   |   +-- UE5MCPActorHandlers.h
|                   |   +-- UE5MCPActorHandlers.cpp
|                   |   +-- UE5MCPTransformHandlers.h
|                   |   +-- UE5MCPTransformHandlers.cpp
|                   |   +-- UE5MCPPropertyHandlers.h
|                   |   +-- UE5MCPPropertyHandlers.cpp
|                   |   +-- UE5MCPConsoleHandlers.h
|                   |   +-- UE5MCPConsoleHandlers.cpp
|                   |   +-- UE5MCPPIEHandlers.h
|                   |   +-- UE5MCPPIEHandlers.cpp
|                   |   +-- UE5MCPScreenshotHandlers.h
|                   |   +-- UE5MCPScreenshotHandlers.cpp
|                   +-- Logging/
|                       +-- UE5MCPLogCapture.h
|                       +-- UE5MCPLogCapture.cpp
|
+-- mcp_server/
|   +-- src/
|   |   +-- ue5_mcp/
|   |       +-- __init__.py
|   |       +-- __main__.py
|   |       +-- server.py
|   |       +-- config.py
|   |       +-- client.py
|   |       +-- tools/
|   |       |   +-- __init__.py
|   |       |   +-- actors.py
|   |       |   +-- transforms.py
|   |       |   +-- properties.py
|   |       |   +-- console.py
|   |       |   +-- pie.py
|   |       |   +-- screenshot.py
|   |       |   +-- logs.py
|   |       +-- models/
|   |           +-- __init__.py
|   |           +-- requests.py
|   |           +-- responses.py
|   +-- tests/
|   |   +-- conftest.py
|   |   +-- tools/
|   |       +-- test_actors.py
|   |       +-- test_transforms.py
|   |       +-- test_properties.py
|   |       +-- test_console.py
|   +-- pyproject.toml
|   +-- .python-version              <- Contains: 3.11
|
+-- docs/
|   +-- installation.md
|   +-- architecture.md
|   +-- tools-reference.md
|
+-- .github/
|   +-- workflows/
|       +-- python-tests.yml
|       +-- python-lint.yml
|
+-- .gitignore
+-- LICENSE                          <- MIT
+-- README.md
+-- DESIGN.md                        <- This file
```

---

## 4. Plugin Architecture (C++)

### 4.1 Target Configuration

- **Engine version**: Unreal Engine 5.5
- **Plugin type**: Project plugin (installed to `MyProject/Plugins/UE5MCP/`)
- **Module type**: Editor (`"Type": "Editor"` in `.uplugin`)
- **Module loading phase**: `"Default"` — the subsystem handles all real initialization timing
- **Target platforms**: Editor-only. The plugin must compile clean for Win64 console targets (where `bBuildEditor` is false) because project compilation sweeps all plugins. All editor-only code must be guarded.

### 4.2 .uplugin File

```json
{
  "FileVersion": 3,
  "Version": 1,
  "VersionName": "0.1.0",
  "FriendlyName": "UE5 MCP",
  "Description": "Model Context Protocol server for Unreal Engine 5 Editor control via AI.",
  "Category": "Editor",
  "CreatedBy": "UE5-MCP Contributors",
  "CreatedByURL": "https://github.com/your-org/ue5-mcp",
  "DocsURL": "",
  "MarketplaceURL": "",
  "SupportURL": "",
  "CanContainContent": false,
  "IsBetaVersion": true,
  "IsExperimentalVersion": false,
  "Installed": false,
  "Modules": [
    {
      "Name": "UE5MCP",
      "Type": "Editor",
      "LoadingPhase": "Default"
    }
  ]
}
```

### 4.3 Build.cs

All editor-only module dependencies must be inside the `bBuildEditor` guard. Failing to do this causes compile failures when the project is built for console targets.

```csharp
using UnrealBuildTool;

public class UE5MCP : ModuleRules
{
    public UE5MCP(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "CoreUObject",
            "Engine",
            "Slate",
            "SlateCore",
            "Json",
            "JsonUtilities",
            "DeveloperSettings",
        });

        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.AddRange(new string[]
            {
                "UnrealEd",
                "LevelEditor",
                "HTTPServer",
                "HTTP",
            });
        }
    }
}
```

### 4.4 Module Class

`UE5MCPModule` is intentionally minimal. It implements `IModuleInterface` and does nothing except log that it loaded. All real initialization lives in the subsystem.

```cpp
// UE5MCPModule.h
#pragma once
#include "Modules/ModuleManager.h"

class FUE5MCPModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
```

```cpp
// UE5MCPModule.cpp
#include "UE5MCPModule.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FUE5MCPModule, UE5MCP)
DEFINE_LOG_CATEGORY_STATIC(LogUE5MCP, Log, All);

void FUE5MCPModule::StartupModule()
{
    UE_LOG(LogUE5MCP, Log, TEXT("UE5MCP module loaded."));
}

void FUE5MCPModule::ShutdownModule()
{
    UE_LOG(LogUE5MCP, Log, TEXT("UE5MCP module unloaded."));
}
```

### 4.5 Settings Class

`UUE5MCPSettings` surfaces config in the editor's Project Settings panel under "Plugins > UE5 MCP". Values persist to `DefaultEngine.ini` automatically via the `UDeveloperSettings` base class.

```cpp
// UE5MCPSettings.h
#pragma once
#include "Engine/DeveloperSettings.h"
#include "UE5MCPSettings.generated.h"

UCLASS(Config=Engine, DefaultConfig, meta=(DisplayName="UE5 MCP"))
class UUE5MCPSettings : public UDeveloperSettings
{
    GENERATED_BODY()

public:
    UUE5MCPSettings();

    virtual FName GetCategoryName() const override { return TEXT("Plugins"); }
    virtual FName GetSectionName() const override { return TEXT("UE5 MCP"); }

    UPROPERTY(Config, EditAnywhere, Category="Server", meta=(
        DisplayName="Port",
        ToolTip="Port the embedded HTTP server listens on. Default: 8765. Restart editor after changing."))
    int32 Port = 8765;

    UPROPERTY(Config, EditAnywhere, Category="Server", meta=(
        DisplayName="Enable on Startup",
        ToolTip="Automatically start the MCP HTTP server when the editor opens."))
    bool bEnableOnStartup = true;

    static const UUE5MCPSettings* Get() { return GetDefault<UUE5MCPSettings>(); }
};
```

### 4.6 Editor Subsystem

`UUE5MCPSubsystem` is the core lifecycle owner. The engine constructs it automatically during editor startup and tears it down on shutdown. It starts and stops the HTTP server and owns the log capture device.

```cpp
// UE5MCPSubsystem.h
#pragma once
#include "EditorSubsystem.h"
#include "UE5MCPSubsystem.generated.h"

class FUE5MCPHttpServer;
class FUE5MCPLogCapture;

UCLASS()
class UUE5MCPSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable, Category="UE5MCP")
    void StartServer();

    UFUNCTION(BlueprintCallable, Category="UE5MCP")
    void StopServer();

    UFUNCTION(BlueprintCallable, Category="UE5MCP")
    bool IsServerRunning() const;

private:
    TSharedPtr<FUE5MCPHttpServer> HttpServer;
    TSharedPtr<FUE5MCPLogCapture> LogCapture;
};
```

```cpp
// UE5MCPSubsystem.cpp
#include "Subsystem/UE5MCPSubsystem.h"
#include "HttpServer/UE5MCPHttpServer.h"
#include "Logging/UE5MCPLogCapture.h"
#include "UE5MCPSettings.h"

DEFINE_LOG_CATEGORY_STATIC(LogUE5MCPSubsystem, Log, All);

void UUE5MCPSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    LogCapture = MakeShared<FUE5MCPLogCapture>();
    LogCapture->StartCapture();

    if (UUE5MCPSettings::Get()->bEnableOnStartup)
    {
        StartServer();
    }
}

void UUE5MCPSubsystem::Deinitialize()
{
    StopServer();

    if (LogCapture.IsValid())
    {
        LogCapture->StopCapture();
        LogCapture.Reset();
    }

    Super::Deinitialize();
}

void UUE5MCPSubsystem::StartServer()
{
    if (HttpServer.IsValid() && HttpServer->IsRunning())
    {
        UE_LOG(LogUE5MCPSubsystem, Warning, TEXT("Server already running."));
        return;
    }
    const int32 Port = UUE5MCPSettings::Get()->Port;
    HttpServer = MakeShared<FUE5MCPHttpServer>(LogCapture, Port);
    HttpServer->Start();
}

void UUE5MCPSubsystem::StopServer()
{
    if (HttpServer.IsValid())
    {
        HttpServer->Stop();
        HttpServer.Reset();
    }
}

bool UUE5MCPSubsystem::IsServerRunning() const
{
    return HttpServer.IsValid() && HttpServer->IsRunning();
}
```

### 4.7 HTTP Server and Route Registration

`FUE5MCPHttpServer` owns the `IHttpRouter`. Adding a new handler group means one new file and one new call in `RegisterAllRoutes` — the core server class never changes for new functionality.

```cpp
// UE5MCPHttpServer.h
#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

class FUE5MCPLogCapture;

class FUE5MCPHttpServer
{
public:
    explicit FUE5MCPHttpServer(TSharedPtr<FUE5MCPLogCapture> InLogCapture, int32 InPort);
    ~FUE5MCPHttpServer();

    void Start();
    void Stop();
    bool IsRunning() const { return bRunning; }

private:
    void RegisterAllRoutes();

    TSharedPtr<IHttpRouter> Router;
    TSharedPtr<FUE5MCPLogCapture> LogCapture;
    int32 Port;
    bool bRunning = false;
};
```

```cpp
// UE5MCPHttpServer.cpp
#include "HttpServer/UE5MCPHttpServer.h"
#include "HttpServerModule.h"
#include "IHttpRouter.h"
#include "Logging/UE5MCPLogCapture.h"
#include "Handlers/UE5MCPActorHandlers.h"
#include "Handlers/UE5MCPTransformHandlers.h"
#include "Handlers/UE5MCPPropertyHandlers.h"
#include "Handlers/UE5MCPConsoleHandlers.h"
#include "Handlers/UE5MCPPIEHandlers.h"
#include "Handlers/UE5MCPScreenshotHandlers.h"
#include "Handlers/UE5MCPLogHandlers.h"

DEFINE_LOG_CATEGORY_STATIC(LogUE5MCPServer, Log, All);

FUE5MCPHttpServer::FUE5MCPHttpServer(TSharedPtr<FUE5MCPLogCapture> InLogCapture, int32 InPort)
    : LogCapture(InLogCapture), Port(InPort)
{
}

FUE5MCPHttpServer::~FUE5MCPHttpServer()
{
    Stop();
}

void FUE5MCPHttpServer::Start()
{
    FHttpServerModule& HttpServerModule = FHttpServerModule::Get();
    Router = HttpServerModule.GetHttpRouter(Port);

    if (!Router.IsValid())
    {
        UE_LOG(LogUE5MCPServer, Error, TEXT("Failed to get HTTP router on port %d"), Port);
        return;
    }

    RegisterAllRoutes();
    HttpServerModule.StartAllListeners();
    bRunning = true;
    UE_LOG(LogUE5MCPServer, Log, TEXT("UE5MCP HTTP server started on port %d"), Port);
}

void FUE5MCPHttpServer::Stop()
{
    if (!bRunning) return;
    FHttpServerModule::Get().StopAllListeners();
    Router.Reset();
    bRunning = false;
    UE_LOG(LogUE5MCPServer, Log, TEXT("UE5MCP HTTP server stopped."));
}

void FUE5MCPHttpServer::RegisterAllRoutes()
{
    UE5MCPActorHandlers::RegisterRoutes(Router);
    UE5MCPTransformHandlers::RegisterRoutes(Router);
    UE5MCPPropertyHandlers::RegisterRoutes(Router);
    UE5MCPConsoleHandlers::RegisterRoutes(Router);
    UE5MCPPIEHandlers::RegisterRoutes(Router);
    UE5MCPScreenshotHandlers::RegisterRoutes(Router);
    UE5MCPLogHandlers::RegisterRoutes(Router, LogCapture);
}
```

### 4.8 THE CRITICAL THREADING PATTERN

This is the single most important implementation rule. Every handler must follow it without exception.

`FHttpServerModule` delivers requests on a background thread pool. The `OnComplete` callback may be invoked from any thread at any time after the handler returns `true`. All UObject operations — anything touching `AActor`, `UWorld`, `GEditor`, `FProperty`, PIE state — must run on the game thread.

**CORRECT pattern — dispatch to game thread, call OnComplete from there:**

```cpp
Router->BindRoute(
    FHttpPath(TEXT("/api/v1/actors/list")),
    EHttpServerRequestVerbs::VERB_GET,
    [](const FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
    {
        // We are on the HTTP thread. Do NOT touch any UObject here.
        // Capture OnComplete by value — it is safe to copy and invoke from any thread.

        AsyncTask(ENamedThreads::GameThread, [OnComplete]()
        {
            // We are now on the game thread. All UE5 APIs are safe here.
            UWorld* World = GEditor->GetEditorWorldContext().World();
            if (!World)
            {
                OnComplete(FUE5MCPResponseHelpers::BuildErrorResponse(
                    TEXT("No editor world available"), TEXT("NO_WORLD")));
                return;
            }

            TSharedPtr<FJsonObject> DataObj = MakeShared<FJsonObject>();
            TArray<TSharedPtr<FJsonValue>> ActorList;

            for (TActorIterator<AActor> It(World); It; ++It)
            {
                TSharedPtr<FJsonObject> ActorObj = MakeShared<FJsonObject>();
                ActorObj->SetStringField(TEXT("name"), It->GetName());
                ActorObj->SetStringField(TEXT("class"), It->GetClass()->GetName());
                ActorList.Add(MakeShared<FJsonValueObject>(ActorObj));
            }

            DataObj->SetArrayField(TEXT("actors"), ActorList);
            OnComplete(FUE5MCPResponseHelpers::BuildSuccessResponse(DataObj));
        });

        return true; // Request accepted. OnComplete will be called asynchronously.
    }
);
```

**WRONG — do not access UObjects on the HTTP thread:**

```cpp
// CRASH: Accessing GEditor from the HTTP thread pool
Router->BindRoute(/* ... */,
    [](const FHttpServerRequest& Request, const FHttpResultCallback& OnComplete)
    {
        UWorld* World = GEditor->GetEditorWorldContext().World(); // WRONG
        OnComplete(/* ... */);
        return true;
    }
);
```

Handler return value: return `true` to signal your handler accepted the request and will call `OnComplete`. Return `false` only to pass the request to the next matching route — almost never correct for our handlers.

### 4.9 Response Helpers

Every response from the plugin uses one of exactly two shapes. Define these helpers once and use them everywhere. Never construct raw JSON response objects in handler code.

```cpp
// UE5MCPResponseHelpers.h
#pragma once
#include "CoreMinimal.h"
#include "HttpServerResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

struct FUE5MCPResponseHelpers
{
    // { "ok": true, "data": { ... } }
    static TUniquePtr<FHttpServerResponse> BuildSuccessResponse(
        TSharedPtr<FJsonObject> Data)
    {
        TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
        Root->SetBoolField(TEXT("ok"), true);
        Root->SetObjectField(TEXT("data"), Data);
        return JsonObjectToResponse(Root);
    }

    // { "ok": false, "error": "Human readable message", "code": "MACHINE_CODE" }
    static TUniquePtr<FHttpServerResponse> BuildErrorResponse(
        const FString& Message,
        const FString& Code)
    {
        TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
        Root->SetBoolField(TEXT("ok"), false);
        Root->SetStringField(TEXT("error"), Message);
        Root->SetStringField(TEXT("code"), Code);
        return JsonObjectToResponse(Root);
    }

private:
    static TUniquePtr<FHttpServerResponse> JsonObjectToResponse(
        TSharedPtr<FJsonObject> JsonObj)
    {
        FString Body;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Body);
        FJsonSerializer::Serialize(JsonObj.ToSharedRef(), Writer);
        auto Response = FHttpServerResponse::Create(Body, TEXT("application/json"));
        Response->Code = EHttpServerResponseCodes::Ok;
        return Response;
    }
};
```

### 4.10 Log Capture

`FUE5MCPLogCapture` subclasses `FOutputDevice` and registers with `GLog`. It maintains a thread-safe circular buffer of recent log lines. This is the only correct approach for capturing UE5 log output — do not poll log files from disk. On Windows, log files are locked while the editor is running.

```cpp
// UE5MCPLogCapture.h
#pragma once
#include "CoreMinimal.h"
#include "Misc/OutputDevice.h"
#include "HAL/CriticalSection.h"

class FUE5MCPLogCapture : public FOutputDevice
{
public:
    static constexpr int32 MaxLines = 2000;

    FUE5MCPLogCapture() = default;
    virtual ~FUE5MCPLogCapture();

    void StartCapture();
    void StopCapture();

    // Thread-safe. Returns up to Count most recent lines, optionally filtered by category name.
    TArray<FString> GetRecentLines(int32 Count = 200, const FString& Category = TEXT("")) const;

protected:
    virtual void Serialize(const TCHAR* V, ELogVerbosity::Type Verbosity,
                           const FName& Category) override;
    virtual bool CanBeUsedOnAnyThread() const override { return true; }

private:
    mutable FCriticalSection Lock;
    TArray<FString> Buffer;
    bool bCapturing = false;
};
```

```cpp
// UE5MCPLogCapture.cpp
#include "Logging/UE5MCPLogCapture.h"
#include "Misc/OutputDeviceRedirector.h"

FUE5MCPLogCapture::~FUE5MCPLogCapture()
{
    StopCapture();
}

void FUE5MCPLogCapture::StartCapture()
{
    if (!bCapturing)
    {
        GLog->AddOutputDevice(this);
        bCapturing = true;
    }
}

void FUE5MCPLogCapture::StopCapture()
{
    if (bCapturing && GLog)
    {
        GLog->RemoveOutputDevice(this);
        bCapturing = false;
    }
}

void FUE5MCPLogCapture::Serialize(const TCHAR* V, ELogVerbosity::Type Verbosity,
                                   const FName& Category)
{
    FScopeLock ScopeLock(&Lock);

    FString Line = FString::Printf(TEXT("[%s] %s: %s"),
        *FDateTime::Now().ToString(TEXT("%H:%M:%S")),
        *Category.ToString(),
        V);

    if (Buffer.Num() >= MaxLines)
    {
        Buffer.RemoveAt(0, 1, false);
    }
    Buffer.Add(MoveTemp(Line));
}

TArray<FString> FUE5MCPLogCapture::GetRecentLines(int32 Count, const FString& Category) const
{
    FScopeLock ScopeLock(&Lock);
    TArray<FString> Result;
    const int32 Start = FMath::Max(0, Buffer.Num() - Count);
    for (int32 i = Start; i < Buffer.Num(); ++i)
    {
        if (Category.IsEmpty() || Buffer[i].Contains(Category))
        {
            Result.Add(Buffer[i]);
        }
    }
    return Result;
}
```

### 4.11 Generic Property Handler (Reflection System)

The `get_property` and `set_property` tools use `FProperty::ImportText_InContainer` and `FProperty::ExportText_InContainer` for type-agnostic property access.

**Supported property types in Tier 1**: `bool`, `int32`, `float`, `FString`, `FName`, `FVector`, `FRotator`, `FLinearColor`.

Any property type outside this set must return error code `UNSUPPORTED_PROPERTY_TYPE` with a clear message naming the unsupported type and listing supported types. Do not attempt partial serialization. Do not silently ignore unsupported types.

```cpp
// Core pattern for set_property — runs inside the GameThread AsyncTask block
AActor* TargetActor = FindActorByName(World, ActorName); // your helper
if (!TargetActor)
{
    OnComplete(FUE5MCPResponseHelpers::BuildErrorResponse(
        FString::Printf(TEXT("Actor '%s' not found."), *ActorName),
        TEXT("ACTOR_NOT_FOUND")));
    return;
}

FProperty* Prop = TargetActor->GetClass()->FindPropertyByName(FName(*PropertyName));
if (!Prop)
{
    OnComplete(FUE5MCPResponseHelpers::BuildErrorResponse(
        FString::Printf(TEXT("Property '%s' not found on class '%s'."),
            *PropertyName, *TargetActor->GetClass()->GetName()),
        TEXT("PROPERTY_NOT_FOUND")));
    return;
}

if (!IsSupportedPropertyType(Prop)) // your helper checking the type whitelist
{
    OnComplete(FUE5MCPResponseHelpers::BuildErrorResponse(
        FString::Printf(TEXT("Property type '%s' is not supported. Supported: bool, int32, float, FString, FName, FVector, FRotator, FLinearColor."),
            *Prop->GetCPPType()),
        TEXT("UNSUPPORTED_PROPERTY_TYPE")));
    return;
}

void* Container = TargetActor;
const TCHAR* ImportResult = Prop->ImportText_InContainer(*NewValue, Container, nullptr, 0);
if (!ImportResult)
{
    OnComplete(FUE5MCPResponseHelpers::BuildErrorResponse(
        FString::Printf(TEXT("Could not parse value '%s' for property type '%s'."),
            *NewValue, *Prop->GetCPPType()),
        TEXT("IMPORT_TEXT_FAILED")));
    return;
}
```

### 4.12 Error Code Reference

All plugin error responses use these machine-readable codes. The Python MCP server surfaces them to Claude verbatim. Never invent new codes in handler code without adding them here.

| Code | Meaning |
|---|---|
| `NO_WORLD` | Editor world context is not available |
| `ACTOR_NOT_FOUND` | Named actor does not exist in the current world |
| `CLASS_NOT_FOUND` | Requested UClass could not be resolved |
| `PROPERTY_NOT_FOUND` | Named property does not exist on the actor's class |
| `UNSUPPORTED_PROPERTY_TYPE` | Property type is outside the supported Tier 1 set |
| `IMPORT_TEXT_FAILED` | Value string could not be parsed for the given property type |
| `PIE_ALREADY_RUNNING` | Start PIE requested but PIE is already active |
| `PIE_NOT_RUNNING` | Stop PIE requested but PIE is not active |
| `SCREENSHOT_FAILED` | Viewport screenshot capture failed |
| `INVALID_REQUEST_BODY` | Request JSON was malformed or missing required fields |
| `SPAWN_FAILED` | SpawnActor returned null |
| `INTERNAL_ERROR` | Unexpected failure — check the editor output log |

---

## 5. HTTP API Contract

### 5.1 Base URL and Versioning

All endpoints: `http://localhost:{port}/api/v1/`  
Default port: `8765`

The `/api/v1/` prefix is present from day one. A future breaking change introduces `/api/v2/` alongside `/api/v1/` for a deprecation period. Never remove a version prefix without a migration window.

### 5.2 Request Format

- POST requests: `Content-Type: application/json`, body is a JSON object
- GET requests: no body, query string parameters only

### 5.3 Response Envelope

Every response — success or error — uses this top-level envelope:

```json
// Success
{ "ok": true, "data": { ... } }

// Error
{ "ok": false, "error": "Human-readable description", "code": "MACHINE_READABLE_CODE" }
```

HTTP status is always `200 OK` regardless of application-level success or failure. The `ok` field is the authoritative success indicator. The Python client never branches on HTTP status codes from the plugin.

### 5.4 Tier 1 Endpoints

**Actors**

```
GET  /api/v1/actors/list
  Response data: { "actors": [ { "name": str, "class": str, "id": str } ] }

POST /api/v1/actors/spawn
  Body:          { "class_path": str, "name": str?, "location": [x,y,z]?, "rotation": [p,y,r]? }
  Response data: { "name": str, "id": str }

POST /api/v1/actors/delete
  Body:          { "name": str }
  Response data: { "deleted": str }
```

**Transforms**

```
POST /api/v1/transform/get
  Body:          { "name": str }
  Response data: { "location": [x,y,z], "rotation": [p,y,r], "scale": [x,y,z] }

POST /api/v1/transform/set
  Body:          { "name": str, "location": [x,y,z]?, "rotation": [p,y,r]?, "scale": [x,y,z]? }
  Response data: { "name": str }
```

**Properties (Reflection)**

```
POST /api/v1/property/get
  Body:          { "actor_name": str, "property_name": str }
  Response data: { "actor_name": str, "property_name": str, "value": str, "type": str }

POST /api/v1/property/set
  Body:          { "actor_name": str, "property_name": str, "value": str }
  Response data: { "actor_name": str, "property_name": str, "value": str }
```

Property values are always strings. The plugin uses ImportText/ExportText for serialization. Accepted string formats:
- bool: `"true"` or `"false"`
- int32/float: numeric string e.g. `"42"`, `"3.14"`
- FVector: `"X=100.0 Y=0.0 Z=50.0"`
- FRotator: `"P=0.0 Y=90.0 R=0.0"`
- FLinearColor: `"(R=1.0,G=0.5,B=0.0,A=1.0)"`

**Console**

```
POST /api/v1/console/execute
  Body:          { "command": str }
  Response data: { "command": str }
```

**PIE (Play In Editor)**

```
POST /api/v1/pie/start
  Body:          { "mode": "selected_viewport" | "simulate" | "new_window" }  (default: selected_viewport)
  Response data: { "state": "running" }

POST /api/v1/pie/stop
  Response data: { "state": "stopped" }

GET  /api/v1/pie/state
  Response data: { "state": "running" | "stopped" | "paused" }
```

**Screenshot**

```
POST /api/v1/screenshot/capture
  Body:          { "filename": str? }
  Response data: { "path": str }   <- absolute path to the saved PNG
```

**Logs**

```
GET  /api/v1/logs/get?count=200&category=LogBlueprintUserMessages
  Response data: { "lines": [ str ], "count": int }
```

---

## 6. Python MCP Server Architecture

### 6.1 Package Metadata (pyproject.toml)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ue5-mcp"
version = "0.1.0"
description = "MCP server giving AI models direct control over Unreal Engine 5 Editor"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.scripts]
ue5-mcp = "ue5_mcp.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/ue5_mcp"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.mypy]
python_version = "3.11"
strict = true
```

### 6.2 Entry Point

```python
# __main__.py
import asyncio
from ue5_mcp.server import create_server
from ue5_mcp.config import Config

def main() -> None:
    config = Config.from_args()
    server = create_server(config)
    asyncio.run(server.run_stdio())

if __name__ == "__main__":
    main()
```

### 6.3 Config

```python
# config.py
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
```

### 6.4 Plugin HTTP Client

A single `EditorClient` instance is shared across all tool calls. It wraps `httpx.AsyncClient` and unwraps the response envelope. It raises typed exceptions that the MCP server layer handles.

```python
# client.py
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
```

### 6.5 Server and Tool Registration

```python
# server.py
from mcp import Server
from mcp.types import Tool, TextContent
from ue5_mcp.config import Config
from ue5_mcp.client import EditorClient
import ue5_mcp.tools.actors as actors_tools
import ue5_mcp.tools.transforms as transform_tools
import ue5_mcp.tools.properties as property_tools
import ue5_mcp.tools.console as console_tools
import ue5_mcp.tools.pie as pie_tools
import ue5_mcp.tools.screenshot as screenshot_tools
import ue5_mcp.tools.logs as logs_tools

def create_server(config: Config) -> Server:
    server = Server("ue5-mcp")
    client = EditorClient(config.editor_base_url, config.request_timeout)

    all_tool_modules = [
        actors_tools,
        transform_tools,
        property_tools,
        console_tools,
        pie_tools,
        screenshot_tools,
        logs_tools,
    ]

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        for module in all_tool_modules:
            tools.extend(module.TOOLS)
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        for module in all_tool_modules:
            if name in module.TOOL_NAMES:
                return await module.handle(name, client, arguments)
        raise ValueError(f"Unknown tool: {name}")

    return server
```

### 6.6 Tool Module Pattern

Every tool module follows this exact pattern. The `actors.py` module below is the canonical example. All other tool modules are structured identically.

```python
# tools/actors.py
import json
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from typing import Optional
from ue5_mcp.client import EditorClient


# Input Models

class SpawnActorInput(BaseModel):
    class_path: str = Field(
        description="UE5 class path, e.g. '/Script/Engine.StaticMeshActor'")
    name: Optional[str] = Field(
        default=None,
        description="Optional actor name. Auto-generated by engine if omitted.")
    location: Optional[list[float]] = Field(
        default=None,
        description="[X, Y, Z] in world space, in centimeters.")
    rotation: Optional[list[float]] = Field(
        default=None,
        description="[Pitch, Yaw, Roll] in degrees.")

class DeleteActorInput(BaseModel):
    name: str = Field(description="Exact name of the actor to delete.")


# Tool Definitions

TOOLS: list[Tool] = [
    Tool(
        name="list_actors",
        description=(
            "List all actors in the currently open UE5 level. "
            "Returns name, class, and engine ID for each actor."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="spawn_actor",
        description=(
            "Spawn a new actor in the current level. "
            "Returns the actual name the engine assigned, which may differ from the requested name."
        ),
        inputSchema=SpawnActorInput.model_json_schema(),
    ),
    Tool(
        name="delete_actor",
        description=(
            "Delete an actor from the current level by name. "
            "This action cannot be undone via this tool."
        ),
        inputSchema=DeleteActorInput.model_json_schema(),
    ),
]

TOOL_NAMES = {t.name for t in TOOLS}


# Handler

async def handle(name: str, client: EditorClient, arguments: dict) -> list[TextContent]:
    if name == "list_actors":
        data = await client.get("/actors/list")
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    if name == "spawn_actor":
        inp = SpawnActorInput.model_validate(arguments)
        body: dict = {"class_path": inp.class_path}
        if inp.name:
            body["name"] = inp.name
        if inp.location:
            body["location"] = inp.location
        if inp.rotation:
            body["rotation"] = inp.rotation
        data = await client.post("/actors/spawn", body)
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    if name == "delete_actor":
        inp = DeleteActorInput.model_validate(arguments)
        data = await client.post("/actors/delete", {"name": inp.name})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    raise ValueError(f"Unknown actor tool: {name}")
```

### 6.7 Error Handling Strategy

Tool handlers let `EditorConnectionError` and `EditorError` propagate to the MCP server layer, which wraps them into proper MCP error responses. Do not swallow exceptions in tool handlers. Do not use bare `except Exception` in tool code. The error messages in both exception types are written to be human-readable for Claude — treat them as user-facing strings.

---

## 7. Tool Name Registry

These names are the public API. They must not be changed after v0.1.0 is tagged without a major version bump and a migration guide.

| MCP Tool Name | Plugin Endpoint | Tier |
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

## 8. Development Tiers

### Tier 1 — Foundation (v0.1.0)

Plugin skeleton, UEditorSubsystem lifecycle, embedded HTTP server, log capture, and all 13 tools in the registry above. The Python MCP server ships alongside Tier 1. This is the first release.

### Tier 2 — Asset Pipeline

- `import_asset` — import a file from disk into the Content Browser
- `create_material` — create a basic material asset
- `assign_material` — assign a material to a static mesh component
- `create_blueprint_class` — create a Blueprint class from a native or Blueprint parent
- `run_automation_tests` — execute a named automation test and return pass/fail and output

### Tier 3 — Advanced

- Blueprint graph node manipulation (add/remove/connect nodes)
- Animation sequence creation and keyframe editing
- Landscape sculpting and paint tools
- Level streaming control

Tier 2 and Tier 3 tools are not stubbed or partially implemented in earlier tiers. A tool either exists and works completely, or it does not exist. The codebase does not contain placeholder implementations.

---

## 9. Absolute Invariants

These rules are non-negotiable. Code that violates them is incorrect regardless of whether it appears to work in testing.

1. **No UObject access outside the game thread.** Every HTTP handler dispatches via `AsyncTask(ENamedThreads::GameThread, ...)`. No exceptions, no special cases.

2. **Every plugin response uses `BuildSuccessResponse` or `BuildErrorResponse`.** No hand-constructed JSON response objects in handler code.

3. **HTTP status is always 200.** Application errors are signaled by `"ok": false` in the response body, never by HTTP 4xx or 5xx status codes.

4. **The `OnComplete` callback is called exactly once per request.** Failing to call it leaks the request and eventually hangs the client. Calling it twice is undefined behavior.

5. **All editor-only module dependencies in `Build.cs` are inside `if (Target.bBuildEditor)`.** All editor-only includes in headers that may be transitively included by non-editor targets are inside `#if WITH_EDITOR`. Violating this breaks console builds.

6. **Tool names are frozen after v0.1.0.** Renaming or removing a tool parameter after release is a breaking change that requires a major version bump.

7. **`get_property` and `set_property` only support the Tier 1 type set.** Unsupported types return `UNSUPPORTED_PROPERTY_TYPE`. Silent failures and partial serialization are not acceptable.

8. **The Python client does not retry on `EditorError`.** The plugin returned a deliberate error response — retrying will not fix it. Retrying once on `EditorConnectionError` is acceptable but must be opt-in at the call site.

9. **Log capture uses `FOutputDevice` registration only.** `GLog->AddOutputDevice` on start, `GLog->RemoveOutputDevice` on stop. Never read log files from disk.

10. **`FUE5MCPLogCapture::Serialize` always acquires `Lock` before touching `Buffer`.** This method is called from arbitrary threads.

---

## 10. Claude Code Configuration

After installing the plugin and running `pip install ue5-mcp`, add this to the Claude Code MCP config file:

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

Or if running directly from source:

```json
{
  "mcpServers": {
    "ue5": {
      "command": "python",
      "args": ["-m", "ue5_mcp", "--editor-port", "8765"],
      "env": {}
    }
  }
}
```

Restart Claude Code after editing the config. The UE5 tool set will appear in Claude's available tools.

---

## 11. Testing Strategy

### Plugin (C++)

Manual integration testing during Tier 1 development. The `BuildSuccessResponse` and `BuildErrorResponse` helpers and any pure-logic functions (string parsing, type checking) can be covered with UE5 Automation Framework tests. A full compile check via `RunUAT BuildPlugin` should be added to CI once a Windows runner with a UE5 installation is available.

### Python MCP Server

Full unit test coverage for all tool handlers using `pytest` and `pytest-asyncio`. Mock the plugin HTTP layer with `respx` — tests must not require a running editor instance.

```python
# tests/conftest.py
import pytest
import respx
from ue5_mcp.client import EditorClient

@pytest.fixture
def mock_editor():
    """Mocks the plugin HTTP server. Use as a context manager in tests."""
    with respx.mock(base_url="http://localhost:8765/api/v1") as mock:
        yield mock

@pytest.fixture
def editor_client() -> EditorClient:
    return EditorClient("http://localhost:8765/api/v1", timeout=5.0)
```

Example test:

```python
# tests/tools/test_actors.py
import pytest
import respx
import httpx
from ue5_mcp.tools.actors import handle

@pytest.mark.asyncio
async def test_list_actors_success(mock_editor, editor_client):
    mock_editor.get("/actors/list").mock(return_value=httpx.Response(200, json={
        "ok": True,
        "data": {"actors": [{"name": "Floor", "class": "StaticMeshActor", "id": "abc123"}]}
    }))
    result = await handle("list_actors", editor_client, {})
    assert len(result) == 1
    assert "Floor" in result[0].text
```

---

## 12. Installation

### Plugin

1. Copy `plugin/UE5MCP/` into `YourProject/Plugins/`
2. Open UE5 — it will prompt to rebuild the plugin. Confirm.
3. Enable via Edit > Plugins > UE5 MCP if not auto-enabled.
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

With the editor open and the plugin running:

```bash
curl http://localhost:8765/api/v1/actors/list
```

Expected: `{"ok":true,"data":{"actors":[...]}}`
