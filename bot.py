import os
import time
import random
import threading
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime, timedelta

app = Flask(__name__)

# ==========================================
# 1. CONFIGURACIÓN (¡CAMBIA ESTO!)
# ==========================================
WAPPFLY_TOKEN = "AQUI_TU_TOKEN_DE_WAPPFLY"
DEEPSEEK_API_KEY = "AQUI_TU_API_KEY_DE_DEEPSEEK"
VERIFY_TOKEN = "palabra_secreta_123"
SESSION_NAME = "mi-sesion"

# ==========================================
# 2. CONFIGURACIÓN ANTI-DETECCIÓN
# ==========================================
SIMULATION_MODE = True  # True = Simulacro, False = Real
HOURLY_LIMIT = 20       # Límite de mensajes por hora
message_count = 0
hour_start = datetime.now()
lock = threading.Lock()

# ==========================================
# 3. CONFIGURAR DEEPSEEK
# ==========================================
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# ==========================================
# 4. FUNCIÓN: ENVIAR MENSAJE (CON SIMULACRO)
# ==========================================
def enviar_mensaje(numero, texto):
    global message_count, hour_start
    with lock:
        ahora = datetime.now()
        if ahora - hour_start > timedelta(hours=1):
            message_count = 0
            hour_start = ahora
        if message_count >= HOURLY_LIMIT:
            print(f"⛔ Límite de {HOURLY_LIMIT} mensajes/hora alcanzado.")
            return {"status": "limit_reached"}
        message_count += 1

    if SIMULATION_MODE:
        print(f"🧪 [SIMULACRO] Enviando a {numero}: {texto}")
        return {"status": "simulated"}

    time.sleep(random.uniform(0.5, 2.0))
    url = "https://api.wappfly.com/api/sendText"
    headers = {"apikey": WAPPFLY_TOKEN, "Content-Type": "application/json"}
    data = {"session": SESSION_NAME, "chatId": numero, "text": texto}
    try:
        respuesta = requests.post(url, headers=headers, json=data, timeout=10)
        return respuesta.json()
    except Exception as e:
        print(f"❌ Error al enviar: {e}")
        return {"status": "error", "details": str(e)}

# ==========================================
# 5. FUNCIÓN: PREGUNTAR A DEEPSEEK
# ==========================================
def preguntar_deepseek(mensaje_usuario):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": """
                Eres un asistente experto en arbitraje de apuestas hípicas.
                Tu misión es analizar mensajes de un grupo de WhatsApp para identificar oportunidades de arbitraje.

                REGLAS DE ARBITRAJE:
                - El arbitraje existe cuando (1/Cuota_A) + (1/Cuota_B) < 1
                - Si hay oportunidad, calcula el porcentaje y la cantidad a apostar en cada caballo para obtener una ganancia libre de riesgo.
                - Si no hay oportunidad, indica que no hay y sugiere esperar.

                INSTRUCCIONES:
                - Extrae números de caballo y sus cuotas. Reconoce sinónimos: "paga", "pago", "cotiza", "cuota", "rate", "odds".
                - Si el mensaje menciona un favorito (ej. "el 5 es el que va a ganar"), priorízalo.
                - Varía ligeramente el formato de tus respuestas para que no sean siempre idénticas.

                EJEMPLOS DE RESPUESTA:
                - Si hay arbitraje: "¡Oportunidad! 📈 Apostá 54.05€ al caballo 5 y 45.95€ al 8. Ganancia garantizada: 100€ 🏆"
                - Si no hay: "No hay oportunidad ahora. La suma es 1.02, lo que indica que no hay beneficio garantizado. Seguí monitoreando."

                Responde siempre en español, con un tono claro y directo.
                """},
                {"role": "user", "content": mensaje_usuario}
            ],
            temperature=random.uniform(0.8, 1.2)
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error con DeepSeek: {e}")
        return "Lo siento, tuve un problema al procesar tu mensaje."

# ==========================================
# 6. FUNCIÓN: PROCESAR COMANDOS
# ==========================================
def procesar_comando(mensaje):
    global SIMULATION_MODE, HOURLY_LIMIT
    partes = mensaje.lower().split()
    if not partes:
        return None
    comando = partes[0]

    if comando == "!estado":
        modo = "🧪 SIMULACRO" if SIMULATION_MODE else "✅ REAL"
        return f"📊 **Estado del Bot**\n- Modo: {modo}\n- Límite/hora: {HOURLY_LIMIT}\n- Mensajes enviados en la hora: {message_count}"
    elif comando == "!modo" and len(partes) > 1:
        if partes[1] == "real":
            SIMULATION_MODE = False
            return "✅ Cambiado a **MODO REAL**. Ahora enviaré mensajes de verdad."
        elif partes[1] == "simulacro":
            SIMULATION_MODE = True
            return "🧪 Cambiado a **MODO SIMULACRO**. Solo mostraré logs, no enviaré mensajes."
        else:
            return "❌ Modo no válido. Usa `!modo real` o `!modo simulacro`."
    elif comando == "!limite" and len(partes) > 1:
        try:
            nuevo_limite = int(partes[1])
            if 5 <= nuevo_limite <= 200:
                HOURLY_LIMIT = nuevo_limite
                return f"✅ Límite de mensajes por hora actualizado a **{nuevo_limite}**."
            else:
                return "❌ El límite debe estar entre 5 y 200."
        except ValueError:
            return "❌ Por favor, envía un número válido. Ej: `!limite 50`"
    elif comando == "!ayuda":
        return """
        📖 **Comandos disponibles:**
        - `!estado` → Ver estado del bot
        - `!modo real` → Activar envío real
        - `!modo simulacro` → Activar simulación (seguro)
        - `!limite [n]` → Cambiar límite de mensajes/hora
        - `!ayuda` → Mostrar esta ayuda
        """
    return None

# ==========================================
# 7. ENDPOINT: WEBHOOK DE WHATSAPP
# ==========================================
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return "OK", 200



    if request.method == 'POST':
        datos = request.json
        print("📩 Mensaje recibido:", datos)
        numero = datos.get('chatId')
        mensaje = datos.get('text')
        if not mensaje or not numero:
            return jsonify({"status": "ok"}), 200

        respuesta_comando = procesar_comando(mensaje)
        if respuesta_comando:
            enviar_mensaje(numero, respuesta_comando)
            return jsonify({"status": "ok"}), 200

        time.sleep(random.uniform(1.0, 4.0))
        respuesta_ia = preguntar_deepseek(mensaje)
if respuesta_ia:
    enviar_mensaje(numero, respuesta_ia)
else:
    enviar_mensaje(numero, "No pude procesar tu mensaje. Intenta con '!estado'.")
        return jsonify({"status": "ok"}), 200

# ==========================================
# 8. PUNTO DE ENTRADA (CORREGIDO)
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    modo = "🧪 SIMULACRO" if SIMULATION_MODE else "✅ REAL"
    print(f"🚀 Bot iniciado en modo {modo}")
    print(f"📊 Límite de mensajes por hora: {HOURLY_LIMIT}")
    app.run(host='0.0.0.0', port=port)
