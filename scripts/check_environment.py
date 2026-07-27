"""Comprobación rápida del entorno antes de levantar el agente CIE-11."""
from __future__ import annotations
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def mcp_alcanzable(url: str) -> bool:
    try:
        with requests.get(url, timeout=3, stream=True) as response:
            return response.status_code == 200
    except requests.RequestException:
        return False


mcp_url = os.getenv("AGENT_MCP_URL", "http://127.0.0.1:8000/sse")

print("OPENAI_API_KEY:", "OK" if os.getenv("OPENAI_API_KEY") else "FALTA")
print("Modelo:", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
print("ICD_CLIENT_ID:", "OK" if os.getenv("ICD_CLIENT_ID") else "FALTA")
print("ICD_CLIENT_SECRET:", "OK" if os.getenv("ICD_CLIENT_SECRET") else "FALTA")
print(f"Servidor MCP ({mcp_url}):", "ACTIVO" if mcp_alcanzable(mcp_url) else "INACTIVO")
