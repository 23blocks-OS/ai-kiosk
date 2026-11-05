"""Agent backend skeleton (STUB).

FastAPI service that will run on the Jetson next to the kiosk web app.
For now every AI endpoint is a clearly-marked stub returning a canned
reply, so the front end can be wired and tested before the local model
is installed. Nothing here calls a cloud service.
"""

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

app = FastAPI(title="ai-kiosk agent-backend (stub)")


class ChatRequest(BaseModel):
    message: str
    lang: str = "es"


class ChatResponse(BaseModel):
    reply: str
    stub: bool = True


@app.get("/health")
def health():
    return {"status": "ok", "stub": True, "model": "not-connected"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # STUB: no model is connected yet. Replace with a call to the local
    # Qwen3-VL 4B server (llama.cpp / Ollama) once it runs on the Jetson.
    if req.lang.startswith("en"):
        reply = (
            "STUB — no local model connected yet. When the Jetson is ready, "
            "this reply will come from Qwen3-VL 4B running on-device."
        )
    else:
        reply = (
            "STUB — todavía no hay modelo local conectado. Cuando el Jetson "
            "esté listo, esta respuesta vendrá de Qwen3-VL 4B corriendo en el equipo."
        )
    return ChatResponse(reply=reply, stub=True)


@app.post("/api/vision")
async def vision(image: UploadFile = File(...)):
    # STUB: accepts an image (e.g. the frozen PiP frame) and returns a
    # canned description. Replace with a Qwen3-VL 4B vision call.
    data = await image.read()
    return {
        "stub": True,
        "filename": image.filename,
        "bytes_received": len(data),
        "description": (
            "STUB — no local model connected yet. "
            "When the Jetson is ready, Qwen3-VL 4B will describe this image "
            "and read any document in it."
        ),
    }
