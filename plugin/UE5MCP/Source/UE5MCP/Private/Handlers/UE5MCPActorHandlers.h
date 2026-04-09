#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

namespace UE5MCPActorHandlers
{
    // Registers: GET /api/v1/actors/list
    //            POST /api/v1/actors/spawn
    //            POST /api/v1/actors/delete
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
}
