# MCP Tool Router Application

A testing and demonstration application for the MCP Tool Router Server that provides both interactive query testing and automated benchmark evaluation capabilities.

## Overview

The MCP Tool Router Application serves as a client interface for testing and evaluating the performance of the MCP Tool Router Server. It supports two primary modes of operation:

1. **Interactive Mode**: Manual query testing with real-time results
2. **Automated Testing Mode**: Batch testing with comprehensive performance metrics

## Features

- **Interactive Query Testing**: Real-time tool discovery with performance metrics
- **Automated Benchmark Testing**: Batch evaluation against predefined test cases
- **Performance Analytics**: Detailed timing and accuracy measurements
- **Match Analysis**: Multi-tier matching evaluation (Top-1, Top-3, Top-5, Top-10)
- **Statistical Reporting**: Comprehensive test run summaries with success rates
- **Configurable Testing**: Customizable sample sizes and test parameters

## Architecture

### Core Components

- **[`run.py`](run.py)** - Main application with interactive and automated testing modes
- **[`data/config.ini`](data/config.ini)** - Application configuration settings
- **[`data/test_cases.json`](data/test_cases.json)** - Comprehensive test case database
- **[`data/test_output.json`](data/test_output.json)** - Test results output file

## Configuration

Configure the application through [`data/config.ini`](data/config.ini):

```ini
[TestRun]
SAMPLE_SIZE = 50              # Number of test cases to run in batch mode
USE_SEARCH_CACHE = False      # Enable/disable search result caching
```

## Usage

### Interactive Mode

Run individual queries with real-time feedback:

```python
# Uncomment in run.py main section
run_single_query()
```

**Features:**
- Enter natural language queries
- View matching tools with scores
- See execution time per query
- Continue with new queries or exit

**Example Session:**
```
Type your query: "file manipulation tools"

Server: FileSystem, Tool: readFile, Score: 95.32
Server: FileSystem, Tool: writeFile, Score: 92.18
Server: FileSystem, Tool: deleteFile, Score: 89.45
Execution time: 245.67 ms

Type a new query or press Enter to exit...
```

### Automated Testing Mode

Run comprehensive benchmarks against test case database:

```python
# Default mode in run.py
asyncio.run(test_run())
```

**Features:**
- Batch processing of test cases
- Multi-tier match evaluation
- Performance metrics collection
- Statistical analysis and reporting

## Test Case Structure

Test cases in [`data/test_cases.json`](data/test_cases.json) follow this format:

```json
{
    "id": 1,
    "question": "What public repositories under the Microsoft organization mention \"Copilot\" in their description?",
    "expected_tools": [
        "GitHub.SearchRepositories"
    ],
    "local_server": false
}
```

**Properties:**
- `id`: Unique test case identifier
- `question`: Natural language query to test
- `expected_tools`: List of expected tool matches in "Server.Tool" format
- `local_server`: Whether test requires local server tools

## Evaluation Metrics

### Match Tiers

The application evaluates tool discovery accuracy across multiple tiers:

- **Top-1 Match**: Expected tool appears in the first result
- **Top-3 Match**: Expected tool appears in the top 3 results
- **Top-5 Match**: Expected tool appears in the top 5 results
- **Top-10 Match**: Expected tool appears in the top 10 results

### Performance Metrics

- **Execution Time**: Per-query and average response times
- **Success Rate**: Percentage of queries that found expected tools
- **Cache Hit Rate**: Efficiency of search result caching
- **Missing Tools**: Analysis of tools that should have been found but weren't

### Sample Output

```
====TEST RUN SUMMARY====
Total queries processed: 50
Successful queries: 48
Failed queries: 2
Cache hit rate: 12.0%
Total execution time: 15.43 seconds
Average time per query: 308.60 ms

====MATCH SUMMARY====
Match success rate: 84.0% (42)
Match miss rate: 16.0% (8)
Top match: 28 (66.7%)
Top 3 matches: 8 (19.0%)
Top 5 matches: 4 (9.5%)
Top 10 matches: 2 (4.8%)

====MISSING TOOLS====
GitHub.SearchRepositories: 5
FileSystem.writeFile: 3
Database.queryTable: 2
```

## Key Functions

### `run_single_query()`
Interactive mode for manual testing with real-time feedback.

### `test_run()`
Automated testing mode that processes batch test cases and generates comprehensive reports.

### `run_single_test(query: str) -> dict`
Core testing function that evaluates a single query and returns detailed results including:
- Match status across all tiers
- Matching, missing, and unexpected tools
- Performance metrics

## Test Case Management

### Filtering
- Automatically filters test cases based on server configuration
- Supports both local and remote server testing
- Random sampling for varied test runs

### Local vs Remote Testing
The application automatically filters test cases based on the `USE_LOCAL_TOOLS` setting:
- **Remote Mode**: Excludes tests marked with `"local_server": true`
- **Local Mode**: Includes all test cases

## Development

### Prerequisites

- Python 3.8+
- MCP Tool Router Server (from [`../server/`](../server/))
- Access to configured search backends (Azure or local)

### Running Tests

1. **Configure Settings**: Update [`data/config.ini`](data/config.ini) as needed
2. **Interactive Testing**: 
   ```python
   # In run.py, uncomment:
   run_single_query()
   ```
3. **Batch Testing**:
   ```python
   # Default mode:
   asyncio.run(test_run())
   ```

### Adding Test Cases

Add new test cases to [`data/test_cases.json`](data/test_cases.json):

```json
{
    "id": <next_id>,
    "question": "Your natural language query",
    "expected_tools": ["Server.Tool1", "Server.Tool2"],
    "local_server": false
}
```

## Output Files

- **[`data/test_output.json`](data/test_output.json)** - Stores detailed test results for analysis
- **Console Output** - Real-time statistics and summaries

## Integration

The application integrates with the MCP Tool Router Server from [`../server/`](../server/) and uses the same configuration system for seamless operation.

## Performance Tuning

Optimize testing performance by adjusting:
- `SAMPLE_SIZE` - Reduce for faster test runs
- `USE_SEARCH_CACHE` - Enable for repeated testing scenarios
- Server configuration parameters in the main router config

This application provides comprehensive testing and evaluation capabilities for the MCP Tool Router, enabling both development validation and performance optimization.