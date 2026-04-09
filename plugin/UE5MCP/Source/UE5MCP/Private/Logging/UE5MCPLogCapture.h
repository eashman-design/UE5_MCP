#pragma once
#include "CoreMinimal.h"
#include "Misc/OutputDevice.h"
#include "HAL/CriticalSection.h"

class FUE5MCPLogCapture : public FOutputDevice
{
public:
    static constexpr int32 MaxLines = 2000;

    FUE5MCPLogCapture() = default;
    virtual ~FUE5MCPLogCapture();

    void StartCapture();
    void StopCapture();

    // Thread-safe. Returns up to Count most recent lines, optionally filtered by category name.
    TArray<FString> GetRecentLines(int32 Count = 200, const FString& Category = TEXT("")) const;

protected:
    virtual void Serialize(const TCHAR* V, ELogVerbosity::Type Verbosity,
                           const FName& Category) override;
    virtual bool CanBeUsedOnAnyThread() const override { return true; }

private:
    mutable FCriticalSection Lock;
    TArray<FString> Buffer;
    bool bCapturing = false;
};
