from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PeticionTTS(BaseModel):
    texto: str
    voz: str = "es-ES-AlvaroNeural"
    tono: float = 1.0
    velocidad: float = 1.0

def formatear_velocidad(valor_float: float) -> str:
    porcentaje = int((valor_float - 1.0) * 100)
    return f"{porcentaje:+d}%"

def formatear_tono(valor_float: float) -> str:
    hz = int((valor_float - 1.0) * 100)
    return f"{hz:+d}Hz"

@app.get("/")
async def servir_frontend():
    if not os.path.exists("cliente.html"):
        return {"error": "Archivo cliente.html no encontrado en el servidor."}
    return FileResponse("cliente.html")

@app.post("/api/sintetizar")
async def sintetizar_audio(req: PeticionTTS):
    # Configurar la comunicación con Microsoft
    communicate = edge_tts.Communicate(
        text=req.texto,
        voice=req.voz,
        rate=formatear_velocidad(req.velocidad),
        pitch=formatear_tono(req.tono)
    )

    # Función asíncrona generadora de bytes (Stream)
    async def generador_audio():
        # edge-tts iterará sobre los datos que Microsoft envía en tiempo real
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    # Devolvemos el flujo de bytes directamente al frontend (Cero uso de disco duro)
    return StreamingResponse(
        generador_audio(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"attachment; filename=tu_frase.mp3"}
    )

if __name__ == "__main__":
    import uvicorn
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=puerto)