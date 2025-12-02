# app.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# importa tu clase ChatBienestar desde chat_bienestar.py
from chat_bienestar import ChatBienestar

app = FastAPI()

# Montar carpeta static para servir index.html, css, js, imágenes
app.mount("/static", StaticFiles(directory="static"), name="static")

# Página raíz sirve index.html
@app.get("/")
def root():
    return FileResponse("static/index.html")

# Endpoint de test simple
@app.get("/health")
def health():
    return {"status": "ok"}

# Modelo pydantic para recibir mensajes
class Mensaje(BaseModel):
    texto: str

# Instancia global del chatbot (mantiene estado en memoria mientras la app viva)
chatbot = ChatBienestar()

@app.post("/mensaje")
def procesar_mensaje(data: Mensaje):
    try:
        respuesta = chatbot.procesar_mensaje(data.texto)
        return JSONResponse(content={"respuesta": respuesta})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})