#include "HttpServer/UE5MCPHttpServer.h"
#include "HttpServerModule.h"
#include "IHttpRouter.h"
#include "Logging/UE5MCPLogCapture.h"
#include "Handlers/UE5MCPActorHandlers.h"
#include "Handlers/UE5MCPTransformHandlers.h"
#include "Handlers/UE5MCPPropertyHandlers.h"
#include "Handlers/UE5MCPConsoleHandlers.h"
#include "Handlers/UE5MCPPIEHandlers.h"
#include "Handlers/UE5MCPScreenshotHandlers.h"
#include "Handlers/UE5MCPLogHandlers.h"

DEFINE_LOG_CATEGORY_STATIC(LogUE5MCPServer, Log, All);

FUE5MCPHttpServer::FUE5MCPHttpServer(TSharedPtr<FUE5MCPLogCapture> InLogCapture, int32 InPort)
    : LogCapture(InLogCapture), Port(InPort)
{
}

FUE5MCPHttpServer::~FUE5MCPHttpServer()
{
    Stop();
}

void FUE5MCPHttpServer::Start()
{
    FHttpServerModule& HttpServerModule = FHttpServerModule::Get();
    Router = HttpServerModule.GetHttpRouter(Port);

    if (!Router.IsValid())
    {
        UE_LOG(LogUE5MCPServer, Error, TEXT("Failed to get HTTP router on port %d"), Port);
        return;
    }

    RegisterAllRoutes();
    HttpServerModule.StartAllListeners();
    bRunning = true;
    UE_LOG(LogUE5MCPServer, Log, TEXT("UE5MCP HTTP server started on port %d"), Port);
}

void FUE5MCPHttpServer::Stop()
{
    if (!bRunning) return;
    FHttpServerModule::Get().StopAllListeners();
    Router.Reset();
    bRunning = false;
    UE_LOG(LogUE5MCPServer, Log, TEXT("UE5MCP HTTP server stopped."));
}

void FUE5MCPHttpServer::RegisterAllRoutes()
{
    UE5MCPActorHandlers::RegisterRoutes(Router);
    UE5MCPTransformHandlers::RegisterRoutes(Router);
    UE5MCPPropertyHandlers::RegisterRoutes(Router);
    UE5MCPConsoleHandlers::RegisterRoutes(Router);
    UE5MCPPIEHandlers::RegisterRoutes(Router);
    UE5MCPScreenshotHandlers::RegisterRoutes(Router);
    UE5MCPLogHandlers::RegisterRoutes(Router, LogCapture);
}
