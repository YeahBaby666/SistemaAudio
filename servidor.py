from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
import os
import uuid

app = FastAPI()

# Configuración CORS
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

# Formateador para Velocidad (exige %)
def formatear_velocidad(valor_float: float) -> str:
    porcentaje = int((valor_float - 1.0) * 100)
    return f"{porcentaje:+d}%"

# Formateador para Tono/Pitch (exige Hz según el Regex de la librería)
def formatear_tono(valor_float: float) -> str:
    # Mapeo simple: 1.0 -> +0Hz, 1.5 -> +50Hz, 0.5 -> -50Hz
    hz = int((valor_float - 1.0) * 100)
    return f"{hz:+d}Hz"

# NUEVO: Ruta raíz para servir la interfaz web al navegador del celular
@app.get("/")
async def servir_frontend():
    # Verifica que el archivo exista en la raíz del proyecto
    if not os.path.exists("cliente.html"):
        return {"error": "Archivo cliente.html no encontrado en el servidor."}
    return FileResponse("cliente.html")

@app.post("/api/sintetizar")
async def sintetizar_audio(req: PeticionTTS, background_tasks: BackgroundTasks):
    nombre_archivo = f"audio_generado_{uuid.uuid4().hex}.mp3"
    
    # Invocación corregida con los formateadores correctos
    communicate = edge_tts.Communicate(
        text=req.texto,
        voice=req.voz,
        rate=formatear_velocidad(req.velocidad),
        pitch=formatear_tono(req.tono)
    )
    
    await communicate.save(nombre_archivo)
    background_tasks.add_task(os.remove, nombre_archivo)
    
    return FileResponse(
        path=nombre_archivo, 
        media_type="audio/mpeg", 
        filename="tu_frase.mp3"
    )

if __name__ == "__main__":
    import uvicorn
    # Render asigna el puerto dinámicamente en la variable de entorno PORT
    # 0.0.0.0 permite que acepte conexiones externas (internet), no solo locales
    puerto = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=puerto)