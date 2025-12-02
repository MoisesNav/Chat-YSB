# chat_bienestar.py
"""
Sistema de Chat Automatizado para Yo Soy Bienestar
Módulo de verificación de clientes y consulta de recargas
(versión lista para importar)
"""

import requests
import re
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

class ChatBienestar:
    TIMEOUT_API = 60  # segundos
    ESTADOS = {
        "INICIO": "inicio",
        "SOLICITAR_NUMERO": "solicitar_numero",
        "MENU_PRINCIPAL": "menu_principal",
        "SOLICITAR_REFERENCIA": "solicitar_referencia",
        "FINALIZADO": "finalizado"
    }

    def __init__(self) -> None:
        self.base_url = "https://recargasyventassims.yosoybienestar.com/YSB"
        self.estado = self.ESTADOS["INICIO"]
        self.numero_verificado = None
        self.datos_cliente = None

    def validar_numero_telefonico(self, numero: str) -> Tuple[bool, Optional[str]]:
        numero_limpio = re.sub(r'[^\d]', '', numero)
        if len(numero_limpio) == 10 and numero_limpio.isdigit():
            return True, numero_limpio
        return False, None

    def _realizar_peticion_api(self, url: str) -> Union[Dict, str, None]:
        try:
            respuesta = requests.get(url, timeout=self.TIMEOUT_API)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return datos if datos else {}
            else:
                return {}
        except requests.exceptions.Timeout:
            return "timeout"
        except requests.exceptions.RequestException as error:
            print(f"Error de conexión con la API: {error}")
            return {}
        except Exception as error:
            print(f"Error inesperado en petición API: {error}")
            return {}

    def verificar_cliente_api(self, numero: str) -> Union[List[Dict], str, None]:
        url = f"{self.base_url}/sim/{numero}/msisdn"
        return self._realizar_peticion_api(url)

    def verificar_recarga_api(self, referencia: str) -> Union[Dict, str, None]:
        url = f"{self.base_url}/payment/{referencia}"
        return self._realizar_peticion_api(url)

    # --- lógica de estados (igual a la tuya) ---
    def _procesar_estado_inicio(self, mensaje: str) -> str:
        if "hola" in mensaje:
            self.estado = self.ESTADOS["SOLICITAR_NUMERO"]
            return self._mensaje_bienvenida()
        else:
            return "Por favor inicia la conversación con 'Hola'"

    def _procesar_estado_solicitar_numero(self, mensaje: str) -> str:
        es_valido, numero_limpio = self.validar_numero_telefonico(mensaje)
        if not es_valido:
            return "⚠️ Por favor ingresa un número telefónico válido de 10 dígitos."

        print("⏳ Verificando número en la API...")
        resultado_api = self.verificar_cliente_api(numero_limpio)
        if resultado_api == "timeout":
            self.estado = self.ESTADOS["FINALIZADO"]
            return self._mensaje_timeout()
        if resultado_api:
            self.datos_cliente = resultado_api[0] if isinstance(resultado_api, list) else resultado_api
            self.numero_verificado = numero_limpio
            self.estado = self.ESTADOS["MENU_PRINCIPAL"]
            return self._mensaje_verificacion_exitosa()
        else:
            self.estado = self.ESTADOS["FINALIZADO"]
            return "❌ No eres cliente, no podemos hacer más. Gracias por contactarnos. 👋"

    def _procesar_estado_menu_principal(self, mensaje: str) -> str:
        opciones = {
            "1": self._manejar_opcion_recarga,
            "2": self._manejar_opcion_otro_reporte,
            "3": self._manejar_opcion_salir
        }
        manejador = opciones.get(mensaje, self._manejar_opcion_invalida)
        return manejador()

    def _procesar_estado_solicitar_referencia(self, mensaje: str) -> str:
        referencia = mensaje.strip()
        if not referencia:
            return "⚠️ Por favor ingresa un número de referencia válido."

        print("⏳ Verificando recarga en la API...")
        resultado_recarga = self.verificar_recarga_api(referencia)
        if resultado_recarga == "timeout":
            self.estado = self.ESTADOS["FINALIZADO"]
            return self._mensaje_timeout_recarga()
        if resultado_recarga and resultado_recarga.get("code") == 0:
            self.estado = self.ESTADOS["FINALIZADO"]
            return self._formatear_informacion_recarga(resultado_recarga, referencia)
        else:
            self.estado = self.ESTADOS["FINALIZADO"]
            return self._mensaje_referencia_no_encontrada(referencia)

    def procesar_mensaje(self, mensaje: str) -> str:
        mensaje_limpio = mensaje.strip().lower()
        manejadores_estado = {
            self.ESTADOS["INICIO"]: self._procesar_estado_inicio,
            self.ESTADOS["SOLICITAR_NUMERO"]: self._procesar_estado_solicitar_numero,
            self.ESTADOS["MENU_PRINCIPAL"]: self._procesar_estado_menu_principal,
            self.ESTADOS["SOLICITAR_REFERENCIA"]: self._procesar_estado_solicitar_referencia
        }
        if self.estado == self.ESTADOS["FINALIZADO"]:
            return "La conversación ha finalizado. Si necesitas ayuda, por favor inicia una nueva conversación."

        manejador = manejadores_estado.get(self.estado)
        return manejador(mensaje_limpio) if manejador else "Estado no válido"

    # --- mensajes y formateo (igual que los tuyos) ---
    def _mensaje_bienvenida(self) -> str:
        return (
            "¡Hola! 👋 Bienvenido a Yo Soy Bienestar.\n\n"
            "Por favor comparte tu número telefónico para verificar que eres cliente Yo Soy Bienestar."
        )

    def _mensaje_timeout(self) -> str:
        return (
            "❌ ⏱️ La verificación está tomando más tiempo de lo esperado. "
            "Por favor intenta nuevamente más tarde."
        )

    def _mensaje_verificacion_exitosa(self) -> str:
        return f"""✅ ¡Verificación exitosa! 

Hola bienvenido Cliente Yo Soy Bienestar.

📱 Número: {self.datos_cliente.get('msisdn', 'N/A')}
⚡ Servicio: {self.datos_cliente.get('altanService', 'N/A')}
🟢 Estado: {self.datos_cliente.get('altanStatus', 'N/A')}

¿Qué operación deseas realizar?

1️⃣ Reportar problema con recarga
2️⃣ Realizar otro tipo de reporte  
3️⃣ Salir del chat

Por favor selecciona una opción (1, 2 o 3):"""

    def _manejar_opcion_recarga(self) -> str:
        self.estado = self.ESTADOS["SOLICITAR_REFERENCIA"]
        return (
            "📋 Reportar Problema con Recarga\n\n"
            "Por favor ingresa el número de referencia de tu recarga:"
        )

    def _manejar_opcion_otro_reporte(self) -> str:
        self.estado = self.ESTADOS["FINALIZADO"]
        return (
            "ℹ️ Realizar otro tipo de reporte\n\n"
            "Esta funcionalidad actualmente no está desarrollada ni implementada.\n\n"
            "Gracias por contactarnos. 👋"
        )

    def _manejar_opcion_salir(self) -> str:
        self.estado = self.ESTADOS["FINALIZADO"]
        return "👋 ¡Gracias por usar nuestro servicio! Que tengas un excelente día."

    def _manejar_opcion_invalida(self) -> str:
        return (
            "⚠️ Opción no válida. Por favor selecciona:\n\n"
            "1️⃣ Reportar problema con recarga\n"
            "2️⃣ Realizar otro tipo de reporte\n"  
            "3️⃣ Salir del chat\n\n"
            "Escribe 1, 2 o 3:"
        )

    def _mensaje_timeout_recarga(self) -> str:
        return (
            "❌ ⏱️ La verificación de la recarga está tomando más tiempo de lo esperado. "
            "Por favor intenta nuevamente más tarde o contacta a soporte."
        )

    def _formatear_informacion_recarga(self, datos_recarga: Dict, referencia: str) -> str:
        data = datos_recarga.get("data", {})
        referencia_real = data.get("paymentMethod", {}).get("reference", referencia)
        nombre_cliente = f"{data.get('customer', {}).get('name', 'N/A')} {data.get('customer', {}).get('lastName', '')}"
        telefono = data.get("customer", {}).get("phoneNumber", "N/A")
        monto = data.get("amount", "N/A")
        estado = data.get("status", "N/A")
        autorizacion = data.get("authorization", "N/A")
        fecha_creacion = self._formatear_fecha(data.get("creationDate"))
        fecha_operacion = self._formatear_fecha(data.get("operationDate"))
        fecha_vencimiento = self._formatear_fecha(data.get("dueDate"))
        emoji_estado = "✅" if estado == "completed" else "⏳" if estado == "pending" else "❌"
        estado_formateado = self._traducir_estado(estado)

        return f"""✅ **Información de Recarga Encontrada**

📊 **Referencia:** {referencia_real}
👤 **Cliente:** {nombre_cliente.strip()}
📱 **Teléfono:** {telefono}
💰 **Monto:** ${monto} MXN
{emoji_estado} **Estado:** {estado_formateado}
🔢 **Autorización:** {autorizacion}

📅 **Fechas:**
   • Creación: {fecha_creacion}
   • Operación: {fecha_operacion}
   • Vencimiento: {fecha_vencimiento}

📋 **Descripción:** {datos_recarga.get('message', 'Recarga Telefonia Celular - Yo Soy Bienestar')}

¡Gracias por ser parte de Yo Soy Bienestar! 👋"""

    def _formatear_fecha(self, fecha_str: str) -> str:
        if not fecha_str:
            return "N/A"
        try:
            if 'T' in fecha_str:
                fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            else:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            return fecha_obj.strftime('%d/%m/%Y %H:%M:%S')
        except (ValueError, TypeError):
            return "N/A"

    def _traducir_estado(self, estado: str) -> str:
        traducciones = {
            "completed": "Completado",
            "pending": "Pendiente",
            "failed": "Fallido",
            "cancelled": "Cancelado",
            "in_progress": "En Progreso"
        }
        return traducciones.get(estado, estado)

    def _mensaje_referencia_no_encontrada(self, referencia: str) -> str:
        return f"""❌ **Referencia No Encontrada**

La referencia **'{referencia}'** no fue encontrada en nuestro sistema.

**Posibles causas:**
• La referencia puede ser incorrecta
• La transacción está aún en proceso
• Puede haber un error en el sistema

Te recomendamos:
1. Verificar el número de referencia
2. Esperar unos minutos si acabas de realizar la recarga
3. Contactar a nuestro equipo de soporte si el problema persiste

¡Gracias por contactarnos! 👋"""
