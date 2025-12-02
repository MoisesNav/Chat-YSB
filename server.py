from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chat_bienestar import ChatBienestar
import uuid

app = FastAPI()

# Sesiones: { session_id: ChatBienestar }
sesiones = {}

# Permitir front local o deployado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    session_id: str
    mensaje: str

@app.post("/mensajear")
def mensajear(data: Message):
    session_id = data.session_id

    # Crear sesión si no existe
    if session_id not in sesiones:
        sesiones[session_id] = ChatBienestar()

    respuesta = sesiones[session_id].procesar_mensaje(data.mensaje)
    return {"respuesta": respuesta}

@app.get("/nueva_sesion")
def nueva_sesion():
    nuevo_id = str(uuid.uuid4())
    sesiones[nuevo_id] = ChatBienestar()
    return {"session_id": nuevo_id}

@app.get("/cerrar_sesion/{session_id}")
def cerrar_sesion(session_id: str):
    if session_id in sesiones:
        del sesiones[session_id]
    return {"ok": True}
