#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

namespace UE5MCPConsoleHandlers
{
    // Registers: POST /api/v1/console/execute
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
}
