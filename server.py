from fastapi import FastAPI
from pydantic import BaseModel
from chat_bienestar import ChatBienestar

app = FastAPI()
chat = ChatBienestar()  # instancia global

class Message(BaseModel):
    mensaje: str

@app.post("/mensajear")
def mensajear(msg: Message):
    respuesta = chat.procesar_mensaje(msg.mensaje)
    return {"respuesta": respuesta}
