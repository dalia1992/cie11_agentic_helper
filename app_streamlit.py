"""
Interfaz Streamlit: UI, Gestión de Sesión y Evidencia.
"""
import streamlit as st
import uuid
from agent_core import run_clinical_agent

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
        with st.spinner("Ejecutando consulta a CIE-11..."):
            try:
                result = run_clinical_agent(prompt, st.session_state.session_id)
                st.markdown(result["answer"])
                
                with st.expander("Trazabilidad y Criterios Consultados"):
                    if result["trace"]:
                        st.json(result["trace"])
                    else:
                        st.info("No se ejecutaron herramientas en este turno.")
                
                st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
            except Exception as e:
                st.error(f"Error de sistema: {str(e)}")