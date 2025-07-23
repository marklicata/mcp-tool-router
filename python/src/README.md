# MCP Tool Router - Python Source

This directory contains the complete Python implementation of the MCP (Model Context Protocol) Tool Router, a high-performance system for intelligent tool discovery and routing across multiple MCP servers.

## Architecture Overview

The Python source is organized into two main components:

```
python/src/
├── server/          # Core MCP Tool Router Server
├── app/             # Testing and Demonstration Application
└── .gitignore       # Python-specific ignore patterns
```

## Components

### 🔧 [Server](server/) 
**Core MCP Tool Router Implementation**

The server component provides a FastAPI-based tool routing service with Azure-based cloud search capabilities and planned local vector search support.

**Key Features:**
- **FastAPI REST API**: Modern web API with automatic documentation and authentication
- **Intelligent Semantic Tool Discovery**: Uses Azure AI Search with OpenAI embeddings
- **High-Performance Async Operations**: Configurable concurrent request handling
- **Advanced Score Normalization**: Rescaling algorithms for consistent ranking
- **Tool Scoring & Filtering**: Configurable minimum score thresholds for result quality
- **MCP Registry Integration**: Connects with MCP registry for server discovery
- **Docker Support**: Containerized deployment ready

**Current Implementation:**
- Azure AI Search with OpenAI text-embedding-3-large
- FastAPI endpoints: `/get_mcp_tools/` and `/get_router_status`
- Score normalization and filtering capabilities
- Local search planned for future implementation

📖 **[Read the Server Documentation →](server/README.md)**

### 🧪 [App](app/)
**Testing and Evaluation Application**

The app component provides comprehensive automated testing and benchmarking capabilities for validating router performance and accuracy.

**Key Features:**
- **Automated Benchmark Testing**: Batch evaluation against predefined test cases
- **Multi-Metric Evaluation**: Precision, recall, and AI-judge scoring systems
- **Multi-Tier Match Analysis**: Top-1, Top-3, Top-5, Top-10 accuracy measurement
- **Performance Analytics**: Detailed timing and statistical reporting
- **Interactive Chat Mode**: Manual query testing interface
- **Azure OpenAI Integration**: AI-powered tool quality assessment
- **Configurable Test Management**: Flexible test case and evaluation parameters

**Current Implementation:**
- TestRunManager for automated testing orchestration
- AI judge evaluation using GPT-4
- Comprehensive statistical reporting
- HTTP client integration with server API

📖 **[Read the App Documentation →](app/README.md)**

## Quick Start

### Prerequisites

- Python 3.8+
- Azure account with AI Search and OpenAI services
- FastAPI and Uvicorn for web server
- SQLite with vector extensions (for future local mode)

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r server/requirements.txt
   ```

2. **Configure Settings**
   
   Update configuration files:
   - [`server/data/config.ini`](server/data/config.ini) - Server configuration
   - [`app/data/config.ini`](app/data/config.ini) - App configuration

3. **Azure Authentication**
   ```bash
   az login
   ```

### Running the System

#### Start the Server
```bash
# From python/src/server/
python run.py
```
Server will start on `http://localhost:8000` with API docs at `/docs`

#### Test with Interactive Mode
```python
# From python/src/app/
python run.py
# Edit run.py to uncomment run_chat() for interactive mode
```

#### Run Automated Benchmarks
```python
# From python/src/app/
python run.py
# Uses automated testing mode by default
```

## API Usage

### REST API Endpoints

**POST `/get_mcp_tools/`** - Search for tools
```json
{
  "query": "file manipulation tools"
}
```

**GET `/get_router_status`** - Get router status and configuration

### Programmatic Usage
```python
from server.run import ToolRouter

router = ToolRouter()
results = await router.route(query="database operations")
```

## Configuration

### Server Configuration
Located in [`server/data/config.ini`](server/data/config.ini):

```ini
[AzureAI]
AZURE_FOUNDARY_ENDPOINT = https://your-endpoint.cognitiveservices.azure.com/
AZURE_EMBEDDING_MODEL = text-embedding-3-large

[AzureSearch]
AZURE_SEARCH_ENDPOINT = https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME = toolset-vector-index

[ToolRouter]
MAX_CONCURRENT_REQUESTS = 15
TOOL_RESULT_CNT = 10
TOOL_RETURN_LIMIT = 10
USE_LOCAL_TOOLS = False
MINIMUM_TOOL_SCORE = 0.5
```

### App Configuration  
Located in [`app/data/config.ini`](app/data/config.ini):

```ini
[TestRun]
SAMPLE_SIZE = 25
TOOL_QUALITY_JUDGES = 7
USE_SEARCH_CACHE = False

[Registry]
ENDPOINT1 = https://data.mcp.azure.com/workspaces/default/apis
ENDPOINT2 = https://registry.mcp.azure.com/v0/servers
```

## Search Implementation

### 🌐 Azure Mode (Current Implementation)
- **Azure AI Search**: Managed semantic search service
- **OpenAI Embeddings**: text-embedding-3-large model (1536 dimensions)
- **Hybrid Search**: Combines text and vector search
- **Score Normalization**: Advanced rescaling algorithms for consistent ranking
- **Tool Filtering**: Configurable minimum score thresholds

### 🏠 Local Mode (Planned)
- **SQLite Vector Search**: Using sqlite-vec extensions
- **Local Embeddings**: Self-hosted embedding generation
- **Privacy-Focused**: No external service dependencies
- **Offline Capability**: Full functionality without internet connectivity

Configure the mode using `USE_LOCAL_TOOLS` in the server configuration.

## Key Data Structures

### Server Components
- **`ToolRouter`**: Main orchestrator class with routing and normalization
- **`Server`**: MCP server representation with validation
- **`Tool`**: Tool metadata with vector embeddings and scoring
- **`ToolResults`**: Result container with performance metrics
- **`VectorStoreManager`**: Extensible base for vector operations

### App Components
- **`TestRunManager`**: Test execution orchestrator
- **`TestResult`**: Individual test outcome storage
- **`TestCase`**: Test case definition structure
- **`RequestHandler`**: HTTP client for server communication

## Development Workflow

### 1. Server Development
Work on core routing logic and search implementations in [`server/`](server/):
- Modify [`run.py`](server/run.py) for main router logic
- Update [`utils_azure_search.py`](server/utils_azure_search.py) for search functionality
- Extend [`utils_objects.py`](server/utils_objects.py) for data structures

### 2. Testing & Validation
Use the [`app/`](app/) component to:
- Test new features with automated benchmarks
- Validate accuracy with multi-tier match analysis
- Monitor performance with detailed metrics
- Debug with interactive chat mode

### 3. Configuration Management
Maintain separate configurations for:
- **Development**: Local testing settings
- **Production**: Deployed environment settings  
- **Testing**: Benchmark-specific configurations

## Key Dependencies

### Server Dependencies
- **Azure Integration**: `azure-search-documents>=11.4.0`, `azure-identity>=1.15.0`
- **OpenAI**: `openai>=1.12.0`
- **Web Framework**: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`
- **Data Validation**: `pydantic>=2.5.0`
- **Future Local Search**: `sqlite-vec>=0.1.0`

### App Dependencies
- **HTTP Client**: `requests>=2.31.0`
- **Azure AI**: `azure-identity`, `openai` (for quality assessment)
- **Utilities**: `tabulate`, `asyncio`

## Performance Features

### Server Performance
- **Concurrent Requests**: Configurable via `MAX_CONCURRENT_REQUESTS` (default: 15)
- **Result Limits**: Tunable through `TOOL_RESULT_CNT` and `TOOL_RETURN_LIMIT`
- **Score Filtering**: `MINIMUM_TOOL_SCORE` threshold for quality control
- **Advanced Normalization**: Rescaling algorithms for consistent ranking

### App Performance
- **Concurrent Testing**: Parallel test case execution
- **Configurable Batches**: Adjustable `SAMPLE_SIZE` for testing needs
- **Comprehensive Metrics**: Multiple evaluation methodologies
- **AI Judge Evaluation**: Configurable number of quality assessors

## File Organization

```
python/src/
├── server/
│   ├── run.py                      # Main ToolRouter and FastAPI app
│   ├── utils_objects.py           # Core data structures  
│   ├── utils_azure_search.py      # Azure Search integration
│   ├── requirements.txt           # Server dependencies
│   ├── Dockerfile                 # Container configuration
│   ├── data/
│   │   ├── config.ini             # Server configuration
│   │   ├── mcp_servers.json       # Server registry
│   │   └── tool_manifest.json     # Tool metadata
│   └── json_utils/                # Server management utilities
├── app/
│   ├── run.py                     # Testing application entry point
│   ├── utils.py                   # Testing framework classes
│   └── data/
│       ├── config.ini             # App configuration
│       └── test_cases.json        # Test case database
└── .gitignore                     # Python ignore patterns
```

## Docker Deployment

The server includes full Docker support:

```bash
# Build the Docker image
cd python/src/server
docker build -t mcp-tool-router .

# Run the container
docker run -p 8000:8000 mcp-tool-router
```

## Authentication

### Azure Authentication
Uses `DefaultAzureCredential` supporting:
- Azure CLI (`az login`)
- Visual Studio Code Azure Account extension
- Managed Identity (when running in Azure)
- Environment variables

### API Authentication
REST endpoints support Authorization header:
```
Authorization: Bearer <token>
```

## Troubleshooting

### Common Issues

1. **Azure Authentication**: Ensure you're logged in via `az login`
2. **Missing Dependencies**: Install via `pip install -r server/requirements.txt`
3. **Configuration Errors**: Verify INI file settings and Azure endpoints
4. **Server Connection**: Ensure server is running on localhost:8000 for app testing

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Server Roadmap
- **Local Search Implementation**: SQLite-based vector search
- **Hybrid Search**: Combine local and remote results
- **Enhanced Caching**: Search result caching for improved performance
- **Multi-language Support**: Additional embedding models

### App Roadmap
- **Advanced Metrics**: Additional quality assessment methods
- **Real-time Monitoring**: Continuous performance tracking
- **Test Case Generation**: Automated test case creation
- **Integration Testing**: End-to-end workflow validation

## Next Steps

- 📖 **Explore Server Implementation**: [Server Documentation](server/README.md)
- 🧪 **Try Automated Testing**: [App Documentation](app/README.md)
- ⚙️ **Configure Your Environment**: Update configuration files
- 🚀 **Deploy to Production**: Follow Docker deployment guide

For detailed implementation information, refer to the component-specific documentation linked above.