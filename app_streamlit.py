"""
Interfaz Streamlit: UI, Gestión de Sesión y Evidencia.
"""
import streamlit as st
import uuid
from agent_core import stream_clinical_agent

st.set_page_config(page_title="Asistente Diagnóstico CIE-11", layout="wide")

# Paleta verde-azulada (salud), en lugar de los rojos/naranjas por defecto de Streamlit.
st.markdown("""
<style>
:root {
    --primary-color: #0F9B8E;
}
.stButton>button, button[kind="primary"] {
    background-color: #0F9B8E;
    border-color: #0F9B8E;
    color: white;
}
.stButton>button:hover, button[kind="primary"]:hover {
    background-color: #0C7D73;
    border-color: #0C7D73;
}
div.stSpinner > div > div {
    border-top-color: #0F9B8E !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #0F9B8E !important;
    box-shadow: 0 0 0 1px #0F9B8E !important;
    outline-color: #0F9B8E !important;
}
[data-testid="stChatMessageAvatarUser"] {
    background-color: #2E86AB !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background-color: #0F9B8E !important;
}
[data-testid="stChatInputSubmitButton"]:not(:disabled) {
    background-color: #0F9B8E !important;
}
[data-testid="stChatInputSubmitButton"]:not(:disabled):hover {
    background-color: #0C7D73 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🩺 Soporte para Evaluación Clínica CIE-11")

if "session_id" not in st.session_state:
    st.session_state.session_id = "eval-" + str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ Control de Evaluación")
    st.text(f"ID Sesión: {st.session_state.session_id}")
    if st.button("Nuevo Caso Clínico"):
        st.session_state.messages = []
        st.session_state.session_id = "eval-" + str(uuid.uuid4())[:8]
        st.rerun()

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

prompt = st.chat_input("Ingrese datos de la entrevista clínica o diagnóstico a contrastar...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        estado = st.status("Analizando consulta clínica...", expanded=True)
        answer = None
        trace = []
        try:
            for evento in stream_clinical_agent(prompt, st.session_state.session_id):
                tipo = evento.get("tipo")
                if tipo == "inicio":
                    estado.update(label=f"🔧 Consultando `{evento['herramienta']}`...")
                    estado.write(f"🔧 **Herramienta:** `{evento['herramienta']}`")
                    estado.write(f"**Input:** {evento['input']}")
                elif tipo == "fin":
                    estado.write(f"**Resultado de** `{evento['herramienta']}`:")
                    estado.json(evento["resultado"], expanded=False)
                    estado.divider()
                elif tipo == "error":
                    raise RuntimeError(evento["mensaje"])
                elif tipo == "final":
                    answer = evento["answer"]
                    trace = evento["trace"]

            estado.update(label="✅ Consulta completada", state="complete", expanded=False)
            st.markdown(answer)

            with st.expander("🔍 Trazabilidad y Criterios Consultados"):
                if trace:
                    for i, paso in enumerate(trace, start=1):
                        st.markdown(f"**{i}. 🔧 Herramienta:** `{paso['herramienta']}`")
                        st.caption(f"Input: {paso['input']}")
                        st.json(paso["resultado"], expanded=False)
                        if i < len(trace):
                            st.divider()
                else:
                    st.info("No se ejecutaron herramientas en este turno.")

            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            estado.update(label="❌ Error en la consulta", state="error")
            st.error(f"Error de sistema: {str(e)}")