#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

namespace UE5MCPScreenshotHandlers
{
    // Registers: POST /api/v1/screenshot/capture
    // Default filename: ue5mcp_<timestamp>.png in Saved/Screenshots/
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
}
