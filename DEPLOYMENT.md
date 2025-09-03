# 🚀 Guía de Deployment

## Streamlit Cloud

### 1. Preparación del Repositorio

Asegúrate de que tu repositorio tenga:
- ✅ `app.py` en la raíz
- ✅ `requirements.txt` con todas las dependencias
- ✅ `.streamlit/config.toml` para configuración
- ✅ `.streamlit/secrets.toml.example` como ejemplo

### 2. Configuración en Streamlit Cloud

1. **Ve a [share.streamlit.io](https://share.streamlit.io)**
2. **Conecta tu repositorio de GitHub**
3. **Configura las variables de entorno**:

```bash
# Variables requeridas
LLMWHISPERER_API_KEY=tu_api_key_aqui
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-4o-mini
```

### 3. Configuración de Secrets (Opcional)

Si prefieres usar secrets de Streamlit:

1. **Crea `.streamlit/secrets.toml`** en tu repositorio local
2. **Configura las API keys**:

```toml
[api_keys]
openai_api_key = "tu_openai_api_key_aqui"
llmwhisperer_api_key = "tu_llmwhisperer_api_key_aqui"

[models]
default_model = "gpt-4o-mini"
temperature = 0.0
```

3. **Sube el archivo** (asegúrate de que esté en `.gitignore`)

### 4. Configuración de la Aplicación

- **Main file path**: `app.py`
- **Python version**: 3.11 (recomendado)
- **Branch**: `main` o `master`

### 5. Límites y Consideraciones

- **Tamaño máximo de archivo**: 200MB por archivo
- **Tiempo de procesamiento**: Hasta 5 minutos por sesión
- **Memoria**: Limitada a 1GB
- **CPU**: Limitada a 1 core

### 6. Optimizaciones para Producción

- **Procesamiento paralelo**: Configurado para 3 hilos simultáneos
- **Timeouts optimizados**: 60 segundos para LLMWhisperer
- **Chunk processing**: Para archivos > 5 PDFs
- **Logging**: Configurado para nivel INFO

## Variables de Entorno Requeridas

```bash
# LLMWhisperer
LLMWHISPERER_API_KEY=tu_api_key_aqui

# OpenAI
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-4o-mini
```

## Verificación Post-Deployment

1. **Verifica que la aplicación cargue** sin errores
2. **Prueba con un PDF pequeño** para verificar funcionalidad
3. **Revisa los logs** para identificar problemas
4. **Verifica las API keys** están configuradas correctamente

## Troubleshooting

### Error: "API key not configured"
- Verifica que las variables de entorno estén configuradas
- Asegúrate de que los nombres sean exactos (case-sensitive)

### Error: "Module not found"
- Verifica que `requirements.txt` tenga todas las dependencias
- Asegúrate de que las versiones sean compatibles

### Error: "Timeout"
- Reduce el número de archivos procesados simultáneamente
- Verifica la conexión a las APIs externas

### Error: "Memory limit exceeded"
- Reduce el `chunk_size` en la configuración
- Procesa menos archivos por lote
