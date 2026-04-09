#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

namespace UE5MCPPropertyHandlers
{
    // Registers: POST /api/v1/property/get
    //            POST /api/v1/property/set
    // Supported types: bool, int32, float, FString, FName, FVector, FRotator, FLinearColor
    void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
}
