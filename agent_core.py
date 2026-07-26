"""
Orquestador LangChain, Memoria y Extracción de Traza.
"""
import os
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()

SYSTEM_PROMPT = """Eres un Especialista en Diagnóstico Clínico.
Tu objetivo es estructurar análisis comparativos y apoyar en la elaboración de informes psicológicos detallados utilizando la CIE-11.

REGLAS DE ORQUESTACIÓN OBLIGATORIAS:
1. Usa las tools para obtener datos taxonómicos precisos.
2. Ante dudas en diagnósticos de casos, extrae definiciones, inclusiones y exclusiones de múltiples entidades para contrastar.
3. Mantén un rigor analítico alto, separando observaciones de entrevistas clínicas de las clasificaciones formales de la OMS.
4. Indica siempre qué evidencia y códigos MMS sustentan tu conclusión.
"""

async def _invoke_agent(prompt: str, session_id: str) -> dict:
    mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    servers_config = {"clinica_mcp": {"transport": "http", "url": mcp_url}}
    mcp_client = MultiServerMCPClient(servers_config)
    tools = await mcp_client.get_tools()
    
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    agent = create_react_agent(model=llm, tools=tools, state_modifier=SYSTEM_PROMPT, checkpointer=memory)
    
    config = {"configurable": {"thread_id": session_id}}
    result = await agent.ainvoke({"messages": [("user", prompt)]}, config=config)
    return result

def run_clinical_agent(prompt: str, session_id: str) -> dict:
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