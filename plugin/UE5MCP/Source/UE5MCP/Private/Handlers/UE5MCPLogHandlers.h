#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

class FUE5MCPLogCapture;

namespace UE5MCPLogHandlers
{
    // Registers: GET /api/v1/logs/get?count=200&category=
    // count clamped to [1, 2000]; category is optional substring filter.
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router, TSharedPtr<FUE5MCPLogCapture> LogCapture);
}
