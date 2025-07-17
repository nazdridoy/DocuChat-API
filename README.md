# DocuChat API

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
   git clone https://github.com/nazdridoy/ducuchat-api.git
   cd ducuchat-api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the API

You can now run the API using the CLI entry point:

```bash
uv run ducuchat-api --host 0.0.0.0 --port 8080
```

Or, if you have your virtual environment activated, you can run directly:

```bash
source .venv/bin/activate
ducuchat-api --host 0.0.0.0 --port 8080
```

Or see all available options:

```bash
uv run ducuchat-api --help
```

#### CLI Options

```
usage: ducuchat-api [-h] [--host HOST] [--port PORT] [--reload] [--log-level LOG_LEVEL]

Run the DocuChat API server.

options:
  -h, --help            show this help message and exit
  --host HOST           Host to bind the server to
  --port PORT           Port to bind the server to
  --reload              Enable auto-reload
  --log-level LOG_LEVEL Uvicorn log level
```

The API will be available at the host and port you specify (default: http://0.0.0.0:8000).

## API Usage

### Session Management

Sessions are used to manage configuration. You must create a session before using other API endpoints.

#### Create a Session

```bash
curl -X POST http://localhost:8000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{
    "db_path": "./data.db",
    "openai_base_url": "https://api.openai.com/v1",
    "openai_api_key": "sk-OPENAI-API-KEY-1234567890",
    "openai_model": "gpt-3.5-turbo",
    "rag_model": "text-embedding-3-small"
  }'
```

Response:
```json
{
  "session_id": "cafd852c-830d-4e35-9dc3-cc31e61f75c9",
  "vector_search": true
}
```

#### View Session Config (Public Endpoint)

You can view the full configuration for any session (no authentication required):

```bash
curl --location 'http://localhost:8000/api/session/config/cafd852c-830d-4e35-9dc3-cc31e61f75c9'
```

Example response:
```json
{
  "db_path": "/home/youruser/ducuchat-api/data.db",
  "embedding_dimensions": 384,
  "openai_base_url": "https://api.openai.com/v1",
  "openai_model": "gpt-3.5-turbo",
  "openai_api_key": "sk-OPENAI-API-KEY-1234567890",
  "rag_base_url": "https://api.openai.com/v1",
  "rag_model": "text-embedding-3-small",
  "rag_api_key": null,
  "chunk_size": null,
  "chunk_overlap": null,
  "similarity_threshold": 0.5,
  "context_max_length": 4096,
  "deep_search_enabled": true,
  "deep_search_initial_threshold": 0.3,
  "max_file_size": 10485760,
  "upload_directory": "./uploads"
}
```

#### List Sessions

```bash
curl -X GET http://localhost:8000/api/session/list
```

#### Update Session

```bash
curl -X POST http://localhost:8000/api/session/update/cafd852c-830d-4e35-9dc3-cc31e61f75c9 \
  -H "Content-Type: application/json" \
  -d '{
    "db_path": "./data.db",
    "openai_api_key": "sk-NEW-API-KEY-0987654321",
    "openai_model": "gemini-2.5-pro"
  }'
```

#### Delete Session

```bash
curl -X DELETE http://localhost:8000/api/session/expire/cafd852c-830d-4e35-9dc3-cc31e61f75c9
```

### Using the API Endpoints

For all API endpoints except session creation and listing, include the session ID in the `X-Session-ID` header:

```bash
curl -X GET http://localhost:8000/api/documents \
  -H "X-Session-ID: cafd852c-830d-4e35-9dc3-cc31e61f75c9"
```

## Project Structure

```
ducuchat-api/
├── ducuchat_api/
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

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.