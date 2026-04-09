#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

/**
 * Contract for all handler groups.
 * Each handler group must expose a static RegisterRoutes function matching one of:
 *
 *   static void RegisterRoutes(TSharedPtr<IHttpRouter> Router);
 *   static void RegisterRoutes(TSharedPtr<IHttpRouter> Router, TSharedPtr<FUE5MCPLogCapture> LogCapture);
 *
 * This header documents the convention — it is not a virtual interface.
 * Adding a new handler group: implement RegisterRoutes, then call it from
 * FUE5MCPHttpServer::RegisterAllRoutes in UE5MCPHttpServer.cpp.
 */
