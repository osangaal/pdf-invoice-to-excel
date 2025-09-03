"""
Clientes para APIs externas
==========================

Módulos para interactuar con OpenAI y LLMWhisperer APIs.
"""

from .openai_client import (
    init_chat_model,
    chat_with_system_prompt,
    init_embedding_model,
    extract_data_to_excel
)

from .llmwhisperer_client import (
    init_llmwhisperer_client,
    convert_pdf_to_text,
    test_llmwhisperer_connection
)

__all__ = [
    # OpenAI
    "init_chat_model",
    "chat_with_system_prompt", 
    "init_embedding_model",
    "extract_data_to_excel",
    
    # LLMWhisperer
    "init_llmwhisperer_client",
    "convert_pdf_to_text",
    "test_llmwhisperer_connection"
]
