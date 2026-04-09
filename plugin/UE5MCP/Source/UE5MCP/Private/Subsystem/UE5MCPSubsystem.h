#pragma once
#include "EditorSubsystem.h"
#include "UE5MCPSubsystem.generated.h"

class FUE5MCPHttpServer;
class FUE5MCPLogCapture;

UCLASS()
class UUE5MCPSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable, Category="UE5MCP")
    void StartServer();

    UFUNCTION(BlueprintCallable, Category="UE5MCP")
    void StopServer();

    UFUNCTION(BlueprintCallable, Category="UE5MCP")
    bool IsServerRunning() const;

private:
    TSharedPtr<FUE5MCPHttpServer> HttpServer;
    TSharedPtr<FUE5MCPLogCapture> LogCapture;
};
