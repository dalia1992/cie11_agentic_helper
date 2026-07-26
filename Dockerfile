# Usa una imagen de Python ligera y segura
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y almacene en caché
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define el directorio de trabajo
WORKDIR /app

# Instala solo las dependencias necesarias
# Asegúrate de que requirements.txt contenga lo mínimo para el servidor (fastmcp, requests, etc)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia estrictamente lo necesario para el servidor MCP
COPY mcp_server.py .

# Expone el puerto que usará el servidor (usualmente 8000 en el protocolo SSE)
EXPOSE 8000

# Ejecuta el servidor
# IMPORTANTE: Asegúrate de que en mcp_server.py el host sea "0.0.0.0"
CMD ["python", "mcp_server.py"]