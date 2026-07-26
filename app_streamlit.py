"""
Interfaz Streamlit: UI, Gestión de Sesión y Evidencia.
"""
import streamlit as st
import uuid
from agent_core import run_clinical_agent

st.set_page_config(page_title="Asistente Diagnóstico CIE-11", layout="wide")
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
        with st.spinner("Ejecutando mapeo taxonómico..."):
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