#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

namespace UE5MCPPIEHandlers
{
    // Registers: POST /api/v1/pie/start
    //            POST /api/v1/pie/stop
    //            GET  /api/v1/pie/state
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
}
