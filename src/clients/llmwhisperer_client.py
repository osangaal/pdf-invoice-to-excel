"""
Cliente LLMWhisperer para el proyecto PDF Invoice to Excel
========================================================

Uso recomendado:
from src.clients.llmwhisperer_client import (
    init_llmwhisperer_client,
    convert_pdf_to_text,
    test_llmwhisperer_connection,
)

client = init_llmwhisperer_client()
text = convert_pdf_to_text(client, "document.pdf")
"""

from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from unstract.llmwhisperer import LLMWhispererClientV2
    from unstract.llmwhisperer.client_v2 import LLMWhispererClientException
    LLMWHISPERER_AVAILABLE = True
except ImportError:
    LLMWHISPERER_AVAILABLE = False
    LLMWhispererClientV2 = None
    LLMWhispererClientException = Exception

from ..utils.secrets import get_llmwhisperer_api_key

logger = logging.getLogger(__name__)


def init_llmwhisperer_client(
    api_key: Optional[str] = None,
    base_url: str = "https://llmwhisperer-api.us-central.unstract.com/api/v2",
) -> Optional[LLMWhispererClientV2]:
    """
    Inicializa un cliente de LLMWhisperer.
    
    Args:
        api_key: API key opcional (si no se proporciona, se usa desde .env)
        base_url: URL base de la API
    
    Returns:
        LLMWhispererClientV2: Cliente inicializado o None si hay error
        
    Raises:
        ValueError: Si la API key no está configurada
    """
    if not LLMWHISPERER_AVAILABLE:
        logger.error(
            "❌ LLMWhisperer client no disponible. Instale: pip install unstract-llmwhisperer"
        )
        return None
    
    # Obtener API key
    resolved_api_key = api_key or get_llmwhisperer_api_key()
    if not resolved_api_key:
        raise ValueError(
            "LLMWhisperer API key no configurada. Defina LLMWHISPERER_API_KEY en entorno o en .env"
        )
    
    try:
        client = LLMWhispererClientV2(
            base_url=base_url.rstrip("/"),
            api_key=resolved_api_key
        )
        logger.info(f"✅ LLMWhisperer Client inicializado - Base URL: {base_url}")
        return client
    except Exception as e:
        logger.error(f"❌ Error inicializando LLMWhisperer client: {str(e)}")
        return None


def convert_pdf_to_text(
    client: LLMWhispererClientV2,
    pdf_path: Union[str, Path],
    mode: str = "table",
    output_mode: str = "layout_preserving",
    wait_timeout: int = 120,
) -> Optional[str]:
    """
    Convierte un PDF a texto estructurado usando LLMWhisperer.
    
    Args:
        client: Cliente inicializado de LLMWhisperer
        pdf_path: Ruta al archivo PDF
        mode: Modo de conversión ("table", "text", etc.)
        output_mode: Modo de salida ("layout_preserving", etc.)
        wait_timeout: Timeout en segundos
    
    Returns:
        str: Texto estructurado en formato ASCII art, o None si hay error
    """
    if not client:
        logger.error("❌ Cliente LLMWhisperer no disponible")
        return None
    
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"❌ Archivo PDF no encontrado: {pdf_path}")
            return None
        
        if not pdf_path.suffix.lower() == ".pdf":
            logger.error(f"❌ El archivo no es un PDF válido: {pdf_path}")
            return None
        
        logger.info(f"🔄 Iniciando conversión de PDF: {pdf_path.name}")
        
        # Usar el método whisper del cliente oficial
        result = client.whisper(
            file_path=str(pdf_path),
            wait_for_completion=True,
            wait_timeout=wait_timeout,
            mode=mode,
            output_mode=output_mode,
            mark_vertical_lines=True,
            mark_horizontal_lines=True,
        )
        
        if result and "extraction" in result and "result_text" in result["extraction"]:
            structured_text = result["extraction"]["result_text"]
            logger.info(f"✅ Conversión completada: {len(structured_text)} caracteres")
            return structured_text
        else:
            logger.error("❌ No se pudo obtener el texto estructurado")
            return None
            
    except LLMWhispererClientException as e:
        logger.error(f"❌ Error de LLMWhisperer: {e.message} (Status: {e.status_code})")
        return None
    except Exception as e:
        logger.error(f"❌ Error en conversión de PDF: {str(e)}")
        return None


def test_llmwhisperer_connection(
    client: Optional[LLMWhispererClientV2] = None,
) -> Dict[str, Any]:
    """
    Prueba la conexión con la API de LLMWhisperer.
    
    Args:
        client: Cliente opcional. Si no se proporciona, se inicializa uno nuevo.
    
    Returns:
        dict: Información del estado de la conexión
    """
    if client is None:
        try:
            client = init_llmwhisperer_client()
        except Exception as e:
            return {
                "connected": False,
                "api_key_valid": False,
                "service_status": "error",
                "error": f"Error inicializando cliente: {str(e)}",
            }
    
    if not client:
        return {
            "connected": False,
            "api_key_valid": False,
            "service_status": "unavailable",
            "error": "Cliente LLMWhisperer no disponible",
        }
    
    try:
        logger.info("🔍 Probando conexión con LLMWhisperer API...")
        
        # Probar obteniendo información de uso
        usage_info = client.get_usage_info()
        if usage_info:
            logger.info("✅ Conexión exitosa con LLMWhisperer")
            return {
                "connected": True,
                "api_key_valid": True,
                "service_status": "operational",
                "usage_info": usage_info,
            }
        else:
            logger.warning("⚠️ No se pudo obtener información de uso")
            return {
                "connected": False,
                "api_key_valid": False,
                "service_status": "unavailable",
                "error": "No se pudo obtener información de uso",
            }
            
    except LLMWhispererClientException as e:
        logger.error(f"❌ Error de LLMWhisperer: {e.message} (Status: {e.status_code})")
        return {
            "connected": False,
            "api_key_valid": False,
            "service_status": "error",
            "error": f"Error de API: {e.message} (Status: {e.status_code})",
        }
    except Exception as e:
        logger.error(f"❌ Error probando conexión: {str(e)}")
        return {
            "connected": False,
            "api_key_valid": False,
            "service_status": "error",
            "error": f"Error de conexión: {str(e)}",
        }
