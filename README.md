# 🩺 Sistema de Agentes Clínicos CIE-11

## 📌 Problema
Asistencia en la evaluación clínica y elaboración de informes psicológicos. El sistema resuelve la dificultad de navegar la taxonomía oficial de la OMS (CIE-11) manualmente, permitiendo diagnósticos diferenciales precisos y trazables para profesionales de la psicología.

## 🏗️ Arquitectura
El sistema emplea un patrón de arquitectura distribuida para garantizar el desacoplamiento entre la interfaz de usuario, la lógica de razonamiento y el acceso a datos taxonómicos:

1. **Frontend (Streamlit):** Actúa como el cliente principal que mantiene el estado de la sesión (`session_id`) y renderiza la interfaz conversacional.
2. **Orquestador (LangGraph):** Implementado en `agent_core.py`, maneja el flujo de razonamiento y la memoria persistente por sesión. Se comunica con el servidor MCP mediante el protocolo **SSE (Server-Sent Events)** para una comunicación asíncrona y robusta sobre HTTP.
3. **Servidor MCP (mcp_server.py):** Expone las herramientas clínicas como un servidor HTTP independiente, facilitando el despliegue escalable en servicios en la nube (Azure/Render) y garantizando que el acceso a la API de la OMS sea centralizado.

### Diagrama de Flujo
```text
[Streamlit App] --(HTTPS/SSE)--> [Agente LangGraph] --(Tools)--> [MCP Server] --(API)--> [OMS CIE-11]
``` 

## 🛠️ Matriz de Tools MCP
| Tool | Propósito | Entrada | Salida | Riesgo |
|---|---|---|---|---|
| `icd11_buscar_fundacion` | Búsqueda taxonómica general | Término (str) | Lista de URI/Títulos | Bajo |
| `icd11_buscar_sintomas` | Mapeo clínico de síntomas | Síntoma (str) | Manifestaciones/URI | Bajo |
| `icd11_buscar_codigo_mms` | Extracción de código MMS | Trastorno (str) | Código, Título, URL | Bajo |
| `icd11_obtener_criterios` | Análisis diferencial profundo | URI (str) | Definición, Inclusiones | Bajo |

## 🧠 Memoria
El sistema utiliza `InMemorySaver` de `langgraph` con un `session_id` único por usuario/conversación. La memoria permite referencias contextuales (ej. "dame sus criterios" tras buscar una entidad). 
*Limitación: Al ser en memoria, los datos se reinician al recargar el proceso.*

## Variables de Entorno

Inicializa el archivo de configuración a partir de la plantilla.

cp .env.example .env

Edita el archivo .env con tus credenciales:

OPENAI_API_KEY=tu_clave_de_openai  
OPENAI_MODEL=gpt-4o-mini  
ICD_CLIENT_ID=tu_client_id_de_la_oms  
ICD_CLIENT_SECRET=tu_client_secret_de_la_oms  
MCP_SERVER_URL=<http://127.0.0.1:8000/mcp>

## 🚀 Instalación Local
1. `python -m venv .venv`
2. `source .venv/bin/activate` (o `.venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. Crear `.env` basado en `.env.example` con tus credenciales.
5. Ejecutar servidor MCP: `python mcp_server.py`
6. Ejecutar UI: `streamlit run app_streamlit.py`

## 🧪 Pruebas
1. **Consulta directa:** "Dime el código MMS de la distimia".
2. **Referencia:** "¿Cuáles son sus criterios de exclusión?" (usa la memoria).
3. **Análisis diferencial:** "Diferencia TEPT de trastorno de adaptación con síntomas de ansiedad".

## 🔗 Enlaces
- **App:** [Enlace de Streamlit Community Cloud]
- **Repo:** [Tu URL de GitHub]