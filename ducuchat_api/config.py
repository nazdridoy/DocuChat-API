from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Union
import os


class SessionConfig(BaseModel):
    """Session configuration schema for DocuChat Python API"""
    # Database configuration
    embedding_dimensions: Optional[int] = None
    
    # OpenAI API configuration (for chat)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    openai_api_key: str
    
    # RAG API configuration (for embeddings)
    rag_base_url: str = "https://api.openai.com/v1"
    rag_model: str = "text-embedding-3-small"
    rag_api_key: Optional[str] = None
    
    # Document processing configuration
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    
    # RAG configuration
    similarity_threshold: float = 0.5
    context_max_length: int = 4096
    deep_search_enabled: bool = True
    deep_search_initial_threshold: float = 0.3
    
    # Document upload configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_directory: str = "./uploads"
    
    @field_validator("rag_api_key")
    def set_rag_api_key(cls, v, info):
        """Use openai_api_key if rag_api_key is not provided"""
        return v or info.data.get("openai_api_key")
    
    @field_validator("chunk_size", "chunk_overlap")
    def set_chunking_defaults(cls, v, info):
        """Set chunking defaults based on embedding dimensions"""
        if v is not None:
            return v
            
        dims = info.data.get("embedding_dimensions")
        if not dims:
            return None
            
        if info.field_name == "chunk_size":
            # Set chunk size based on embedding dimensions
            if dims >= 1024:
                return 1000
            elif dims >= 768:
                return 768
            elif dims >= 512:
                return 512
            else:
                return 384
        elif info.field_name == "chunk_overlap":
            # If chunk_size is set, calculate overlap as 20% of chunk size
            chunk_size = info.data.get("chunk_size")
            if chunk_size:
                return int(chunk_size * 0.2)
            return None


def validate_session_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate session configuration and return as dictionary"""
    # Ensure upload directory exists
    if "upload_directory" in config and not os.path.exists(config["upload_directory"]):
        os.makedirs(config["upload_directory"], exist_ok=True)
        
    # Convert to Pydantic model for validation
    config_model = SessionConfig(**config)
    
    # Return as dictionary
    return config_model.model_dump() 