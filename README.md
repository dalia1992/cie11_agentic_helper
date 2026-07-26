# 🩺 Sistema de Agentes Clínicos CIE-11 (LangChain + FastMCP)

## 📌 Descripción del Proyecto

Este repositorio contiene un sistema de inteligencia artificial basado en agentes diseñado para asistir en la evaluación clínica, diagnósticos diferenciales y la elaboración de informes psicológicos detallados. Utiliza el **Model Context Protocol (MCP)** para integrar dinámicamente un agente de lenguaje (LLM) con la API oficial de la Clasificación Internacional de Enfermedades (CIE-11) de la OMS.

El sistema garantiza rigor analítico al separar las capacidades de razonamiento conversacional de las fuentes de verdad taxonómica.

## 🏗️ Arquitectura del Sistema

El proyecto sigue un patrón de diseño modular que separa la interfaz, el orquestador y los datos:

- **Interfaz de Usuario (app_streamlit.py):** Frontend ligero que maneja el estado de la sesión visual (session_id) y renderiza la trazabilidad de la evidencia.
- **Núcleo del Agente (agent_core.py):** Orquestador implementado con langgraph.prebuilt.create_react_agent. Maneja la memoria a corto plazo mediante InMemorySaver (vinculada al hilo de la sesión) y abstrae el bucle de razonamiento.
- **Servidor MCP de Dominio (mcp_server.py):** Servidor FastMCP autónomo que expone herramientas estandarizadas para consultar la API v2 de la OMS, eliminando dependencias de bases de datos locales.

## 🛠️ Matriz de Herramientas (Tools)

El servidor MCP expone las siguientes herramientas clínicas con contratos validados:

| **Herramienta**         | **Propósito**                                       | **Entrada**       | **Salida**               |
| ----------------------- | --------------------------------------------------- | ----------------- | ------------------------ |
| icd11_buscar_fundacion  | Búsqueda taxonómica general en la OMS.              | termino (str)     | Lista de URI y títulos.  |
| ---                     | ---                                                 | ---               | ---                      |
| icd11_buscar_sintomas   | Mapeo de manifestaciones inespecíficas.             | termino (str)     | Manifestaciones y URI.   |
| ---                     | ---                                                 | ---               | ---                      |
| icd11_buscar_codigo_mms | Extracción de códigos estadísticos de morbilidad.   | termino (str)     | Código MMS oficial, URI. |
| ---                     | ---                                                 | ---               | ---                      |
| icd11_obtener_criterios | Extracción de inclusiones/exclusiones diagnósticas. | uri_entidad (str) | Definición y criterios.  |
| ---                     | ---                                                 | ---               | ---                      |

## 🚀 Requisitos Previos y Configuración

### 1\. Variables de Entorno

Clona el repositorio e inicializa el archivo de configuración a partir de la plantilla.

cp .env.example .env

Edita el archivo .env con tus credenciales:

OPENAI_API_KEY=tu_clave_de_openai  
OPENAI_MODEL=gpt-4o-mini  
ICD_CLIENT_ID=tu_client_id_de_la_oms  
ICD_CLIENT_SECRET=tu_client_secret_de_la_oms  
MCP_SERVER_URL=<http://127.0.0.1:8000/mcp>

### 2\. Instalación de Dependencias

Se recomienda utilizar un entorno virtual (venv o conda). Ejecuta:

pip install -r requirements.txt

_(Asegúrate de que dependencias como langchain, langgraph, streamlit y mcp estén actualizadas según el archivo)._

## 💻 Ejecución Local

Para garantizar la correcta comunicación entre los componentes, el sistema requiere levantar dos procesos independientes.

**Paso 1: Iniciar el Servidor MCP (Backend de Datos)**

Abre una terminal y ejecuta el servidor que expone las herramientas de la OMS:

python mcp_server.py

_(El servidor se ejecutará por defecto en <http://127.0.0.1:8000>)_

**Paso 2: Iniciar la Interfaz Streamlit (Frontend y Agente)**

Abre una segunda terminal, asegurándote de estar en el mismo entorno virtual, y ejecuta:

streamlit run app_streamlit.py

## 🧪 Casos de Prueba (Validación Funcional)

Para verificar la correcta integración y trazabilidad de las herramientas, ingresa los siguientes prompts en la interfaz:

- **Mapeo Sintomatológico:** _"Tengo un caso con estado de ánimo deprimido y anhedonia persistente. Busca estos síntomas y sugiere entidades taxonómicas relacionadas."_
- **Extracción de Códigos MMS:** _"Necesito el código estadístico oficial (MMS) para el Trastorno de Ansiedad Generalizada."_
- **Análisis Diferencial Profundo:** _"Obtén los criterios clínicos, inclusiones y exclusiones del Trastorno de Estrés Postraumático y compáralo taxonómicamente con el Trastorno de Adaptación."_