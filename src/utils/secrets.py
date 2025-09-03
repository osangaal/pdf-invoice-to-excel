"""
Módulo para manejo seguro de secretos y API keys
===============================================

Este módulo maneja la carga de variables de entorno y API keys
de manera segura, con soporte para archivos .env
"""

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si dotenv no está instalado, continuar silenciosamente
    pass


def get_openai_api_key() -> Optional[str]:
    """
    Obtiene la API key de OpenAI desde variables de entorno.
    
    Prioridad:
    1. Variable de entorno OPENAI_API_KEY
    2. Archivo .env (si dotenv está disponible)
    
    Returns:
        str: API key de OpenAI o None si no está configurada
    """
    return os.getenv("OPENAI_API_KEY")


def get_llmwhisperer_api_key() -> Optional[str]:
    """
    Obtiene la API key de LLMWhisperer desde variables de entorno.
    
    Prioridad:
    1. Variable de entorno LLMWHISPERER_API_KEY
    2. Archivo .env (si dotenv está disponible)
    
    Returns:
        str: API key de LLMWhisperer o None si no está configurada
    """
    return os.getenv("LLMWHISPERER_API_KEY")


def get_openai_model() -> str:
    """
    Obtiene el modelo de OpenAI desde variables de entorno.
    
    Returns:
        str: Nombre del modelo (default: gpt-4o-mini)
    """
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def validate_api_keys() -> dict:
    """
    Valida que todas las API keys necesarias estén configuradas.
    
    Returns:
        dict: Estado de validación de cada API key
    """
    return {
        "openai_api_key": bool(get_openai_api_key()),
        "llmwhisperer_api_key": bool(get_llmwhisperer_api_key()),
        "openai_model": get_openai_model()
    }
