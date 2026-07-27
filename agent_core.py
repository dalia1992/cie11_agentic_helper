"""
Orquestador LangChain, Memoria y Extracción de Traza.
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

# Configuración de logging para diagnóstico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

memory = InMemorySaver()

SYSTEM_PROMPT = """Eres un Especialista en Diagnóstico Clínico utilizando la CIE-11.
Tu objetivo es ayudar en la evaluación y estructuración de diagnósticos diferenciales.
Apoyas en el análisis comparativo y extracción de códigos y criterios de la CIE-11.

REGLAS DE ORQUESTACIÓN OBLIGATORIAS:
1. Usa las tools para obtener datos taxonómicos precisos.
3. Si la herramienta provee una 'url_navegable', preséntala como "Enlace oficial al navegador de la OMS: [Abrir en el Browser](URL)". NO compartas la 'uri_api' (URL interna) con el usuario, ya que requiere autenticación.
4. Ante dudas en diagnósticos de casos, extrae definiciones, inclusiones y exclusiones de múltiples entidades para contrastar.
5. Mantén un rigor analítico alto, separando observaciones de entrevistas clínicas de las clasificaciones formales de la OMS.
6. Indica siempre qué evidencia y códigos MMS sustentan tu conclusión.
7. EVALUACIÓN DIFERENCIAL ACTIVA: Al recibir síntomas, no solo identifiques posibles códigos. DEBES sugerir activamente síntomas adicionales para:
   a) Confirmar criterios (ej. "¿Ha experimentado X síntoma adicional?").
   b) Realizar diagnóstico diferencial (ej. "Verificar ausencia de episodios maníacos/hipomaníacos para descartar trastorno bipolar" o "Confirmar si hay antecedentes de trauma para descartar TEPT").
   c) Indicar qué síntomas faltan para cumplir con el umbral diagnóstico de la entidad sospechada.
8. SIEMPRE incluye los códigos y url navegables de las enfermedades mencionadas"""

async def _invoke_agent(prompt: str, session_id: str) -> dict:
    mcp_url = os.getenv("AGENT_MCP_URL", "http://127.0.0.1:8000/sse")
    servers_config = {"clinica_mcp": {"transport": "sse", "url": mcp_url}}
    mcp_client = MultiServerMCPClient(servers_config)
    tools = await mcp_client.get_tools()
    
    # 2. Inicialización de LLM
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró OPENAI_API_KEY en el entorno.")
        
    llm = ChatOpenAI(
        api_key=api_key, 
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), 
        temperature=0
    )
    
    # 3. Creación y ejecución del agente
    agent = create_react_agent(
        model=llm, 
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory
    )
    
    config = {"configurable": {"thread_id": session_id}}
    try:
        result = await agent.ainvoke({"messages": [("user", prompt)]}, config=config)
        return result
    except Exception as e:
        logger.error(f"❌ Error durante la invocación del agente: {e}")
        raise e

def run_clinical_agent(prompt: str, session_id: str) -> dict:
    """Función síncrona para ser llamada desde Streamlit"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        raw_result = loop.run_until_complete(_invoke_agent(prompt, session_id))
        
        messages = raw_result.get("messages", [])
        answer = messages[-1].content if messages else "Error en la generación."
        
        trace = []
        for m in messages:
            if m.type == "tool":
                trace.append({"tool_name": m.name, "result": m.content})
            elif m.type == "ai" and hasattr(m, 'tool_calls') and m.tool_calls:
                for tc in m.tool_calls:
                    trace.append({"action": tc.get('name'), "args": tc.get('args')})
                    
        return {"answer": answer, "trace": trace}
    except Exception as e:
        return {"answer": f"Error del sistema: {str(e)}", "trace": []}