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
- **High-Performance Async Operations**: Configurable concurrent request handling (default: 15)
- **Advanced Score Normalization**: Rescaling algorithms for consistent ranking
- **Tool Scoring & Filtering**: Configurable minimum score thresholds for result quality
- **Hybrid Search**: Combines semantic and keyword search for optimal results
- **Flexible Configuration**: Easy configuration through INI files with multiple service sections
- **Docker Support**: Containerized deployment ready

**Current Implementation:**
- Azure AI Search with OpenAI text-embedding-3-large (1536 dimensions)
- FastAPI endpoints: `/get_mcp_tools/`, `/run_az_search/`, and `/get_router_status`
- Score normalization and filtering capabilities
- Tool reranking with configurable thresholds
- Local search planned for future implementation

📖 **[Read the Server Documentation →](server/README.md)**

### 🧪 [App](app/)
**Testing and Evaluation Application**

The app component provides comprehensive automated testing and benchmarking capabilities for validating router performance and accuracy with advanced machine learning metrics.

**Key Features:**
- **Automated Benchmark Testing**: Batch evaluation against predefined test case collections
- **Advanced Metrics Evaluation**: Precision@K, Recall@K, nDCG, Average Precision, and semantic analysis
- **Performance Analytics**: Detailed timing measurements with percentile analysis (TP50, TP75, TP90, TP95)
- **Match Tier Analysis**: Multi-tier matching evaluation (Top-1, Top-3, Top-5, Top-10)
- **Comparison Testing**: Side-by-side evaluation of selection-enabled vs selection-disabled modes
- **Statistical Reporting**: Comprehensive test run summaries with success rates and missed tool analysis
- **Interactive Chat Mode**: Simple query interface for manual testing
- **Azure OpenAI Integration**: Semantic similarity analysis using text embeddings for redundancy and confusion index metrics

**Current Implementation:**
- TestRunManager for automated testing orchestration
- Advanced ML metrics (precision, recall, nDCG, average precision)
- Semantic analysis using Azure OpenAI embeddings
- Comprehensive statistical reporting with percentile analysis
- HTTP client integration with server API

📖 **[Read the App Documentation →](app/README.md)**

## Quick Start

### Prerequisites

- Python 3.11+
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
Server will start on `http://0.0.0.0:8000` with API docs at `/docs`

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

**PUT `/get_mcp_tools/`** - Search for tools using full routing pipeline
```json
{
  "query": "file manipulation tools",
  "top_k": 10,
  "allowed_tools": ["tool1", "tool2"]
}
```

**PUT `/run_az_search/`** - Direct Azure Search access
```json
{
  "query": "database operations",
  "top_k": 10,
  "allowed_tools": []
}
```

**GET `/get_router_status`** - Get router status and configuration

### Programmatic Usage
```python
from server.run import ToolRouter

router = ToolRouter()
results = await router.route(query="database operations", top_k=10)
```

## Configuration

### Server Configuration
Located in [`server/data/config.ini`](server/data/config.ini):

```ini
[AzureAI]
AZURE_FOUNDARY_ENDPOINT = https://your-endpoint.cognitiveservices.azure.com/
AZURE_EMBEDDING_MODEL = text-embedding-3-large
AZURE_EMBEDDING_DEPLOYMENT = text-embedding-3-large
AZURE_EMBEDDING_DIMENSIONS = 1536

[AzureSearch]
AZURE_SEARCH_ENDPOINT = https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX_NAME = toolset-vector-index

[ToolRouter]
MAX_CONCURRENT_REQUESTS = 15
USE_LOCAL_TOOLS = False
MINIMUM_TOOL_SCORE = 0.5
MINIMUM_RERANKER_SCORE = 1.1
```

### App Configuration  
Located in [`app/data/config.ini`](app/data/config.ini):

```ini
[TestRun]
SAMPLE_SIZE = 50
TEST_CASE_FILE = python/src/app/data/test_cases_complex_50.json
RUN_SIMPLE_SEARCH_COMPARISON = True
TOOLS_TO_RETURN = 10
MAX_TOOLS_TO_RETURN = 100
```

## Search Implementation

### 🌐 Azure Mode (Current Implementation)
- **Azure AI Search**: Managed semantic search service with hybrid search capabilities
- **OpenAI Embeddings**: text-embedding-3-large model (1536 dimensions)
- **Hybrid Search**: Combines semantic vector search and keyword search
- **Advanced Reranking**: Configurable reranker score thresholds
- **Score Normalization**: Advanced rescaling algorithms for consistent ranking
- **Tool Filtering**: Configurable minimum score thresholds and allowed tools filtering

### 🏠 Local Mode (Planned)
- **SQLite Vector Search**: Using sqlite-vec extensions
- **Local Embeddings**: Self-hosted embedding generation
- **Privacy-Focused**: No external service dependencies
- **Offline Capability**: Full functionality without internet connectivity

Configure the mode using `USE_LOCAL_TOOLS` in the server configuration.

## Key Data Structures

### Server Components
- **`ToolRouter`**: Main orchestrator class with routing, normalization, and concurrent request handling
- **`AzureSearchManager`**: Azure AI Search and OpenAI embedding integration
- **`Server`**: MCP server representation with validation and metadata
- **`Tool`**: Tool metadata with vector embeddings and scoring
- **`ToolResults`**: Result container with performance metrics and execution time

### App Components
- **`TestRunManager`**: Test execution orchestrator with advanced metrics calculation
- **`MetricsCalculator`**: Advanced metrics computation including Azure OpenAI integration
- **`TestResult`**: Individual test outcome storage with comprehensive metrics
- **`TestCase`**: Test case definition structure
- **`RequestHandler`**: HTTP client for server communication
- **`MetricsResult`**: Data structure for storing calculated metrics (precision, recall, nDCG, etc.)

## Development Workflow

### 1. Server Development
Work on core routing logic and search implementations in [`server/`](server/):
- Modify [`run.py`](server/run.py) for main router logic and FastAPI endpoints
- Update [`utils_azure_search.py`](server/utils_azure_search.py) for search functionality
- Extend [`utils_objects.py`](server/utils_objects.py) for data structures

### 2. Testing & Validation
Use the [`app/`](app/) component to:
- Test new features with automated benchmarks
- Validate accuracy with advanced ML metrics (precision, recall, nDCG)
- Monitor performance with detailed timing and percentile analysis
- Debug with interactive chat mode
- Compare selection-enabled vs selection-disabled modes

### 3. Configuration Management
Maintain separate configurations for:
- **Development**: Local testing settings
- **Production**: Deployed environment settings  
- **Testing**: Benchmark-specific configurations

## Advanced Evaluation Metrics

### Machine Learning Metrics
- **Precision@K**: Proportion of relevant tools in top-K results
- **Recall@K**: Proportion of relevant tools successfully retrieved
- **Average Precision**: Ranking-sensitive metric rewarding earlier placement
- **nDCG@K**: Normalized Discounted Cumulative Gain with position-based discounting

### Semantic Analysis Metrics
- **Redundancy Score**: Semantic similarity between selected tools using Azure OpenAI embeddings
- **Confusion Index**: Cognitive load estimation combining list length and redundancy
- **Tool Overlap Analysis**: Identification of functionally similar tools

### Performance Metrics
- **Response Time Percentiles**: TP50, TP75, TP90, TP95 analysis
- **Success/Failure Rates**: Query processing statistics
- **Missing Tool Analysis**: Detailed breakdown of commonly missed tools

## Key Dependencies

### Server Dependencies
- **Azure Integration**: `azure-search-documents>=11.4.0`, `azure-identity>=1.15.0`
- **OpenAI**: `openai>=1.12.0`
- **Web Framework**: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`
- **Data Validation**: `pydantic>=2.5.0`
- **MCP Framework**: `mcp>=1.0.0`
- **Future Local Search**: `sqlite-vec>=0.1.0`

### App Dependencies
- **HTTP Client**: `requests>=2.31.0`
- **Azure AI**: `azure-identity`, `openai` (for semantic analysis)
- **ML Libraries**: `scikit-learn`, `numpy`
- **Utilities**: `tabulate`, `asyncio`

## Performance Features

### Server Performance
- **Concurrent Requests**: Configurable via `MAX_CONCURRENT_REQUESTS` (default: 15)
- **Advanced Filtering**: `MINIMUM_TOOL_SCORE` and `MINIMUM_RERANKER_SCORE` thresholds
- **Hybrid Search**: Combines semantic and keyword search for optimal results
- **Score Normalization**: Rescaling algorithms for consistent ranking
- **Tool Reranking**: Advanced reranking with configurable thresholds

### App Performance
- **Concurrent Testing**: Parallel test case execution with asyncio
- **Configurable Batches**: Adjustable `SAMPLE_SIZE` for testing needs
- **Advanced Metrics**: Multiple ML evaluation methodologies
- **Semantic Analysis**: Azure OpenAI integration for redundancy assessment
- **Statistical Analysis**: Comprehensive percentile and distribution reporting

## Test Case Collections

### Available Test Case Files
- **`test_cases_simple_20_SWE.json`** - 20 simple software engineering test cases
- **`test_cases_simple_100_M365.json`** - 100 simple Microsoft 365 test cases
- **`test_cases_simple_600.json`** - 600 simple test cases across domains
- **`test_cases_complex_50.json`** - 50 complex test scenarios
- **`test_cases_complex_175.json`** - 175 complex test scenarios

### Test Case Structure
```json
{
    "question": "Find the machine learning org in GitHub",
    "expected_tools": [
        "GitHub.SearchOrgs"
    ]
}
```

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
│   │   ├── tool_manifest.json     # Tool metadata
│   │   └── new_tests.json         # Test cases and validation data
│   └── json_utils/                # Server management utilities
│       ├── create_servers.py      # Server creation utilities
│       ├── create_test_cases.py   # Test case generation
│       └── update_servers.py      # Server update utilities
├── app/
│   ├── run.py                     # Testing application entry point
│   ├── utils_test_manager.py      # Core testing framework
│   ├── utils_request_manager.py   # HTTP client for server communication
│   ├── utils_metrics.py           # Advanced metrics calculation
│   └── data/
│       ├── config.ini             # App configuration
│       ├── test_cases_simple_*.json    # Simple test case collections
│       ├── test_cases_complex_*.json   # Complex test case collections
│       └── test_results.json      # Test results storage
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
- **Local Search Implementation**: SQLite-based vector search with sqlite-vec
- **Hybrid Local/Remote Search**: Combine local and remote results
- **Enhanced Caching**: Search result caching for improved performance
- **Multi-language Support**: Additional embedding models
- **Real-time Tool Synchronization**: Dynamic tool updates

### App Roadmap
- **Advanced Metrics**: Additional quality assessment methods
- **Real-time Monitoring**: Continuous performance tracking
- **Test Case Generation**: Automated test case creation
- **Integration Testing**: End-to-end workflow validation
- **Visualization**: Interactive dashboards for metrics analysis

## Next Steps

- 📖 **Explore Server Implementation**: [Server Documentation](server/README.md)
- 🧪 **Try Advanced Testing**: [App Documentation](app/README.md)
- ⚙️ **Configure Your Environment**: Update configuration files
- 🚀 **Deploy to Production**: Follow Docker deployment guide

For detailed implementation information, refer to the component-specific documentation