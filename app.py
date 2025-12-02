# app.py
import uuid
import time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict
from chat_bienestar import ChatBienestar
import threading

app = FastAPI()

# Montar carpeta static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

# Modelo para recibir mensaje
class Mensaje(BaseModel):
    session_id: str = None
    texto: str

# Session store en memoria: {session_id: {"chat": ChatBienestar(), "last_active": timestamp}}
sessions: Dict[str, Dict] = {}
SESSION_TIMEOUT_SECONDS = 20 * 60  # 20 minutos

lock = threading.Lock()

def purge_expired_sessions():
    """Elimina sesiones inactivas (correrse manualmente periódicamente)."""
    now = time.time()
    with lock:
        expired = [sid for sid, v in sessions.items() if now - v["last_active"] > SESSION_TIMEOUT_SECONDS]
        for sid in expired:
            del sessions[sid]

@app.post("/mensaje")
def procesar_mensaje(data: Mensaje):
    try:
        purge_expired_sessions()  # limpieza ligera en cada petición
        sid = data.session_id
        if not sid:
            # generar uno si no se envió
            sid = str(uuid.uuid4())

        with lock:
            session = sessions.get(sid)
            if not session:
                # crear nueva sesión con una instancia del chatbot
                sessions[sid] = {"chat": ChatBienestar(), "last_active": time.time()}
                session = sessions[sid]
            else:
                session["last_active"] = time.time()

            chatbot: ChatBienestar = session["chat"]

        respuesta = chatbot.procesar_mensaje(data.texto)
        return JSONResponse(content={"session_id": sid, "respuesta": respuesta})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
def health():
    return {"status": "ok", "active_sessions": len(sessions)}
