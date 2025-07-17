# DocuChat Python API

A Python implementation of the DocuChat RAG (Retrieval-Augmented Generation) API, based on the Node.js version. This API enables document chat functionality with advanced RAG features including HyDE, MMR re-ranking, and deep search.

## Features

- Session-based configuration management
- SQLite database with vector search extensions for efficient similarity search
- Document processing with intelligent chunking
- Advanced RAG implementation:
  - HyDE (Hypothetical Document Embeddings)
  - Context-aware HyDE for deep search
  - MMR (Maximal Marginal Relevance) re-ranking
- FastAPI REST interface with SSE (Server-Sent Events) for streaming responses
- LangChain integration for document processing and embeddings generation

## Technology Stack

- **FastAPI**: For the REST API framework
- **SQLite** with **sqlite-vec**: For vector database functionality
- **LangChain**: For document loading, processing, and embeddings
- **Pydantic**: For data validation and configuration
- **OpenAI SDK**: For chat and embeddings API calls
- **Uvicorn**: ASGI server for hosting the API

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ducuchat-python.git
   cd ducuchat-python
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the API

Start the server:
```bash
python -m app.main
```

The API will be available at http://localhost:8000.

## API Usage

### Session Management

Sessions are used to manage configuration. You must create a session before using other API endpoints.

#### Create a Session

```bash
curl -X POST http://localhost:8000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "db_path": "./data.db",                       # Path to SQLite database file (required)
    "embedding_dimensions": 384,                  # Vector embedding dimensions (optional, detected from DB)
    
    "openai_api_key": "your-api-key",            # OpenAI API key for chat (required)
    "openai_base_url": "https://api.openai.com/v1", # OpenAI API base URL (default: https://api.openai.com/v1)
    "openai_model": "gpt-3.5-turbo",             # OpenAI model for chat (default: gpt-3.5-turbo)
    
    "rag_api_key": "your-embedding-api-key",     # API key for embeddings (optional, defaults to openai_api_key)
    "rag_base_url": "https://api.openai.com/v1", # Embeddings API base URL (default: https://api.openai.com/v1)
    "rag_model": "text-embedding-3-small",       # Embeddings model (default: text-embedding-3-small)
    
    "chunk_size": 1000,                          # Document chunk size (optional, auto-sized based on embedding dimensions)
    "chunk_overlap": 200,                        # Document chunk overlap (optional, defaults to 20% of chunk_size)
    
    "similarity_threshold": 0.5,                 # Minimum similarity score for retrieval (default: 0.5)
    "context_max_length": 4096,                  # Maximum context length for LLM (default: 4096)
    "deep_search_enabled": true,                 # Enable deep search with HyDE (default: true)
    "deep_search_initial_threshold": 0.3,        # Initial threshold for deep search (default: 0.3)
    
    "max_file_size": 10485760,                   # Maximum file size in bytes (default: 10MB)
    "upload_directory": "./uploads"              # Directory for uploaded files (default: ./uploads)
  }'
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### List Sessions

```bash
curl -X GET http://localhost:8000/api/session/list
```

#### Update Session

```bash
curl -X POST http://localhost:8000/api/session/update/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "db_path": "./data.db",
    "openai_api_key": "new-api-key",
    "openai_model": "gpt-4"
  }'
```

#### Delete Session

```bash
curl -X DELETE http://localhost:8000/api/session/expire/550e8400-e29b-41d4-a716-446655440000
```

### Using the API Endpoints

For all API endpoints except session creation and listing, include the session ID in the `X-Session-ID` header:

```bash
curl -X GET http://localhost:8000/api/documents \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000"
```

## Project Structure

```
ducuchat-python/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── session.py              # Session management
│   ├── api/                    # API endpoints
│   ├── db/                     # Database operations
│   ├── documents/              # Document processing
│   ├── embeddings/             # Embeddings generation
│   ├── rag/                    # RAG implementation
│   └── utils/                  # Utility functions
├── tests/                      # Test suite
└── requirements.txt            # Dependencies
```

## Development

### Adding New Endpoints

1. Create a new router module in the `app/api/` directory
2. Include your router in `app/api/router.py`
3. Implement your API logic

### Running Tests

```bash
pytest
```

## License

[MIT License](LICENSE) 