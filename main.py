from fastapi import FastAPI
from pydantic import BaseModel
from chat_bienestar import ChatBienestar   # tu clase va en chat.py

app = FastAPI()
bot = ChatBienestar()

class Mensaje(BaseModel):
    texto: str

@app.post("/chat")
def procesar(mensaje: Mensaje):
    respuesta = bot.procesar_mensaje(mensaje.texto)
    return {"respuesta": respuesta}
