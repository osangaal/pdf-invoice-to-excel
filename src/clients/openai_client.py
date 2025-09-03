"""
Cliente OpenAI para el proyecto PDF Invoice to Excel
==================================================

Uso recomendado:
from src.clients.openai_client import (
    init_chat_model,
    chat_with_system_prompt,
    init_embedding_model,
)

llm = init_chat_model(model_name="gpt-4o-mini", temperature=0.1)
content = chat_with_system_prompt(llm, "You are helpful", "Hola")
"""

from typing import Optional
import logging

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import SystemMessage, HumanMessage
from ..utils.secrets import get_openai_api_key, get_openai_model

logger = logging.getLogger(__name__)


def init_chat_model(
    model_name: Optional[str] = None,
    temperature: Optional[float] = 0.1,
) -> ChatOpenAI:
    """
    Inicializa un modelo de chat de OpenAI.
    
    Args:
        model_name: Nombre del modelo (default: desde .env)
        temperature: Temperatura para la generación (default: 0.1)
    
    Returns:
        ChatOpenAI: Cliente de chat inicializado
        
    Raises:
        ValueError: Si la API key no está configurada
    """
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        raise ValueError(
            "OpenAI API key no configurada. Defina OPENAI_API_KEY en entorno o en .env"
        )
    
    # Usar modelo desde .env si no se especifica
    if model_name is None:
        model_name = get_openai_model()
    
    # Modelos de razonamiento no usan temperatura
    reasoning_models = {"o4-mini", "o1-mini"}
    if model_name in reasoning_models:
        return ChatOpenAI(model=model_name, api_key=openai_api_key)
    
    # Modelos estándar con temperatura
    return ChatOpenAI(
        model=model_name,
        api_key=openai_api_key,
        temperature=0.0 if temperature is None else float(temperature),
    )


def chat_with_system_prompt(
    llm: ChatOpenAI,
    system_prompt: str,
    user_prompt: str,
    complete_response: bool = False,
):
    """
    Interacciona con el modelo usando un system prompt.
    
    Args:
        llm: Cliente de chat inicializado
        system_prompt: Prompt del sistema
        user_prompt: Prompt del usuario
        complete_response: Si devolver respuesta completa o solo contenido
    
    Returns:
        str o objeto Response: Contenido de la respuesta
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    response = llm.invoke(messages)
    return response if complete_response else response.content


def init_embedding_model(
    model_name: str = "text-embedding-3-small",
) -> OpenAIEmbeddings:
    """
    Inicializa el modelo de embeddings de OpenAI.
    
    Args:
        model_name: Nombre del modelo de embeddings
    
    Returns:
        OpenAIEmbeddings: Cliente de embeddings inicializado
        
    Raises:
        ValueError: Si la API key no está configurada
    """
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        raise ValueError(
            "OpenAI API key no configurada. Defina OPENAI_API_KEY en entorno o en .env"
        )
    
    return OpenAIEmbeddings(model=model_name, api_key=openai_api_key)


def extract_data_to_excel(
    structured_text: str,
    extraction_prompt: str,
    model_name: Optional[str] = None
) -> str:
    """
    Extrae datos estructurados del texto y los convierte a formato Excel.
    
    Args:
        structured_text: Texto estructurado del PDF
        extraction_prompt: Prompt para la extracción
        model_name: Modelo a usar (default: desde .env)
    
    Returns:
        str: Datos extraídos en formato tabular
    """
    try:
        llm = init_chat_model(model_name=model_name, temperature=0.0)
        result = chat_with_system_prompt(
            llm=llm,
            system_prompt=extraction_prompt,
            user_prompt=structured_text
        )
        logger.info("✅ Extracción de datos completada")
        return result
    except Exception as e:
        logger.error(f"❌ Error en extracción de datos: {str(e)}")
        raise
