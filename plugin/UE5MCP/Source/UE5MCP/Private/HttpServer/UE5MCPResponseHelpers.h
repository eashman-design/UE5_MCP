#pragma once
#include "CoreMinimal.h"
#include "HttpServerResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

struct FUE5MCPResponseHelpers
{
    // { "ok": true, "data": { ... } }
    static TUniquePtr<FHttpServerResponse> BuildSuccessResponse(
        TSharedPtr<FJsonObject> Data)
    {
        TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
        Root->SetBoolField(TEXT("ok"), true);
        Root->SetObjectField(TEXT("data"), Data);
        return JsonObjectToResponse(Root);
    }

    // { "ok": false, "error": "Human readable message", "code": "MACHINE_CODE" }
    static TUniquePtr<FHttpServerResponse> BuildErrorResponse(
        const FString& Message,
        const FString& Code)
    {
        TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
        Root->SetBoolField(TEXT("ok"), false);
        Root->SetStringField(TEXT("error"), Message);
        Root->SetStringField(TEXT("code"), Code);
        return JsonObjectToResponse(Root);
    }

private:
    static TUniquePtr<FHttpServerResponse> JsonObjectToResponse(
        TSharedPtr<FJsonObject> JsonObj)
    {
        FString Body;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Body);
        FJsonSerializer::Serialize(JsonObj.ToSharedRef(), Writer);
        auto Response = FHttpServerResponse::Create(Body, TEXT("application/json"));
        Response->Code = EHttpServerResponseCodes::Ok;
        return Response;
    }
};
