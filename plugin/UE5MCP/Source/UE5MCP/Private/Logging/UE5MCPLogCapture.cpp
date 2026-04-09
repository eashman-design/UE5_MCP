#include "Logging/UE5MCPLogCapture.h"
#include "Misc/OutputDeviceRedirector.h"

FUE5MCPLogCapture::~FUE5MCPLogCapture()
{
    StopCapture();
}

void FUE5MCPLogCapture::StartCapture()
{
    if (!bCapturing)
    {
        GLog->AddOutputDevice(this);
        bCapturing = true;
    }
}

void FUE5MCPLogCapture::StopCapture()
{
    if (bCapturing && GLog)
    {
        GLog->RemoveOutputDevice(this);
        bCapturing = false;
    }
}

void FUE5MCPLogCapture::Serialize(const TCHAR* V, ELogVerbosity::Type Verbosity,
                                   const FName& Category)
{
    FScopeLock ScopeLock(&Lock);

    FString Line = FString::Printf(TEXT("[%s] %s: %s"),
        *FDateTime::Now().ToString(TEXT("%H:%M:%S")),
        *Category.ToString(),
        V);

    if (Buffer.Num() >= MaxLines)
    {
        Buffer.RemoveAt(0, 1, false);
    }
    Buffer.Add(MoveTemp(Line));
}

TArray<FString> FUE5MCPLogCapture::GetRecentLines(int32 Count, const FString& Category) const
{
    FScopeLock ScopeLock(&Lock);
    TArray<FString> Result;
    const int32 Start = FMath::Max(0, Buffer.Num() - Count);
    for (int32 i = Start; i < Buffer.Num(); ++i)
    {
        if (Category.IsEmpty() || Buffer[i].Contains(Category))
        {
            Result.Add(Buffer[i]);
        }
    }
    return Result;
}
