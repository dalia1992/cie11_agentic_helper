"""
Servidor MCP Clínico Avanzado: Soporte Diagnóstico, Sintomatología y Códigos Oficiales CIE-11.
"""

import os
import requests
import urllib3
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

mcp = FastMCP("GestorDiagnosticoClinicoCIE11")

class ICDAuthManager:
    def __init__(self):
        self.token_endpoint = 'https://icdaccessmanagement.who.int/connect/token'
        self._access_token = None

    def get_token(self) -> str:
        client_id = os.getenv("ICD_CLIENT_ID")
        client_secret = os.getenv("ICD_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("❌ Credenciales ICD_CLIENT_ID o ICD_CLIENT_SECRET ausentes en el entorno.")
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'icdapi_access',
            'grant_type': 'client_credentials'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(self.token_endpoint, data=payload, headers=headers, verify=False)
        response.raise_for_status()
        self._access_token = response.json().get('access_token')
        return self._access_token

auth_manager = ICDAuthManager()

def _get_api_headers() -> dict:
    token = auth_manager.get_token()
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Accept-Language': 'es',
        'API-Version': 'v2'
    }

class TermQuery(BaseModel):
    termino: str = Field(description="Término clínico, enfermedad, síntoma o signo a consultar.")

@mcp.tool()
def icd11_buscar_fundacion(query: TermQuery) -> dict:
    """
    Propósito: Consultar el componente multidimensional de Fundación de la OMS para localizar conceptos taxonómicos generales.
    Input: termino (str) - Término clínico o patología a buscar.
    Output: resultados_fundacion (list of dict) con título, uri, capítulo y score.
    """
    url = "https://id.who.int/icd/entity/search"
    response = requests.get(url, headers=_get_api_headers(), params={'q': query.termino}, verify=False)
    response.raise_for_status()
    data = response.json()
    resultados = [{"titulo": e.get("title"), "uri": e.get("id"), "capitulo": e.get("chapter"), "score": e.get("score")} for e in data.get('destinationEntities', [])]
    return {"resultados_fundacion": resultados}

@mcp.tool()
def icd11_buscar_sintomas_y_signos(query: TermQuery) -> dict:
    """
    Propósito: Explorar manifestaciones clínicas inespecíficas, signos o síntomas aislados (ej. fatiga, irritabilidad) para diagnósticos diferenciales iniciales.
    Input: termino (str) - Manifestación clínica o síntoma específico a consultar.
    Output: resultados_sintomatologia (list of dict) con manifestacion, uri, capitulo y coincidencia.
    """
    url = "https://id.who.int/icd/entity/search"
    params = {'q': query.termino, 'includeKeywordResult': 'true'}
    response = requests.get(url, headers=_get_api_headers(), params=params, verify=False)
    response.raise_for_status()
    data = response.json()
    resultados = [{"manifestacion": e.get("title"), "uri": e.get("id"), "capitulo": e.get("chapter"), "coincidencia": e.get("score")} for e in data.get('destinationEntities', [])]
    return {"resultados_sintomatologia": resultados}

@mcp.tool()
def icd11_buscar_codigo_mms(query: TermQuery) -> dict:
    """
    Propósito: Consultar la linearización oficial MMS (Mortality and Morbidity Statistics) para extraer el código estadístico oficial y la URI de liberación.
    Input: termino (str) - Patología o diagnóstico formal a codificar.
    Output: resultados_mms (list of dict) con codigo_oficial, titulo, uri_linearizacion y capitulo.
    """
    url = "https://id.who.int/icd/release/11/2024-01/mms/search"
    response = requests.get(url, headers=_get_api_headers(), params={'q': query.termino}, verify=False)
    if response.status_code == 404:
        url_alt = "https://id.who.int/icd/release/11/mms/search"
        response = requests.get(url_alt, headers=_get_api_headers(), params={'q': query.termino}, verify=False)
    response.raise_for_status()
    data = response.json()
    resultados = [{"codigo_oficial": e.get("theCode"), "titulo": e.get("title"), "uri_linearizacion": e.get("id"), "capitulo": e.get("chapter")} for e in data.get('destinationEntities', [])]
    return {"resultados_mms": resultados}

class URIQuery(BaseModel):
    uri_entidad: str = Field(description="URI completa de la entidad (Foundation o MMS) obtenida en las búsquedas.")

@mcp.tool()
def icd11_obtener_criterios_clinicos(query: URIQuery) -> dict:
    """
    Propósito: Extraer metadatos profundos, definiciones formales, inclusiones y exclusiones para análisis diferencial.
    Input: uri_entidad (str) - URI completa de la entidad obtenida en búsquedas previas.
    Output: dict con uri, titulo, definicion, inclusiones y exclusiones.
    """
    target_url = query.uri_entidad.strip().replace("http://", "https://")
    response = requests.get(target_url, headers=_get_api_headers(), verify=False)
    response.raise_for_status()
    data = response.json()
    return {
        "uri": data.get("@id"),
        "titulo": data.get("title", {}).get("@value"),
        "definicion": data.get("definition", {}).get("@value", "Sin definición formal disponible."),
        "inclusiones": [i.get("label", {}).get("@value") for i in data.get("inclusion", [])],
        "exclusiones": [e.get("label", {}).get("@value") for e in data.get("exclusion", [])]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="127.0.0.1", port=8000)