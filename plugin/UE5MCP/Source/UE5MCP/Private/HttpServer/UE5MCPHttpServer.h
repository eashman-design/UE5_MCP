#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"

class FUE5MCPLogCapture;

class FUE5MCPHttpServer
{
public:
    explicit FUE5MCPHttpServer(TSharedPtr<FUE5MCPLogCapture> InLogCapture, int32 InPort);
    ~FUE5MCPHttpServer();

    void Start();
    void Stop();
    bool IsRunning() const { return bRunning; }

private:
    void RegisterAllRoutes();

    TSharedPtr<IHttpRouter> Router;
    TSharedPtr<FUE5MCPLogCapture> LogCapture;
    int32 Port;
    bool bRunning = false;
};
