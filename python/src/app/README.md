# MCP Tool Router Application

A testing and evaluation application for the MCP Tool Router Server that provides automated benchmark testing and tool quality assessment capabilities.

## Overview

The MCP Tool Router Application serves as a client interface for testing and evaluating the performance of the MCP Tool Router Server. The application focuses on automated testing with comprehensive performance metrics and tool quality evaluation using multiple assessment methods.

## Features

- **Automated Benchmark Testing**: Batch evaluation against predefined test cases
- **Multi-Metric Evaluation**: Precision, recall, and AI-judge scoring
- **Performance Analytics**: Detailed timing and accuracy measurements  
- **Match Analysis**: Multi-tier matching evaluation (Top-1, Top-3, Top-5, Top-10)
- **Statistical Reporting**: Comprehensive test run summaries with success rates
- **Interactive Chat Mode**: Simple query interface for manual testing
- **Azure OpenAI Integration**: AI-powered tool quality assessment

## Architecture

### Core Components

- **[`run.py`](run.py)** - Main application entry point with chat and automated testing modes
- **[`utils.py`](utils.py)** - Core testing framework with TestRunManager, TestResult, and TestCase classes
- **[`data/config.ini`](data/config.ini)** - Application configuration settings
- **[`data/test_cases.json`](data/test_cases.json)** - Comprehensive test case database

### Key Classes

- **`TestRunManager`** - Main orchestrator for test execution and evaluation
- **`RequestHandler`** - HTTP client for communicating with the MCP Tool Router Server
- **`TestResult`** - Data structure for storing individual test outcomes
- **`TestCase`** - Data structure for test case definitions

## Configuration

Configure the application through [`data/config.ini`](data/config.ini):

```ini
[TestRun]
SAMPLE_SIZE = 25              # Number of test cases to run in batch mode
TOOL_QUALITY_JUDGES = 7       # Number of AI judge evaluations per test
USE_SEARCH_CACHE = False      # Enable/disable search result caching

[Registry]
ENDPOINT1 = registry_endpoint_1
ENDPOINT2 = registry_endpoint_2
```

## Usage

### Automated Testing Mode (Default)

Run comprehensive benchmarks against the test case database:

```python
# Default mode in run.py
test_runner = TestRunManager()
asyncio.run(test_runner.run_multiple_test_cases(count=10))
```

**Features:**
- Batch processing of test cases with configurable count
- Concurrent test execution for improved performance
- Multi-metric evaluation (precision, recall, AI judge scoring)
- Statistical analysis and reporting

### Interactive Chat Mode

Simple query interface for manual testing:

```python
# Uncomment in run.py main section
run_chat()
```

**Features:**
- Enter natural language queries
- View JSON response from the server
- Continue with new queries or exit

## Test Case Structure

Test cases in [`data/test_cases.json`](data/test_cases.json) follow this simplified format:

```json
{
    "question": "Find GitHub users with expertise in machine learning",
    "description": "Search GitHub users by name or keywords",
    "expected_tools": [
        "GitHub.SearchUsers"
    ]
}
```

**Properties:**
- `question`: Natural language query to test
- `description`: Additional context about the tool functionality
- `expected_tools`: List of expected tool matches in "Server.Tool" format

## Evaluation Metrics

### Match Tiers

The application evaluates tool discovery accuracy across multiple tiers:

- **Top-1 Match**: Expected tool appears in the first result
- **Top-3 Match**: Expected tool appears in the top 3 results
- **Top-5 Match**: Expected tool appears in the top 5 results
- **Top-10 Match**: Expected tool appears in the top 10 results

### Quality Metrics

- **Precision**: True Positives / (True Positives + False Positives)
- **Recall**: True Positives / (True Positives + False Negatives)
- **AI Judge Score**: GPT-4 evaluation of tool relevance (0-10 scale)
- **Response Time**: Per-query execution time in milliseconds

### Sample Output

```
====TEST RUN SUMMARY====
Total queries processed: 10
Successful queries: 10
Failed queries: 0
Average time per query: 245.67 ms

====TOOL SELECTION QUALITY====
Match success rate: 80.0% (8)
Match miss rate: 20.0% (2)
Top match: 6 (75.0%)
Top 3 matches: 1 (12.5%)
Top 5 matches: 1 (12.5%)
Top 10 matches: 0 (0.0%)

====TOOL SELECTION ACCURACY====
Average Precision Score: 85.2%
Average Recall Score: 78.5%
Average Judge Score: 7.85

====MISSED TOOLS====
[Table showing expected vs missing tools for failed cases]
```

## Key Functions

### `TestRunManager.run_multiple_test_cases(count: int)`
Main automated testing function that:
- Loads and shuffles test cases
- Executes tests concurrently
- Calculates comprehensive metrics
- Generates detailed reports

### `TestRunManager.run_single_test(test_case: TestCase) -> TestResult`
Core testing function that evaluates a single query and returns:
- Tool matching analysis
- Performance metrics
- Multi-tier match results
- Quality scores (precision, recall, AI judge)

### `run_chat()`
Interactive mode for manual query testing with direct server communication.

## Quality Assessment

### AI Judge Evaluation
The application uses Azure OpenAI (GPT-4) to evaluate tool selection quality:
- Multiple independent evaluations per test case
- 0-10 scoring scale
- Average scoring across multiple judges
- Configurable number of judges per evaluation

### Precision and Recall
Traditional information retrieval metrics adapted for tool selection:
- **Precision**: How many selected tools were relevant
- **Recall**: How many relevant tools were selected

## Development

### Prerequisites

- Python 3.8+
- Required packages: `azure-identity`, `openai`, `tabulate`, `pydantic`
- MCP Tool Router Server running on localhost:8000
- Azure OpenAI access for quality evaluation

### Running Tests

1. **Configure Settings**: Update [`data/config.ini`](data/config.ini) as needed
2. **Start MCP Server**: Ensure the Tool Router Server is running on localhost:8000
3. **Run Automated Tests**:
   ```bash
   python run.py
   ```

### Adding Test Cases

Add new test cases to [`data/test_cases.json`](data/test_cases.json):

```json
{
    "question": "Your natural language query",
    "description": "Tool functionality description", 
    "expected_tools": ["Server.Tool1", "Server.Tool2"]
}
```

## Integration

The application integrates with:
- **MCP Tool Router Server**: HTTP API on localhost:8000
- **Azure OpenAI**: For AI-powered tool quality assessment
- **Galileo**: Optional logging and monitoring integration

## Performance Features

- **Concurrent Execution**: Parallel test case processing
- **Configurable Batch Sizes**: Adjust `SAMPLE_SIZE` for testing needs
- **Random Sampling**: Varied test runs with shuffled test cases
- **Comprehensive Metrics**: Multiple evaluation approaches for thorough assessment

This application provides a robust testing and evaluation framework for the MCP Tool Router, enabling both development validation and performance optimization through multiple quality assessment methodologies.