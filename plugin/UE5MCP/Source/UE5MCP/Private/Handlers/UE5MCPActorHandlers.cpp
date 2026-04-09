#include "Handlers/UE5MCPActorHandlers.h"
#include "HttpServer/UE5MCPResponseHelpers.h"
#include "HttpPath.h"
#include "HttpServerRequest.h"
#include "Async/Async.h"
#include "EngineUtils.h"
#include "Editor.h"

// TODO: Phase 3 — implement list, spawn, delete routes.
// All UObject access must be dispatched via AsyncTask(ENamedThreads::GameThread, ...).
// See DESIGN.md §4.8 for the required threading pattern.

namespace UE5MCPActorHandlers
{
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router)
    {
        // Phase 3: wire routes here
    }
}
