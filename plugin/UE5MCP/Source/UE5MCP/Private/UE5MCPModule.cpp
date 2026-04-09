#include "UE5MCPModule.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FUE5MCPModule, UE5MCP)
DEFINE_LOG_CATEGORY_STATIC(LogUE5MCP, Log, All);

void FUE5MCPModule::StartupModule()
{
    UE_LOG(LogUE5MCP, Log, TEXT("UE5MCP module loaded."));
}

void FUE5MCPModule::ShutdownModule()
{
    UE_LOG(LogUE5MCP, Log, TEXT("UE5MCP module unloaded."));
}
