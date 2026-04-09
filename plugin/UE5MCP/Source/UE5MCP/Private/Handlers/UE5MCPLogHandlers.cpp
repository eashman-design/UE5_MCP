#include "Handlers/UE5MCPLogHandlers.h"
#include "Logging/UE5MCPLogCapture.h"
#include "HttpServer/UE5MCPResponseHelpers.h"

// TODO: Phase 3 — call LogCapture->GetRecentLines(count, category).
// Default count to 200; clamp to [1, 2000].

namespace UE5MCPLogHandlers
{
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router, TSharedPtr<FUE5MCPLogCapture> LogCapture)
    {
        // Phase 3: wire routes here
    }
}
