# MCP Tool Router Server

A high-performance Model Context Protocol (MCP) Tool Router that enables intelligent discovery and routing of tools across multiple MCP servers using both Azure and local search capabilities.

## Overview

The MCP Tool Router Server provides a centralized interface for discovering and accessing tools from multiple MCP servers. It supports both Azure-based cloud search using Azure AI Search and OpenAI embeddings, as well as local vector search using SQLite.

## Features

- **Intelligent Tool Discovery**: Uses semantic search to find the most relevant tools based on natural language queries
- **Dual Search Modes**: Supports both Azure-based cloud search and local vector search
- **High Performance**: Configurable concurrent request handling with async operations
- **Score Normalization**: Normalizes tool relevance scores across different search providers
- **Flexible Configuration**: Easy configuration through INI files
- **MCP Registry Integration**: Integrates with MCP registry for server discovery

## Architecture

### Core Components

- **[`run.py`](run.py)** - Main ToolRouter class and entry point
- **[`utils_core.py`](utils_core.py)** - Core data structures and base classes (Server, ToolResult, ToolListResult)
- **[`utils_azure_search.py`](utils_azure_search.py)** - Azure AI Search and OpenAI embedding integration
- **[`utils_local_search.py`](utils_local_search.py)** - Local SQLite vector search implementation

### Data Management

- **[`data/config.ini`](data/config.ini)** - Configuration file for Azure, local settings, and router parameters
- **[`data/mcp_servers.json`](data/mcp_servers.json)** - MCP server registry and metadata

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

### Local Search Configuration
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
USE_LOCAL_TOOLS = True
```

## Usage

### Basic Usage

```python
from src.server.run import ToolRouter

# Initialize the router
router = ToolRouter()

# Search for tools
results = await router.search_tools("file manipulation tools")

# Get tool results with normalized scores
tool_results = await router.get_tool_results(query="database operations", top_k=5)
```

### Search Modes

The router supports two search modes:

1. **Azure Search**: Uses Azure AI Search with OpenAI embeddings for cloud-based semantic search
2. **Local Search**: Uses SQLite with vector extensions for local semantic search

Configure the search mode using the `USE_LOCAL_TOOLS` setting in [`config.ini`](data/config.ini).

## Key Classes

### ToolRouter
Main router class that orchestrates tool discovery and search operations.

**Key Methods:**
- `search_tools(query: str, top_k: int)` - Search for relevant tools
- `normalize_NNB_scores(scores: list[float])` - Normalize scores to 0-100 range
- `get_tool_results(query: str, top_k: int)` - Get normalized tool results

### Server
Represents an MCP server with metadata.

**Properties:**
- `id: str` - Unique server identifier
- `name: str` - Human-readable server name
- `url: Optional[str]` - Server endpoint URL
- `location: Literal["remote", "local"]` - Server location type

### ToolResult
Represents a single tool result with scoring and metadata.

**Properties:**
- `score: float` - Relevance score
- `server: Server` - Associated server information
- `toolset: str` - Tool category/grouping
- `name: str` - Tool name
- `description: str` - Tool description

## Development

### Prerequisites

- Python 3.8+
- Azure account with AI Search and OpenAI services (for Azure mode)
- SQLite with vector extensions (for local mode)

### Dependencies

Key dependencies include:
- `azure-search-documents` - Azure Search integration
- `azure-identity` - Azure authentication
- `openai` - OpenAI API client
- `sqlite-vec` - SQLite vector extensions
- `mcp` - Model Context Protocol framework

## Authentication

### Azure Authentication
Uses `DefaultAzureCredential` for Azure service authentication. Ensure you're logged in via:
- Azure CLI (`az login`)
- Visual Studio Code Azure Account extension
- Managed Identity (when running in Azure)
- Environment variables

### GitHub Integration
For MCP registry operations, set the `GITHUB_TOKEN` environment variable with appropriate permissions.

## Performance Tuning

Configure performance parameters in [`config.ini`](data/config.ini):

- `MAX_CONCURRENT_REQUESTS` - Maximum concurrent search requests
- `TOOL_RESULT_CNT` - Number of results to return per search
- `TOOL_RETURN_LIMIT` - Maximum tools returned in a single query
- `USE_SEARCH_CACHE` - Enable search result caching (test mode)

## License

Copyright (c) Microsoft Corporation. Licensed under the MIT License.