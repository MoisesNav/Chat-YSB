# app.py
import uuid
import time
import threading
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
from chat_bienestar import ChatBienestar

app = FastAPI()

# Configurar CORS para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

# Modelo para recibir mensaje
class Mensaje(BaseModel):
    session_id: Optional[str] = None
    mensaje: str

# Session store en memoria
sessions: Dict[str, Dict] = {}
SESSION_TIMEOUT_SECONDS = 20 * 60  # 20 minutos
lock = threading.Lock()

def purge_expired_sessions():
    """Elimina sesiones inactivas."""
    now = time.time()
    with lock:
        expired = [sid for sid, v in sessions.items() 
                  if now - v["last_active"] > SESSION_TIMEOUT_SECONDS]
        for sid in expired:
            del sessions[sid]
            print(f"Sesión expirada eliminada: {sid}")

@app.post("/mensajear")
def procesar_mensaje(data: Mensaje):
    try:
        purge_expired_sessions()  # limpieza ligera en cada petición
        
        sid = data.session_id
        if not sid:
            # generar nueva sesión
            sid = str(uuid.uuid4())
            with lock:
                sessions[sid] = {
                    "chat": ChatBienestar(), 
                    "last_active": time.time()
                }
            return JSONResponse(content={
                "session_id": sid, 
                "respuesta": "¡Hola! 👋 Bienvenido a Yo Soy Bienestar.\n\nPor favor comparte tu número telefónico para verificar que eres cliente Yo Soy Bienestar."
            })

        with lock:
            session = sessions.get(sid)
            if not session:
                # Sesión no encontrada, crear nueva
                sessions[sid] = {
                    "chat": ChatBienestar(), 
                    "last_active": time.time()
                }
                session = sessions[sid]
                respuesta = "¡Hola! 👋 Bienvenido a Yo Soy Bienestar.\n\nPor favor comparte tu número telefónico para verificar que eres cliente Yo Soy Bienestar."
            else:
                session["last_active"] = time.time()
                chatbot: ChatBienestar = session["chat"]
                respuesta = chatbot.procesar_mensaje(data.mensaje)

        return JSONResponse(content={
            "session_id": sid, 
            "respuesta": respuesta
        })
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": str(e), "session_id": sid if 'sid' in locals() else None}
        )

@app.get("/nueva_sesion")
def nueva_sesion():
    """Crea una nueva sesión de chat"""
    sid = str(uuid.uuid4())
    with lock:
        sessions[sid] = {
            "chat": ChatBienestar(), 
            "last_active": time.time()
        }
    
    return JSONResponse(content={
        "session_id": sid,
        "respuesta": "¡Hola! 👋 Bienvenido a Yo Soy Bienestar.\n\nPor favor comparte tu número telefónico para verificar que eres cliente Yo Soy Bienestar."
    })

@app.get("/health")
def health():
    with lock:
        active_sessions = len(sessions)
    return {
        "status": "ok", 
        "active_sessions": active_sessions,
        "timestamp": time.time()
    }

@app.get("/debug_sessions")
def debug_sessions():
    """Endpoint para debugging (no usar en producción)"""
    with lock:
        session_info = {
            sid: {
                "last_active": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data["last_active"])),
                "estado_actual": data["chat"].estado,
                "numero_verificado": data["chat"].numero_verificado,
                "inactivo_segundos": time.time() - data["last_active"]
            }
            for sid, data in sessions.items()
        }
    return JSONResponse(content=session_info)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)