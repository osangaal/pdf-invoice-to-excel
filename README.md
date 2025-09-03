# 📄 PDF Invoice to Excel

Una aplicación web construida con Streamlit que convierte PDFs de facturas a archivos Excel usando inteligencia artificial.

## 🚀 Características

- **Conversión de PDFs**: Procesa archivos PDF individuales o en lote
- **Extracción Inteligente**: Usa LLMWhisperer para convertir PDFs a texto estructurado
- **Procesamiento con IA**: Utiliza OpenAI para extraer datos estructurados
- **Generación de Excel**: Crea archivos Excel organizados con múltiples hojas
- **Interfaz Web**: Aplicación fácil de usar con Streamlit

## 🛠️ Tecnologías

- **Frontend**: Streamlit
- **APIs**: LLMWhisperer, OpenAI
- **Procesamiento**: Python, Pandas, OpenPyXL
- **Deployment**: Streamlit Cloud

## 📋 Requisitos

- Python 3.8+
- API Key de LLMWhisperer
- API Key de OpenAI

## 🔧 Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <tu-repositorio>
   cd pdf-invoice-to-excel
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   ```bash
   # Crear archivo .env
   LLMWHISPERER_API_KEY=tu_api_key_aqui
   OPENAI_API_KEY=tu_api_key_aqui
   OPENAI_MODEL=gpt-4o-mini
   ```

4. **Ejecutar la aplicación**:
   ```bash
   streamlit run app.py
   ```

## 🚀 Deployment en Streamlit Cloud

1. **Subir a GitHub**: Asegúrate de que tu código esté en un repositorio de GitHub

2. **Configurar en Streamlit Cloud**:
   - Ve a [share.streamlit.io](https://share.streamlit.io)
   - Conecta tu repositorio de GitHub
   - Configura las variables de entorno:
     - `LLMWHISPERER_API_KEY`
     - `OPENAI_API_KEY`
     - `OPENAI_MODEL`

3. **Deploy**: La aplicación se desplegará automáticamente

## 📁 Estructura del Proyecto

```
pdf-invoice-to-excel/
├── src/
│   ├── clients/          # Clientes para APIs externas
│   │   ├── openai_client.py
│   │   └── llmwhisperer_client.py
│   ├── services/         # Servicios de procesamiento
│   │   └── pdf_processor.py
│   └── utils/           # Utilidades
│       └── secrets.py
├── config/              # Configuración
│   └── prompts.yaml
├── .streamlit/          # Configuración de Streamlit
│   └── config.toml
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias
└── README.md          # Documentación
```

## 🔑 Configuración de API Keys

### LLMWhisperer
1. Obtén tu API key de [LLMWhisperer](https://llmwhisperer.com)
2. Configúrala en las variables de entorno

### OpenAI
1. Obtén tu API key de [OpenAI](https://platform.openai.com)
2. Configúrala en las variables de entorno

## 📊 Uso

1. **Archivo Individual**: Sube un PDF de factura
2. **Múltiples Archivos**: Sube varios PDFs para procesamiento en lote
3. **Procesar**: Haz clic en "Procesar PDFs"
4. **Descargar**: Descarga el archivo Excel generado

## 🎯 Funcionalidades

### Extracción de Datos
- Información de la factura (número, fecha, vencimiento)
- Datos del emisor/vendedor
- Datos del cliente/comprador
- Lista de productos/servicios
- Totales y cálculos
- Información de pago

### Generación de Excel
- **Hoja Resumen**: Información general de todas las facturas
- **Hoja Productos**: Lista detallada de productos
- **Formato Organizado**: Datos estructurados y fáciles de analizar

## 🐛 Solución de Problemas

### Error de API Keys
- Verifica que las API keys estén configuradas correctamente
- Asegúrate de que tengan los permisos necesarios

### Error de Procesamiento
- Verifica que los PDFs sean legibles
- Asegúrate de que contengan texto (no solo imágenes)

### Error de Dependencias
- Ejecuta `pip install -r requirements.txt`
- Verifica la versión de Python (3.8+)

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la documentación
2. Busca en los issues existentes
3. Crea un nuevo issue si es necesario

---

Desarrollado con ❤️ usando Streamlit, LLMWhisperer y OpenAI
