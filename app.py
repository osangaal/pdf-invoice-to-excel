"""
Aplicación principal de Streamlit para PDF Invoice to Excel
=========================================================

Esta aplicación permite:
1. Cargar un PDF individual
2. Seleccionar una carpeta con múltiples PDFs
3. Procesar los PDFs usando LLMWhisperer y OpenAI
4. Generar archivos Excel con los datos extraídos
"""

import streamlit as st
import logging
from pathlib import Path
from typing import List
import tempfile
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
from src.services.pdf_processor import PDFProcessor
from src.utils.secrets import validate_api_keys

# Configuración de la página
st.set_page_config(
    page_title="PDF Invoice to Excel",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Función principal de la aplicación."""
    
    # Header principal
    st.markdown('<h1 class="main-header">📄 PDF Invoice to Excel</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Verificar API keys
        api_status = validate_api_keys()
        
        if api_status["openai_api_key"] and api_status["llmwhisperer_api_key"]:
            st.success("✅ API Keys configuradas")
        else:
            st.error("❌ API Keys no configuradas")
            st.info("Configura las variables de entorno:")
            st.code("""
OPENAI_API_KEY=tu_api_key
LLMWHISPERER_API_KEY=tu_api_key
            """)
            return
        
        st.markdown("---")
        
        # Opciones de procesamiento
        st.header("🔧 Opciones")
        show_debug = st.checkbox("Mostrar información de debug", value=False)
    
    # Contenido principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Seleccionar Archivos")
        
        # Opción 1: Archivo individual
        st.subheader("📄 Archivo Individual")
        uploaded_file = st.file_uploader(
            "Selecciona un archivo PDF",
            type=['pdf'],
            help="Sube un archivo PDF de factura para procesar"
        )
        
        st.markdown("---")
        
        # Opción 2: Carpeta con múltiples PDFs
        st.subheader("📁 Carpeta con Múltiples PDFs")
        st.info("💡 Para procesar múltiples PDFs, sube todos los archivos a la vez")
        
        uploaded_files = st.file_uploader(
            "Selecciona múltiples archivos PDF",
            type=['pdf'],
            accept_multiple_files=True,
            help="Selecciona múltiples archivos PDF para procesar en lote"
        )
    
    with col2:
        st.header("📊 Estado del Sistema")
        
        # Inicializar procesador
        try:
            processor = PDFProcessor()
            status = processor.get_processing_status()
            
            if status["llmwhisperer_available"]:
                st.success("✅ LLMWhisperer disponible")
            else:
                st.error("❌ LLMWhisperer no disponible")
            
            if status["openai_available"]:
                st.success("✅ OpenAI disponible")
            else:
                st.error("❌ OpenAI no disponible")
            
            if status["config_loaded"]:
                st.success("✅ Configuración cargada")
            else:
                st.error("❌ Error en configuración")
                
        except Exception as e:
            st.error(f"❌ Error inicializando procesador: {str(e)}")
            return
    
    # Procesamiento
    if uploaded_file or uploaded_files:
        st.markdown("---")
        st.header("🔄 Procesamiento")
        
        # Botón de procesamiento
        if st.button("🚀 Procesar PDFs", type="primary"):
            
            # Preparar archivos para procesamiento
            files_to_process = []
            
            if uploaded_file:
                files_to_process.append(uploaded_file)
            
            if uploaded_files:
                files_to_process.extend(uploaded_files)
            
            if not files_to_process:
                st.error("❌ No hay archivos para procesar")
                return
            
            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Guardar archivos temporalmente
                saved_files = []
                for file in files_to_process:
                    file_path = temp_path / file.name
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    saved_files.append(file_path)
                
                # Procesar archivos
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    processor = PDFProcessor()
                    
                    # Procesar archivos con optimización
                    total_files = len(saved_files)
                    
                    if total_files == 1:
                        # Un solo archivo - procesamiento normal
                        status_text.text(f"Procesando {saved_files[0].name}...")
                        progress_bar.progress(0.5)
                        
                        result = processor.process_single_pdf(saved_files[0])
                        results = [result] if result else []
                        
                        progress_bar.progress(1.0)
                    else:
                        # Múltiples archivos - procesamiento paralelo optimizado
                        status_text.text(f"🚀 Procesando {total_files} PDFs en paralelo...")
                        progress_bar.progress(0.1)
                        
                        if total_files <= 5:
                            # Pocos archivos - procesamiento paralelo directo
                            results = processor.process_multiple_pdfs(saved_files)
                        else:
                            # Muchos archivos - procesamiento por chunks
                            results = processor.process_multiple_pdfs_in_chunks(saved_files)
                        
                        progress_bar.progress(1.0)
                    
                    if results:
                        # Crear archivo Excel
                        output_path = temp_path / "facturas_procesadas.xlsx"
                        success = processor.create_excel_file(results, str(output_path))
                        
                        if success:
                            # Mostrar resultados
                            st.success(f"✅ Procesamiento completado: {len(results)}/{total_files} archivos")
                            
                            # Mostrar resumen
                            st.subheader("📋 Resumen de Procesamiento")
                            for result in results:
                                st.write(f"✅ {result['file_name']}")
                            
                            # Descargar archivo Excel
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="📥 Descargar Archivo Excel",
                                    data=f.read(),
                                    file_name="facturas_procesadas.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            
                            # Mostrar información de debug si está habilitada
                            if show_debug:
                                st.subheader("🔍 Información de Debug")
                                for result in results:
                                    with st.expander(f"Debug: {result['file_name']}"):
                                        st.json(result['extracted_data'])
                        else:
                            st.error("❌ Error creando archivo Excel")
                    else:
                        st.error("❌ No se pudieron procesar los archivos")
                        
                except Exception as e:
                    st.error(f"❌ Error durante el procesamiento: {str(e)}")
                    logger.error(f"Error en procesamiento: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📄 PDF Invoice to Excel - Desarrollado con Streamlit</p>
        <p>Usando LLMWhisperer y OpenAI para conversión inteligente de documentos</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
