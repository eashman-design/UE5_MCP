#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

namespace UE5MCPTransformHandlers
{
    // Registers: POST /api/v1/transform/get
    //            POST /api/v1/transform/set
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
}
