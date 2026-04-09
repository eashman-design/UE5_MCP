#pragma once
#include "Engine/DeveloperSettings.h"
#include "UE5MCPSettings.generated.h"

UCLASS(Config=Engine, DefaultConfig, meta=(DisplayName="UE5 MCP"))
class UUE5MCPSettings : public UDeveloperSettings
{
    GENERATED_BODY()

public:
    UUE5MCPSettings();

    virtual FName GetCategoryName() const override { return TEXT("Plugins"); }
    virtual FName GetSectionName() const override { return TEXT("UE5 MCP"); }

    UPROPERTY(Config, EditAnywhere, Category="Server", meta=(
        DisplayName="Port",
        ToolTip="Port the embedded HTTP server listens on. Default: 8765. Restart editor after changing."))
    int32 Port = 8765;

    UPROPERTY(Config, EditAnywhere, Category="Server", meta=(
        DisplayName="Enable on Startup",
        ToolTip="Automatically start the MCP HTTP server when the editor opens."))
    bool bEnableOnStartup = true;

    static const UUE5MCPSettings* Get() { return GetDefault<UUE5MCPSettings>(); }
};
