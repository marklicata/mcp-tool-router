# MCP Tool Router Server

A high-performance Model Context Protocol (MCP) Tool Router that enables intelligent discovery and routing of tools across multiple MCP servers using Azure-based cloud search capabilities with planned local search support.

## Overview

The MCP Tool Router Server provides a centralized FastAPI-based interface for discovering and accessing tools from multiple MCP servers. It currently supports Azure-based cloud search using Azure AI Search and OpenAI embeddings, with local vector search capabilities planned for future implementation.

## Features

- **Intelligent Tool Discovery**: Uses semantic search to find the most relevant tools based on natural language queries
- **Azure Cloud Search**: Integrated Azure AI Search with OpenAI embeddings for semantic tool discovery
- **High Performance**: Configurable concurrent request handling with async operations
- **Score Normalization**: Advanced score normalization using rescaling algorithms
- **FastAPI REST API**: Modern REST API with automatic documentation and authentication
- **Flexible Configuration**: Easy configuration through INI files with multiple service sections
- **Tool Scoring & Filtering**: Configurable minimum score thresholds for result quality
- **Hybrid Search**: Combines semantic and keyword search for optimal results

## Architecture

### Core Components

- **[`run.py`](run.py)** - Main ToolRouter class, FastAPI application, and REST endpoints
- **[`utils_objects.py`](utils_objects.py)** - Core data structures (Server, Tool, ToolResults)
- **[`utils_azure_search.py`](utils_azure_search.py)** - Azure AI Search and OpenAI embedding integration

### Data Management

- **[`data/config.ini`](data/config.ini)** - Configuration file for Azure services, local settings, and router parameters
- **[`data/mcp_servers.json`](data/mcp_servers.json)** - MCP server registry and metadata
- **[`data/tool_manifest.json`](data/tool_manifest.json)** - Tool manifest and metadata
- **[`data/new_tests.json`](data/new_tests.json)** - Test cases and validation data

### Utility Scripts

- **[`json_utils/`](json_utils/)** - JSON utilities for server and test case management
  - [`create_servers.py`](json_utils/create_servers.py) - Server creation utilities
  - [`create_test_cases.py`](json_utils/create_test_cases.py) - Test case generation
  - [`update_servers.py`](json_utils/update_servers.py) - Server update utilities

## Configuration

The server is configured through [`data/config.ini`](data/config.ini) with the following sections:

### Azure AI Configuration
```ini
[AzureAI]
AZURE_FOUNDARY_ENDPOINT = https://your-endpoint.cognitiveservices.azure.com/
AZURE_EMBEDDING_MODEL = text-embedding-3-large
AZURE_EMBEDDING_DEPLOYMENT = text-embedding-3-large
AZURE_EMBEDDING_DIMENSIONS = 1536
AZURE_API_VERSION = 2024-02-01
```

### Azure Search Configuration
```ini
[AzureSearch]
AZURE_SEARCH_ENDPOINT = https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME = toolset-vector-index
```

### Local Search Configuration (Planned)
```ini
[LocalEmbeddings]
LOCAL_EMBEDDING_MODEL = text-embedding-3-large
LOCAL_EMBEDDING_DEPLOYMENT = text-embedding-3-large
LOCAL_EMBEDDING_DIMENSIONS = 1536
LOCAL_API_VERSION = 2024-02-01
```

### Router Settings
```ini
[ToolRouter]
MAX_CONCURRENT_REQUESTS = 15
USE_LOCAL_TOOLS = False
MINIMUM_TOOL_SCORE = 0.5
MINIMUM_RERANKER_SCORE = 1.1
```

## API Endpoints

### PUT /get_mcp_tools/
Search for tools based on a query string using the full routing pipeline.

**Request Body:**
```json
{
  "query": "file manipulation tools",
  "top_k": 10,
  "allowed_tools": ["tool1", "tool2"]
}
```

**Response:**
```json
{
  "execution_time": 0.234,
  "tools": [
    {
      "id": "server.tool_name",
      "server": "server_id",
      "toolset": "file_operations",
      "name": "file_reader",
      "description": "Read files from filesystem",
      "score": 0.95
    }
  ]
}
```

### PUT /run_az_search/
Direct Azure Search access without full routing pipeline.

**Request Body:**
```json
{
  "query": "database operations",
  "top_k": 10,
  "allowed_tools": []
}
```

### GET /get_router_status
Get the current status and configuration of the router.

**Response:**
```json
{
  "status": "active",
  "configuration": {
    "max_concurrent_requests": 15,
    "tool_result_count": 10,
    "tool_return_limit": 10,
    "use_local_tools": false,
    "use_search_cache": false
  },
  "services": {
    "azure_search": "initialized",
    "local_search": "not_initialized"
  },
  "timestamp": "2025-09-02T10:30:00"
}
```

## Usage

### Starting the Server

```bash
python run.py
```

The server will start on `http://0.0.0.0:8000` with automatic API documentation available at `/docs`.

### Programmatic Usage

```python
from run import ToolRouter

# Initialize the router
router = ToolRouter()

# Search for tools
results = await router.route("database operations")

# Access results
for tool in results.tools:
    print(f"Tool: {tool.name} (Score: {tool.score})")
```

## Key Classes

### ToolRouter
Main router class that orchestrates tool discovery and search operations.

**Key Methods:**
- `route(query: str, top_k: int, allowed_tools: List[str])` - Main routing method that returns ToolResults
- `get_remote_tools(query: str, allowed_tools: List[str])` - Get tools from Azure Search
- `get_local_tools(query: str)` - Placeholder for local tools (not yet implemented)
- `normalize_NNB_scores(scores: list[float])` - Normalize scores using rescaling

**Configuration Properties:**
- `max_concurrent_requests` - Maximum concurrent requests (default: 15)
- `tool_result_cnt` - Number of results per search (default: 10)
- `tool_return_limit` - Maximum tools returned (default: 10)
- `use_local_tools` - Enable local search (default: False)
- `minimum_tool_score` - Minimum relevance score (default: 0.5)
- `minimum_reranker_score` - Minimum reranker score (default: 1.1)

### AzureSearchManager
Manages Azure AI Search and OpenAI embedding operations.

**Key Methods:**
- `create_text_embedding(text: str)` - Create embeddings using Azure OpenAI
- `perform_azure_search(search_text: str, top_k: int, allowed_tools: List[str])` - Hybrid search execution
- `create_tools_from_file(file_path: str)` - Bulk tool creation from JSON
- `clear_azure_search_index()` - Clear all documents from index

### Server
Represents an MCP server with metadata and validation.

**Properties:**
- `id: uuid.UUID` - Unique server identifier (required)
- `name: str` - Human-readable server name (required)
- `description: Optional[str]` - Server description
- `url: str` - Server endpoint URL
- `version: Optional[str]` - Server version
- `release_date: Optional[str]` - Release date
- `is_latest: Optional[bool]` - Latest version flag

### Tool
Represents a single tool with scoring and vector embeddings.

**Properties:**
- `id: str` - Unique tool identifier
- `server: str` - Associated server ID
- `toolset: Optional[str]` - Tool category/grouping
- `name: str` - Tool name
- `description: str` - Tool description
- `tool_vector: List[float]` - Embedding vector
- `score: Optional[float]` - Relevance score

### ToolResults
Container for tool search results with performance metrics.

**Properties:**
- `execution_time: float` - Query execution time
- `tools: List[Tool]` - List of matching tools
- `kwargs: Dict[str, Any]` - Additional metadata

## Development

### Prerequisites

- Python 3.11+
- Azure account with AI Search and OpenAI services
- FastAPI and Uvicorn for web server

### Dependencies

Key dependencies (see [`requirements.txt`](requirements.txt)):
- `azure-search-documents>=11.4.0` - Azure Search integration
- `azure-identity>=1.15.0` - Azure authentication
- `openai>=1.12.0` - OpenAI API client
- `fastapi>=0.104.0` - Modern web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pydantic>=2.5.0` - Data validation
- `mcp>=1.0.0` - Model Context Protocol framework
- `sqlite-vec>=0.1.0` - Local vector search (planned)

### Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py

# Run tests
pytest

# Access API documentation
# Navigate to http://localhost:8000/docs
```

## Authentication

### Azure Authentication
Uses `DefaultAzureCredential` for Azure service authentication. Ensure you're logged in via:
- Azure CLI (`az login`)
- Visual Studio Code Azure Account extension
- Managed Identity (when running in Azure)
- Environment variables

### API Authentication
The API endpoints support Authorization header authentication:
```
Authorization: Bearer <token>
```

## Performance Tuning

Configure performance parameters in [`config.ini`](data/config.ini):

- `MAX_CONCURRENT_REQUESTS` - Maximum concurrent search requests (default: 15)
- `MINIMUM_TOOL_SCORE` - Minimum relevance score threshold (default: 0.5)
- `MINIMUM_RERANKER_SCORE` - Minimum reranker score threshold (default: 1.1)
- `USE_LOCAL_TOOLS` - Enable local search capabilities (default: false)

## Search Features

### Hybrid Search
The router uses Azure AI Search's hybrid search capabilities combining:
- **Semantic search** using vector embeddings
- **Keyword search** for exact matches
- **Reranking** for improved relevance

### Tool Filtering
- Server-based filtering for specific MCP servers
- Score-based filtering with configurable thresholds
- Allowed tools list for restricted searches

### Score Normalization
Advanced score normalization using rescaling algorithms to ensure consistent scoring across different search types and result sets.

## Future Enhancements

### Local Search Implementation
- Hybrid search combining local and remote results
- Offline tool discovery capabilities using `sqlite-vec`
- Performance optimizations for local vector operations

### Enhanced Features
- Tool result caching for improved performance
- Advanced scoring algorithms
- Multi-language embedding support
- Real-time tool synchronization
- Enhanced filtering and sorting options

## Docker Support

The server includes Docker support with [`Dockerfile`](Dockerfile) for containerized deployment.

```bash
# Build the Docker image
docker build -t mcp-tool-router .

# Run the container
docker run -p 8000:8000 mcp-tool-router
```

## JSON Utilities

The [`json_utils/`](json_utils/) directory contains helper scripts for managing MCP servers and test cases:

- **[`create_servers.py`](json_utils/create_servers.py)** - Create new server definitions
- **[`create_test_cases.py`](json_utils/create_test_cases.py)** - Generate test cases for validation
- **[`update_servers.py`](json_utils/update_servers.py)** - Update existing server configurations

## License

Copyright (c) Microsoft Corporation. Licensed under the MIT License.