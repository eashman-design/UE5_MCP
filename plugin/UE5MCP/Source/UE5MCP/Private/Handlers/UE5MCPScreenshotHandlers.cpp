#include "Handlers/UE5MCPScreenshotHandlers.h"
#include "HttpServer/UE5MCPResponseHelpers.h"

// TODO: Phase 3 — use FScreenshotRequest::RequestScreenshot on game thread.
// Return absolute path to saved PNG. Return SCREENSHOT_FAILED on failure.

namespace UE5MCPScreenshotHandlers
{
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router)
    {
        // Phase 3: wire routes here
    }
}
