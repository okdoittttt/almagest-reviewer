from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/github/webhook")
async def github_webhook(request: Request):
    payload = await request.json()

    # 디버깅용
    print("Received event:")
    print(payload.get("action"))

    return JSONResponse({"status": "success"})