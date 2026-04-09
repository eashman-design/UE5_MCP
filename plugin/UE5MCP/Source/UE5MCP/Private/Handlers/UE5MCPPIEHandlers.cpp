#include "Handlers/UE5MCPPIEHandlers.h"
#include "HttpServer/UE5MCPResponseHelpers.h"

// TODO: Phase 3 — use GEditor->RequestPlaySession / RequestEndPlayMap.
// Check GEditor->IsPlaySessionRunning() and IsPlaySessionPaused() for state.
// Return PIE_ALREADY_RUNNING / PIE_NOT_RUNNING as appropriate.

namespace UE5MCPPIEHandlers
{
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router)
    {
        // Phase 3: wire routes here
    }
}
