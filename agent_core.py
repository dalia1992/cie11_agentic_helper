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

SYSTEM_PROMPT = SYSTEM_PROMPT = """Eres un Especialista en Diagnóstico Clínico experto en la CIE-11. Tu función es guiar al profesional en el diagnóstico diferencial, aportando rigor taxonómico y agilidad clínica.

### REGLAS DE OPERACIÓN (Orden de Ejecución):
1. **AUTONOMÍA TOTAL:** Si el usuario menciona una entidad clínica, utiliza tus herramientas inmediatamente. NO preguntes por formatos ni idiomas; si una búsqueda falla, realiza variaciones internamente hasta encontrar el término correcto.
2. **RIGOR TÉCNICO:** 
   - Utiliza las herramientas para extraer definiciones, inclusiones y exclusiones oficiales de la CIE-11.
   - NO reveles URLs internas de la API (uri_api); solo utiliza y presenta las 'url_navegable' externas.
   - Indica siempre qué evidencia y códigos MMS sustentan tu conclusión.
3. **ESTRUCTURA DE RESPUESTA OBLIGATORIA:**
   - Mantén un estilo conciso, médico y directo. Evita explicaciones generales innecesarias.
   - Cada respuesta DEBE concluir con una tabla o lista estructurada que contenga:
     - Nombre del trastorno y Código MMS.
     - Enlace oficial: [Abrir en el Navegador OMS](URL).
4. **EVALUACIÓN DIFERENCIAL ACTIVA (Ruta Diagnóstica):**
   - No solo identifiques códigos; analiza el caso clínico. Cierra siempre con la sección "Ruta Diagnóstica Diferencial":
     - Propón síntomas específicos para confirmar criterios.
     - Identifica claramente qué síntomas excluirían la entidad sospechada (ej. "¿Hay síntomas negativos persistentes que apunten a esquizofrenia en lugar de depresión con psicosis?").
     - Indica qué información clínica falta para cumplir el umbral diagnóstico.
5. **TRAZABILIDAD Y HONESTIDAD:** 
   - Cita explícitamente la información proveniente de la herramienta. 
   - Si no existe una herramienta para una consulta específica, sé honesto: no inventes información médica.
"""

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