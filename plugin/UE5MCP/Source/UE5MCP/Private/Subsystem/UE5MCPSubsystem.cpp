#include "Subsystem/UE5MCPSubsystem.h"
#include "HttpServer/UE5MCPHttpServer.h"
#include "Logging/UE5MCPLogCapture.h"
#include "UE5MCPSettings.h"

DEFINE_LOG_CATEGORY_STATIC(LogUE5MCPSubsystem, Log, All);

void UUE5MCPSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    LogCapture = MakeShared<FUE5MCPLogCapture>();
    LogCapture->StartCapture();

    if (UUE5MCPSettings::Get()->bEnableOnStartup)
    {
        StartServer();
    }
}

void UUE5MCPSubsystem::Deinitialize()
{
    StopServer();

    if (LogCapture.IsValid())
    {
        LogCapture->StopCapture();
        LogCapture.Reset();
    }

    Super::Deinitialize();
}

void UUE5MCPSubsystem::StartServer()
{
    if (HttpServer.IsValid() && HttpServer->IsRunning())
    {
        UE_LOG(LogUE5MCPSubsystem, Warning, TEXT("Server already running."));
        return;
    }
    const int32 Port = UUE5MCPSettings::Get()->Port;
    HttpServer = MakeShared<FUE5MCPHttpServer>(LogCapture, Port);
    HttpServer->Start();
}

void UUE5MCPSubsystem::StopServer()
{
    if (HttpServer.IsValid())
    {
        HttpServer->Stop();
        HttpServer.Reset();
    }
}

bool UUE5MCPSubsystem::IsServerRunning() const
{
    return HttpServer.IsValid() && HttpServer->IsRunning();
}
