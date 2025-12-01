"""
Sistema de Chat Automatizado para Yo Soy Bienestar
Módulo de verificación de clientes y consulta de recargas
"""

import requests
import re
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime


class ChatBienestar:
    """
    Clase principal para el sistema de chat automatizado que verifica 
    clientes y consulta estado de recargas mediante API.
    """
    
    # Constantes de configuración
    TIMEOUT_API = 60  # segundos
    ESTADOS = {
        "INICIO": "inicio",
        "SOLICITAR_NUMERO": "solicitar_numero", 
        "MENU_PRINCIPAL": "menu_principal",
        "SOLICITAR_REFERENCIA": "solicitar_referencia",
        "FINALIZADO": "finalizado"
    }
    
    def __init__(self) -> None:
        """Inicializa la instancia del chat con configuración base."""
        self.base_url = "https://recargasyventassims.yosoybienestar.com/YSB"
        self.estado = self.ESTADOS["INICIO"]
        self.numero_verificado = None
        self.datos_cliente = None

    def validar_numero_telefonico(self, numero: str) -> Tuple[bool, Optional[str]]:
        """
        Valida el formato del número telefónico.
        
        Args:
            numero (str): Número telefónico a validar
            
        Returns:
            Tuple[bool, Optional[str]]: (True, número_limpio) si es válido, 
                                       (False, None) si es inválido
        """
        numero_limpio = re.sub(r'[^\d]', '', numero)
        
        if len(numero_limpio) == 10 and numero_limpio.isdigit():
            return True, numero_limpio
            
        return False, None

    def _realizar_peticion_api(self, url: str) -> Union[Dict, str, None]:
        """
        Realiza petición HTTP GET a la API con manejo de errores.
        
        Args:
            url (str): URL completa para la petición API
            
        Returns:
            Union[Dict, str, None]: Datos de respuesta, "timeout" en caso de timeout,
                                   o None en caso de error
        """
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
        """
        Verifica la existencia del cliente en la API.
        
        Args:
            numero (str): Número telefónico del cliente
            
        Returns:
            Union[List[Dict], str, None]: Datos del cliente, "timeout" o None
        """
        url = f"{self.base_url}/sim/{numero}/msisdn"
        return self._realizar_peticion_api(url)

    def verificar_recarga_api(self, referencia: str) -> Union[Dict, str, None]:
        """
        Verifica el estado de una recarga por referencia.
        
        Args:
            referencia (str): Número de referencia de la recarga
            
        Returns:
            Union[Dict, str, None]: Datos de la recarga, "timeout" o None
        """
        url = f"{self.base_url}/payment/{referencia}"
        return self._realizar_peticion_api(url)

    def _procesar_estado_inicio(self, mensaje: str) -> str:
        """
        Procesa mensajes en estado inicial del chat.
        
        Args:
            mensaje (str): Mensaje del usuario
            
        Returns:
            str: Respuesta del bot
        """
        if "hola" in mensaje:
            self.estado = self.ESTADOS["SOLICITAR_NUMERO"]
            return self._mensaje_bienvenida()
        else:
            return "Por favor inicia la conversación con 'Hola'"

    def _procesar_estado_solicitar_numero(self, mensaje: str) -> str:
        """
        Procesa la validación y verificación del número telefónico.
        
        Args:
            mensaje (str): Número proporcionado por el usuario
            
        Returns:
            str: Respuesta del bot con resultado de verificación
        """
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
        """
        Procesa la selección de opciones del menú principal.
        
        Args:
            mensaje (str): Opción seleccionada por el usuario
            
        Returns:
            str: Respuesta según la opción seleccionada
        """
        opciones = {
            "1": self._manejar_opcion_recarga,
            "2": self._manejar_opcion_otro_reporte,
            "3": self._manejar_opcion_salir
        }
        
        manejador = opciones.get(mensaje, self._manejar_opcion_invalida)
        return manejador()

    def _procesar_estado_solicitar_referencia(self, mensaje: str) -> str:
        """
        Procesa la verificación de referencia de recarga.
        
        Args:
            mensaje (str): Referencia proporcionada por el usuario
            
        Returns:
            str: Resultado de la verificación de recarga
        """
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
        """
        Procesa el mensaje del usuario según el estado actual del chat.
        
        Args:
            mensaje (str): Mensaje de entrada del usuario
            
        Returns:
            str: Respuesta del bot
        """
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

    # Métodos auxiliares para mensajes y formateo
    def _mensaje_bienvenida(self) -> str:
        """Retorna mensaje de bienvenida inicial."""
        return (
            "¡Hola! 👋 Bienvenido a Yo Soy Bienestar.\n\n"
            "Por favor comparte tu número telefónico para verificar que eres cliente Yo Soy Bienestar."
        )

    def _mensaje_timeout(self) -> str:
        """Retorna mensaje de timeout en verificación."""
        return (
            "❌ ⏱️ La verificación está tomando más tiempo de lo esperado. "
            "Por favor intenta nuevamente más tarde."
        )

    def _mensaje_verificacion_exitosa(self) -> str:
        """Retorna mensaje de verificación exitosa con datos del cliente."""
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
        """Maneja la opción de reportar problema con recarga."""
        self.estado = self.ESTADOS["SOLICITAR_REFERENCIA"]
        return (
            "📋 Reportar Problema con Recarga\n\n"
            "Por favor ingresa el número de referencia de tu recarga:"
        )

    def _manejar_opcion_otro_reporte(self) -> str:
        """Maneja la opción de otros tipos de reporte."""
        self.estado = self.ESTADOS["FINALIZADO"]
        return (
            "ℹ️ Realizar otro tipo de reporte\n\n"
            "Esta funcionalidad actualmente no está desarrollada ni implementada.\n\n"
            "Gracias por contactarnos. 👋"
        )

    def _manejar_opcion_salir(self) -> str:
        """Maneja la opción de salir del chat."""
        self.estado = self.ESTADOS["FINALIZADO"]
        return "👋 ¡Gracias por usar nuestro servicio! Que tengas un excelente día."

    def _manejar_opcion_invalida(self) -> str:
        """Maneja opciones inválidas en el menú principal."""
        return (
            "⚠️ Opción no válida. Por favor selecciona:\n\n"
            "1️⃣ Reportar problema con recarga\n"
            "2️⃣ Realizar otro tipo de reporte\n"  
            "3️⃣ Salir del chat\n\n"
            "Escribe 1, 2 o 3:"
        )

    def _mensaje_timeout_recarga(self) -> str:
        """Retorna mensaje de timeout en verificación de recarga."""
        return (
            "❌ ⏱️ La verificación de la recarga está tomando más tiempo de lo esperado. "
            "Por favor intenta nuevamente más tarde o contacta a soporte."
        )

    def _formatear_informacion_recarga(self, datos_recarga: Dict, referencia: str) -> str:
        """
        Formatea la información de la recarga para mostrar al usuario.
        
        Args:
            datos_recarga (Dict): Datos completos de la recarga desde la API
            referencia (str): Número de referencia proporcionado
            
        Returns:
            str: Mensaje formateado con la información de la recarga
        """
        data = datos_recarga.get("data", {})
        
        # Extraer información relevante
        referencia_real = data.get("paymentMethod", {}).get("reference", referencia)
        nombre_cliente = f"{data.get('customer', {}).get('name', 'N/A')} {data.get('customer', {}).get('lastName', '')}"
        telefono = data.get("customer", {}).get("phoneNumber", "N/A")
        monto = data.get("amount", "N/A")
        estado = data.get("status", "N/A")
        autorizacion = data.get("authorization", "N/A")
        
        # Formatear fechas
        fecha_creacion = self._formatear_fecha(data.get("creationDate"))
        fecha_operacion = self._formatear_fecha(data.get("operationDate"))
        fecha_vencimiento = self._formatear_fecha(data.get("dueDate"))
        
        # Determinar emoji de estado
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
        """
        Formatea una fecha ISO a formato legible.
        
        Args:
            fecha_str (str): Fecha en formato ISO
            
        Returns:
            str: Fecha formateada o "N/A" si no está disponible
        """
        if not fecha_str:
            return "N/A"
        
        try:
            # Manejar diferentes formatos de fecha
            if 'T' in fecha_str:
                fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            else:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                
            return fecha_obj.strftime('%d/%m/%Y %H:%M:%S')
        except (ValueError, TypeError):
            return "N/A"

    def _traducir_estado(self, estado: str) -> str:
        """
        Traduce el estado de la recarga al español.
        
        Args:
            estado (str): Estado en inglés
            
        Returns:
            str: Estado traducido al español
        """
        traducciones = {
            "completed": "Completado",
            "pending": "Pendiente",
            "failed": "Fallido",
            "cancelled": "Cancelado",
            "in_progress": "En Progreso"
        }
        return traducciones.get(estado, estado)

    def _mensaje_referencia_no_encontrada(self, referencia: str) -> str:
        """Retorna mensaje cuando no se encuentra la referencia."""
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

    def iniciar_chat_interactivo(self) -> None:
        """
        Inicia el chat interactivo por consola.
        
        Maneja la interacción completa con el usuario mediante entrada/salida estándar.
        """
        self._mostrar_encabezado()
        
        # Mensaje inicial
        print("Bot: ¡Hola! 👋 Bienvenido a Yo Soy Bienestar.")
        print("Bot: Por favor inicia la conversación con 'Hola'")
        
        while True:
            try:
                if self.estado == self.ESTADOS["FINALIZADO"]:
                    print("\n💬 Conversación finalizada.")
                    break
                
                entrada_usuario = input("\nTú: ").strip()
                
                if entrada_usuario.lower() == 'salir':
                    print("Bot: 👋 ¡Gracias por contactarnos! Hasta pronto.")
                    break
                
                respuesta = self.procesar_mensaje(entrada_usuario)
                print(f"Bot: {respuesta}")
                
            except KeyboardInterrupt:
                print("\n\nBot: 👋 ¡Conversación interrumpida! Hasta pronto.")
                break
            except Exception as error:
                print(f"\nBot: ❌ Ocurrió un error inesperado. Por favor intenta nuevamente.")
                # Para debugging: print(f"Debug: {error}")

    def _mostrar_encabezado(self) -> None:
        """Muestra el encabezado del chat."""
        print("=" * 60)
        print("🤖 CHAT AUTOMATIZADO - YO SOY BIENESTAR")
        print("=" * 60)
        print("Escribe 'salir' en cualquier momento para terminar\n")
        print("⚠️  Nota: Las verificaciones pueden tomar hasta 60 segundos\n")


def ejecutar_chat() -> None:
    """
    Función principal para ejecutar el sistema de chat.
    
    Crea una instancia del chat y inicia la conversación interactiva.
    """
    instancia_chat = ChatBienestar()
    instancia_chat.iniciar_chat_interactivo()


if __name__ == "__main__":
    ejecutar_chat()