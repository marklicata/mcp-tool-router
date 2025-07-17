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

The server component provides the main tool routing functionality with support for both Azure-based cloud search and local vector search capabilities.

**Key Features:**
- Intelligent semantic tool discovery
- Dual search modes (Azure AI Search + Local SQLite vectors)
- High-performance async operations
- Score normalization across providers
- MCP registry integration

📖 **[Read the Server Documentation →](server/README.md)**

### 🧪 [App](app/)
**Testing and Evaluation Application**

The app component provides comprehensive testing and benchmarking capabilities for validating router performance and accuracy.

**Key Features:**
- Interactive query testing
- Automated benchmark evaluation
- Multi-tier match analysis (Top-1, Top-3, Top-5, Top-10)
- Performance metrics and analytics
- Configurable test case management

📖 **[Read the App Documentation →](app/README.md)**

## Quick Start

### Prerequisites

- Python 3.8+
- Azure account with AI Search and OpenAI services (for cloud mode)
- SQLite with vector extensions (for local mode)

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Settings**
   
   Update configuration files:
   - [`server/data/config.ini`](server/data/config.ini) - Server configuration
   - [`app/data/config.ini`](app/data/config.ini) - App configuration

3. **Azure Authentication** (if using Azure mode)
   ```bash
   az login
   ```

### Running the System

#### Start the Server
```python
# From python/src/
from server.run import ToolRouter

router = ToolRouter()
results = await router.route(query="file manipulation tools")
```

#### Run Interactive Testing
```python
# From python/src/
from app.run import run_single_query
run_single_query()
```

#### Run Automated Benchmarks
```python
# From python/src/
import asyncio
from app.run import test_run
asyncio.run(test_run())
```

## Configuration

Both components share a common configuration approach using INI files:

### Server Configuration
Located in [`server/data/config.ini`](server/data/config.ini):
- Azure AI and Search endpoints
- Local embedding settings
- Router performance parameters
- MCP registry configuration

### App Configuration  
Located in [`app/data/config.ini`](app/data/config.ini):
- Test run parameters
- Sample sizes and caching options

## Search Modes

The system supports two operational modes:

### 🌐 Azure Mode (Default)
- Uses Azure AI Search with OpenAI embeddings
- Cloud-based semantic search
- Scalable and managed infrastructure
- Requires Azure subscription

### 🏠 Local Mode
- Uses SQLite with vector extensions
- Local semantic search capabilities
- No external dependencies
- Privacy-focused deployment

Configure the mode using `USE_LOCAL_TOOLS` in the server configuration.

## Development Workflow

### 1. Server Development
Work on core routing logic, search implementations, and MCP integrations in the [`server/`](server/) directory.

### 2. Testing & Validation
Use the [`app/`](app/) component to:
- Test new features interactively
- Run regression tests
- Evaluate performance improvements
- Validate accuracy with benchmark datasets

### 3. Configuration Management
Maintain configuration files for different environments:
- Development settings for local testing
- Production settings for deployed environments
- Test-specific configurations for benchmarking

## Key Dependencies

- **Azure Integration**: `azure-search-documents`, `azure-identity`, `openai`
- **Local Search**: `sqlite-vec`, `sqlite3`
- **MCP Framework**: `mcp`, `fastmcp`
- **Core Python**: `asyncio`, `configparser`, `logging`

## Performance Considerations

- **Concurrent Requests**: Configurable via `MAX_CONCURRENT_REQUESTS`
- **Result Limits**: Tunable through `TOOL_RESULT_CNT` and `TOOL_RETURN_LIMIT`
- **Caching**: Optional search result caching for improved response times
- **Score Normalization**: Ensures consistent ranking across search providers

## File Organization

```
python/src/
├── server/
│   ├── run.py                    # Main ToolRouter class
│   ├── utils_core.py            # Core data structures
│   ├── utils_azure_search.py    # Azure Search integration
│   ├── utils_local_search.py    # Local SQLite search
│   ├── data/                    # Configuration files
│   └── json_utils/              # Server management utilities
├── app/
│   ├── run.py                   # Testing application
│   └── data/                    # Test cases and configuration
└── .gitignore                   # Python ignore patterns
```

## Contributing

When contributing to this codebase:

1. **Server Changes**: Update the [`server/`](server/) component for core functionality
2. **Testing**: Validate changes using the [`app/`](app/) testing framework
3. **Documentation**: Update relevant README files
4. **Configuration**: Ensure new features are properly configurable

## Troubleshooting

### Common Issues

1. **Azure Authentication**: Ensure you're logged in via `az login`
2. **Missing Dependencies**: Install required packages via `pip install -r requirements.txt`
3. **Configuration Errors**: Verify INI file settings and paths
4. **Local Search Issues**: Ensure SQLite vector extensions are installed

### Debug Mode

Enable detailed logging by setting the logging level in your configuration:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- 📖 **Explore Server Implementation**: [Server Documentation](server/README.md)
- 🧪 **Try Interactive Testing**: [App Documentation](app/README.md)
- ⚙️ **Configure Your Environment**: Update configuration files
- 🚀 **Deploy to Production**: Follow deployment best practices

For detailed implementation information, refer to the component-specific documentation linked above.