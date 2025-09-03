"""
Servicio principal para procesamiento de PDFs
============================================

Este módulo orquesta todo el proceso de conversión de PDFs a Excel:
1. Conversión de PDF a texto estructurado (LLMWhisperer)
2. Extracción de datos (OpenAI)
3. Generación de archivos Excel
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import yaml

from ..clients.openai_client import init_chat_model, chat_with_system_prompt
from ..clients.llmwhisperer_client import init_llmwhisperer_client, convert_pdf_to_text
from ..utils.secrets import validate_api_keys

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Procesador principal de PDFs a Excel."""
    
    def __init__(self, config_path: str = "config/prompts.yaml"):
        """
        Inicializa el procesador.
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config = self._load_config(config_path)
        self.llmwhisperer_client = None
        self.openai_client = None
        self._initialize_clients()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carga la configuración desde archivo YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            logger.info("✅ Configuración cargada exitosamente")
            return config
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {str(e)}")
            raise
    
    def _initialize_clients(self):
        """Inicializa los clientes de las APIs."""
        # Validar API keys
        api_status = validate_api_keys()
        if not api_status["openai_api_key"]:
            raise ValueError("OpenAI API key no configurada")
        if not api_status["llmwhisperer_api_key"]:
            raise ValueError("LLMWhisperer API key no configurada")
        
        # Inicializar clientes
        try:
            self.llmwhisperer_client = init_llmwhisperer_client()
            self.openai_client = init_chat_model(
                model_name=self.config.get("models", {}).get("default_model"),
                temperature=self.config.get("models", {}).get("temperature", 0.0)
            )
            logger.info("✅ Clientes inicializados exitosamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando clientes: {str(e)}")
            raise
    
    def process_single_pdf(self, pdf_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Procesa un PDF individual.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            dict: Datos extraídos o None si hay error
        """
        try:
            pdf_path = Path(pdf_path)
            logger.info(f"🔄 Procesando PDF: {pdf_path.name}")
            
            # Paso 1: Convertir PDF a texto estructurado
            structured_text = convert_pdf_to_text(
                client=self.llmwhisperer_client,
                pdf_path=pdf_path,
                mode=self.config.get("llmwhisperer", {}).get("mode", "table"),
                output_mode=self.config.get("llmwhisperer", {}).get("output_mode", "layout_preserving"),
                wait_timeout=self.config.get("llmwhisperer", {}).get("wait_timeout", 120)
            )
            
            if not structured_text:
                logger.error(f"❌ No se pudo convertir el PDF: {pdf_path.name}")
                return None
            
            # Paso 2: Extraer datos con OpenAI
            extraction_prompt = self.config.get("invoice_extraction_prompt", "")
            extracted_data = self._extract_data_with_openai(structured_text, extraction_prompt)
            
            if not extracted_data:
                logger.error(f"❌ No se pudieron extraer datos del PDF: {pdf_path.name}")
                return None
            
            logger.info(f"✅ PDF procesado exitosamente: {pdf_path.name}")
            return {
                "file_name": pdf_path.name,
                "structured_text": structured_text,
                "extracted_data": extracted_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF {pdf_path}: {str(e)}")
            return None
    
    def process_multiple_pdfs(self, pdf_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Procesa múltiples PDFs.
        
        Args:
            pdf_paths: Lista de rutas a archivos PDF
            
        Returns:
            list: Lista de datos extraídos
        """
        results = []
        total_pdfs = len(pdf_paths)
        
        logger.info(f"🔄 Procesando {total_pdfs} PDFs...")
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"📄 Procesando PDF {i}/{total_pdfs}: {Path(pdf_path).name}")
            result = self.process_single_pdf(pdf_path)
            if result:
                results.append(result)
        
        logger.info(f"✅ Procesamiento completado: {len(results)}/{total_pdfs} PDFs exitosos")
        return results
    
    def _extract_data_with_openai(self, structured_text: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Extrae datos usando OpenAI.
        
        Args:
            structured_text: Texto estructurado del PDF
            prompt: Prompt para la extracción
            
        Returns:
            dict: Datos extraídos o None si hay error
        """
        try:
            response = chat_with_system_prompt(
                llm=self.openai_client,
                system_prompt=prompt,
                user_prompt=structured_text
            )
            
            # Intentar parsear como JSON
            try:
                extracted_data = json.loads(response)
                return extracted_data
            except json.JSONDecodeError:
                # Si no es JSON válido, devolver como texto
                logger.warning("⚠️ Respuesta no es JSON válido, devolviendo como texto")
                return {"raw_text": response}
                
        except Exception as e:
            logger.error(f"❌ Error en extracción con OpenAI: {str(e)}")
            return None
    
    def create_excel_file(self, processed_data: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Crea archivo Excel con los datos procesados.
        
        Args:
            processed_data: Lista de datos procesados
            output_path: Ruta del archivo Excel de salida
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Hoja de resumen
                summary_data = []
                for data in processed_data:
                    if "extracted_data" in data and isinstance(data["extracted_data"], dict):
                        invoice_info = data["extracted_data"].get("invoice_info", {})
                        summary_data.append({
                            "Archivo": data["file_name"],
                            "Número de Factura": invoice_info.get("invoice_number", "N/A"),
                            "Fecha": invoice_info.get("date", "N/A"),
                            "Total": invoice_info.get("total", "N/A")
                        })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name="Resumen", index=False)
                
                # Hoja de productos
                products_data = []
                for data in processed_data:
                    if "extracted_data" in data and isinstance(data["extracted_data"], dict):
                        products = data["extracted_data"].get("products", [])
                        for product in products:
                            products_data.append({
                                "Archivo": data["file_name"],
                                "Descripción": product.get("description", "N/A"),
                                "Cantidad": product.get("quantity", "N/A"),
                                "Precio Unitario": product.get("unit_price", "N/A"),
                                "Total": product.get("total", "N/A")
                            })
                
                if products_data:
                    products_df = pd.DataFrame(products_data)
                    products_df.to_excel(writer, sheet_name="Productos", index=False)
            
            logger.info(f"✅ Archivo Excel creado: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando archivo Excel: {str(e)}")
            return False
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del procesador.
        
        Returns:
            dict: Estado del procesador
        """
        return {
            "llmwhisperer_available": self.llmwhisperer_client is not None,
            "openai_available": self.openai_client is not None,
            "config_loaded": bool(self.config),
            "api_keys_valid": validate_api_keys()
        }
