import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Asistente de Revisión DEI", page_icon="💬")

# --- 2. PROMPT DE PRUEBA (VERSIÓN MÍNIMA) ---
# He eliminado casi todos los ejemplos, dejando solo las instrucciones y UNO de muestra.
# El objetivo es ver si la app funciona con un prompt mucho más ligero.
SYSTEM_PROMPT = """
# ROL Y MISIÓN
Actúa como un Asistente Experto en Comunicación Inclusiva. Tu misión es revisar el texto del usuario para asegurar que cumple con el documento de conocimiento proporcionado (MANUAL DE DIVERSIDAD, EQUIDAD E INCLUSIÓN). Eres un guardián de nuestros valores de profesionalismo y respeto.

# TAREA Y FORMATO DE RESPUESTA
Cuando un usuario te envíe un texto para revisar, basándote EXCLUSIVAMENTE en el manual proporcionado, sigue ESTRICTAMENTE estos 3 pasos:

1.  **IDENTIFICAR ERRORES:** Analiza el texto e identifica cualquier palabra o frase que no se alinee con el manual.
2.  **EXPLICAR AJUSTES:** Explica de forma clara y constructiva por qué esos elementos son problemáticos y sugiere alternativas.
3.  **PROPONER TEXTO MEJORADO:** Ofrece la versión final del texto, corregida y mejorada.

Si el texto ya es perfecto, felicita al usuario.

# EJEMPLO DE ENTRENAMIENTO
---
**Texto de ejemplo a revisar:** "Se busca un hombre para el puesto de asistente de depósito. Es requisito ser fuerte."
**Tu respuesta ideal:**
¡Hola! He revisado tu texto. Aquí tienes algunas sugerencias:
* En la frase "Se busca un hombre..."
    * **Observación:** Al especificar un género, excluimos talento. El manual recomienda usar lenguaje neutro.
    * **Sugerencia:** Podemos iniciar con **"Buscamos una persona..."**.
* Sobre la parte "Es requisito ser fuerte..."
    * **Observación:** El manual recomienda enfocarse en tareas concretas, no en atributos personales subjetivos.
    * **Sugerencia:** Podemos describirlo como **"Las responsabilidades incluyen el movimiento de equipamiento pesado."**.
---
**Propuesta de texto completo mejorado:**
"Buscamos una persona para el puesto de asistente de depósito. Las responsabilidades incluyen el movimiento de equipamiento pesado."
¡Buen trabajo al detallar los requisitos! Con estos ajustes queda impecable.
---
"""

# --- 3. CONFIGURACIÓN DEL MODELO Y SECRETS ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception:
    st.error("Error al configurar la API de Google. Asegúrate de haber añadido tu clave de API a los secretos de Streamlit.")
    st.stop()

# --- 4. GESTIÓN DEL ARCHIVO DE CONOCIMIENTO ---
@st.cache_resource
def upload_file_to_google(filepath):
    try:
        with st.spinner(f"Indexando el manual de conocimiento... por favor espera."):
            file = genai.upload_file(path=filepath, display_name="Manual DEI")
            while file.state.name == "PROCESSING":
                time.sleep(2)
                file = genai.get_file(file.name)
            if file.state.name == "FAILED":
                 raise ValueError("El procesamiento del archivo falló.")
            return file
    except Exception as e:
        st.error(f"No se pudo cargar el manual de conocimiento: {e}")
        st.stop()

# --- 5. LÓGICA DE LA APLICACIÓN ---
st.title("Asistente de Revisión DEI 💬")
st.write("Escribe el texto que deseas revisar. Te daré sugerencias basadas en nuestro Manual de Diversidad, Equidad e Inclusión.")

try:
    dei_file = upload_file_to_google("DEI_Manual.txt")
except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'DEI_Manual.txt'. Asegúrate de que esté subido a tu repositorio de GitHub.")
    st.stop()

model = genai.GenerativeModel(
    model_name='gemini-1.5-pro-latest',
    system_instruction=SYSTEM_PROMPT
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu texto aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Analizando con la guía DEI..."):
        response = model.generate_content([dei_file, prompt])
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

