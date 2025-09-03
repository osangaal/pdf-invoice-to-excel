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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from ..clients.openai_client import init_chat_model, chat_with_system_prompt
from ..clients.llmwhisperer_client import init_llmwhisperer_client, convert_pdf_to_text
from ..utils.secrets import validate_api_keys

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Procesador principal de PDFs a Excel."""
    
    def __init__(self, config_path: str = "config/prompts.yaml", max_workers: int = None):
        """
        Inicializa el procesador.
        
        Args:
            config_path: Ruta al archivo de configuración YAML
            max_workers: Número máximo de hilos para procesamiento paralelo (opcional)
        """
        self.config = self._load_config(config_path)
        self.llmwhisperer_client = None
        self.openai_client = None
        
        # Usar configuración del archivo YAML o valor por defecto
        parallel_config = self.config.get("parallel_processing", {})
        self.max_workers = max_workers or parallel_config.get("max_workers", 3)
        
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
        Procesa múltiples PDFs en paralelo para mayor velocidad.
        
        Args:
            pdf_paths: Lista de rutas a archivos PDF
            
        Returns:
            list: Lista de datos extraídos
        """
        total_pdfs = len(pdf_paths)
        results = []
        
        logger.info(f"🚀 Procesando {total_pdfs} PDFs en paralelo (max {self.max_workers} hilos)...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas al pool de hilos
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_path): pdf_path 
                for pdf_path in pdf_paths
            }
            
            # Procesar resultados conforme se completan
            completed = 0
            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                completed += 1
                
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        logger.info(f"✅ PDF {completed}/{total_pdfs} completado: {Path(pdf_path).name}")
                    else:
                        logger.warning(f"⚠️ PDF {completed}/{total_pdfs} falló: {Path(pdf_path).name}")
                except Exception as e:
                    logger.error(f"❌ Error procesando PDF {completed}/{total_pdfs} {Path(pdf_path).name}: {str(e)}")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"🎉 Procesamiento paralelo completado: {len(results)}/{total_pdfs} PDFs exitosos")
        logger.info(f"⏱️ Tiempo total: {processing_time:.2f} segundos ({processing_time/total_pdfs:.2f}s por PDF)")
        
        return results
    
    def process_multiple_pdfs_in_chunks(self, pdf_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Procesa múltiples PDFs en chunks para optimizar memoria.
        
        Args:
            pdf_paths: Lista de rutas a archivos PDF
            
        Returns:
            list: Lista de datos extraídos
        """
        total_pdfs = len(pdf_paths)
        chunk_size = self.config.get("parallel_processing", {}).get("chunk_size", 5)
        
        logger.info(f"📦 Procesando {total_pdfs} PDFs en chunks de {chunk_size}...")
        
        all_results = []
        total_chunks = (total_pdfs + chunk_size - 1) // chunk_size
        
        for i in range(0, total_pdfs, chunk_size):
            chunk = pdf_paths[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            
            logger.info(f"🔄 Procesando chunk {chunk_num}/{total_chunks} ({len(chunk)} PDFs)...")
            
            chunk_results = self.process_multiple_pdfs(chunk)
            all_results.extend(chunk_results)
            
            logger.info(f"✅ Chunk {chunk_num}/{total_chunks} completado: {len(chunk_results)}/{len(chunk)} exitosos")
        
        logger.info(f"🎉 Procesamiento por chunks completado: {len(all_results)}/{total_pdfs} PDFs exitosos")
        return all_results
    
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
                        # Usar la nueva estructura del prompt mejorado
                        datos_factura = data["extracted_data"].get("datos_factura", {})
                        totales = data["extracted_data"].get("totales", {})
                        resumen_tabular = data["extracted_data"].get("resumen_tabular", {})
                        
                        summary_data.append({
                            "Archivo": data["file_name"],
                            "Número de Factura": datos_factura.get("numero_factura") or resumen_tabular.get("numero_factura", "N/A"),
                            "Fecha": datos_factura.get("fecha_emision", "N/A"),
                            "Total": totales.get("gran_total") or resumen_tabular.get("gran_total", "N/A")
                        })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name="Resumen", index=False)
                
                # Hoja detallada con resumen tabular
                detailed_data = []
                for data in processed_data:
                    if "extracted_data" in data and isinstance(data["extracted_data"], dict):
                        resumen_tabular = data["extracted_data"].get("resumen_tabular", {})
                        if resumen_tabular:
                            detailed_data.append({
                                "Archivo": data["file_name"],
                                "Número de Factura": resumen_tabular.get("numero_factura", ""),
                                "NIS": resumen_tabular.get("nis", ""),
                                "Mes de la Factura": resumen_tabular.get("mes_factura", ""),
                                "Tarifa": resumen_tabular.get("tarifa", ""),
                                "Sector": resumen_tabular.get("sector", ""),
                                "Total del Mes": resumen_tabular.get("total_mes", 0),
                                "Gran Total": resumen_tabular.get("gran_total", 0),
                                "Consumo kWh": resumen_tabular.get("historico_consumo_kwh", 0),
                                "Cargo Fijo": resumen_tabular.get("cargo_fijo", 0),
                                "Energía": resumen_tabular.get("energia", 0),
                                "Interés por Mora": resumen_tabular.get("interes_por_mora", 0),
                                "Subsidio Ley 15": resumen_tabular.get("subsidio_ley_15_recargo", 0),
                                "Var. Combustible": resumen_tabular.get("var_combustible", 0),
                                "Var. Transmisión": resumen_tabular.get("var_transmision", 0),
                                "Var. Generación": resumen_tabular.get("var_generacion", 0)
                            })
                
                if detailed_data:
                    detailed_df = pd.DataFrame(detailed_data)
                    detailed_df.to_excel(writer, sheet_name="Detalle_Completo", index=False)
                
                # Hoja de conceptos de facturación
                concepts_data = []
                for data in processed_data:
                    if "extracted_data" in data and isinstance(data["extracted_data"], dict):
                        conceptos = data["extracted_data"].get("conceptos_facturacion", [])
                        for concepto in conceptos:
                            concepts_data.append({
                                "Archivo": data["file_name"],
                                "Concepto": concepto.get("concepto", "N/A"),
                                "Importe": concepto.get("importe", 0)
                            })
                
                if concepts_data:
                    concepts_df = pd.DataFrame(concepts_data)
                    concepts_df.to_excel(writer, sheet_name="Conceptos", index=False)
            
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
