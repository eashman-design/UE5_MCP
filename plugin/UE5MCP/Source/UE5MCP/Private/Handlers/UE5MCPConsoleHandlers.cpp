#include "Handlers/UE5MCPConsoleHandlers.h"
#include "HttpServer/UE5MCPResponseHelpers.h"

// TODO: Phase 3 — call GEngine->Exec(World, *Command) on game thread.
// Return INVALID_REQUEST_BODY if "command" field is missing or empty.

namespace UE5MCPConsoleHandlers
{
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router)
    {
        // Phase 3: wire routes here
    }
}
