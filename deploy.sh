#!/bin/bash

# 1. Cargar variables del .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: Archivo .env no encontrado."
    exit 1
fi

# Configuración
REGISTRY_NAME="cie11mcp2026"
APP_NAME="cie11-mcp-server"
RESOURCE_GROUP="CIE11-RG"
IMAGE_NAME="$REGISTRY_NAME.azurecr.io/mcp-server:latest"

echo "🚀 Iniciando despliegue de: $APP_NAME"

# 2. Build y Push al registro
echo "📦 Construyendo y subiendo imagen..."
az acr login --name $REGISTRY_NAME
docker build --platform linux/amd64 -t $IMAGE_NAME .
docker push $IMAGE_NAME

# 3. Crear/Actualizar la Container App
# Usamos --registry-server para que no pida credenciales manualmente
echo "☁️ Desplegando en Azure Container Apps..."
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment cie11-env \
  --image $IMAGE_NAME \
  --registry-server $REGISTRY_NAME.azurecr.io \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --output none 2>/dev/null || echo "ℹ️ La App ya existe, actualizando configuración..."

# 4. Inyectar secretos
echo "🔑 Actualizando secretos..."
az containerapp secret set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets "icd-client-id=$ICD_CLIENT_ID" "icd-client-secret=$ICD_CLIENT_SECRET" > /dev/null

# 5. Vincular variables a los secretos (Sintaxis corregida)
echo "⚙️ Configurando variables de entorno..."
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars "ICD_CLIENT_ID=secretref:icd-client-id" "ICD_CLIENT_SECRET=secretref:icd-client-secret"

# 6. Obtener y mostrar la URL final
FQDN=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
echo "✅ Despliegue completado."
echo "🔗 Tu endpoint MCP es: https://$FQDN/sse"