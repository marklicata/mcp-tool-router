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
- **MCP Registry Integration**: Integrates with MCP registry for server discovery
- **Tool Scoring & Filtering**: Configurable minimum score thresholds for result quality

## Architecture

### Core Components

- **[`run.py`](run.py)** - Main ToolRouter class, FastAPI application, and REST endpoints
- **[`utils_objects.py`](utils_objects.py)** - Core data structures (Server, Tool, ToolResults, VectorStoreManager)
- **[`utils_azure_search.py`](utils_azure_search.py)** - Azure AI Search and OpenAI embedding integration

### Data Management

- **[`data/config.ini`](data/config.ini)** - Configuration file for Azure services, local settings, and router parameters
- **[`data/mcp_servers.json`](data/mcp_servers.json)** - MCP server registry and metadata
- **[`data/tool_manifest.json`](data/tool_manifest.json)** - Tool manifest and metadata
- **[`data/new_tests.json`](data/new_tests.json)** - Test cases and validation data

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

### Azure Active Directory Configuration
```ini
[AzureAD]
AZURE_CLIENT_ID = your-client-id
AZURE_TENANT_ID = your-tenant-id
```

### Azure Search Configuration
```ini
[AzureSearch]
AZURE_SEARCH_ENDPOINT = https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME = toolset-vector-index
```

### MCP Registry Configuration
```ini
[MCPRegistry]
MCP_REGISTRY_ENDPOINT = https://data.mcp.azure.com/workspaces/default/apis
MCP_REGISTRY_ENDPOINT_2 = https://registry.mcp.azure.com/v0/servers
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
TOOL_RESULT_CNT = 10
TOOL_RETURN_LIMIT = 10
USE_LOCAL_TOOLS = False
MINIMUM_TOOL_SCORE = 0.5
```

## API Endpoints

### POST /get_mcp_tools/
Search for tools based on a query string.

**Request Body:**
```json
{
  "query": "file manipulation tools"
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
  "timestamp": "2025-07-23T10:30:00"
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
from utils_objects import ToolRouter

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
- `route(query: str)` - Main routing method that returns ToolResults
- `get_remote_tools(query: str)` - Get tools from Azure Search
- `get_local_tools(query: str)` - Placeholder for local tools (not yet implemented)
- `normalize_NNB_scores(scores: list[float])` - Normalize scores using rescaling

### Server
Represents an MCP server with metadata and validation.

**Properties:**
- `id: str` - Unique server identifier (required)
- `name: str` - Human-readable server name (required)
- `url: Optional[str]` - Server endpoint URL (auto-formatted)
- `location: Literal["remote", "local"]` - Server location type

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

### VectorStoreManager
Base manager class for vector store operations (extensible for local/remote).

**Features:**
- Support for both remote and local vector stores
- Methods for creating and updating tools
- Batch operations for server management

## Development

### Prerequisites

- Python 3.8+
- Azure account with AI Search and OpenAI services
- FastAPI and Uvicorn for web server

### Dependencies

Key dependencies include:
- `azure-search-documents` - Azure Search integration
- `azure-identity` - Azure authentication
- `openai` - OpenAI API client
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `mcp` - Model Context Protocol framework

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
- `TOOL_RESULT_CNT` - Number of results to return per search (default: 10)
- `TOOL_RETURN_LIMIT` - Maximum tools returned in a single query (default: 10)
- `MINIMUM_TOOL_SCORE` - Minimum relevance score threshold (default: 0.5)
- `USE_LOCAL_TOOLS` - Enable local search capabilities (default: false)

## Future Enhancements

### Local Search Implementation
- Hybrid search combining local and remote results
- Offline tool discovery capabilities

### Enhanced Features
- Tool result caching for improved performance
- Advanced scoring algorithms
- Multi-language embedding support
- Real-time tool synchronization

## Docker Support

The server includes Docker support with [`Dockerfile`](Dockerfile) for containerized deployment.

```bash
# Build the Docker image
docker build -t mcp-tool-router .

# Run the container
docker run -p 8000:8000 mcp-tool-router
```

## License

Copyright (c) Microsoft Corporation. Licensed under the MIT License.