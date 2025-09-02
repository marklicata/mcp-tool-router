# MCP Tool Router Application

A testing and evaluation application for the MCP Tool Router Server that provides automated benchmark testing and tool selection quality assessment capabilities.

## Overview

The MCP Tool Router Application serves as a client interface for testing and evaluating the performance of the MCP Tool Router Server. The application focuses on automated testing with comprehensive performance metrics and tool selection quality evaluation using advanced machine learning metrics.

## Features

- **Automated Benchmark Testing**: Batch evaluation against predefined test case collections
- **Advanced Metrics Evaluation**: Precision@K, Recall@K, nDCG, Average Precision, and semantic analysis
- **Performance Analytics**: Detailed timing measurements with percentile analysis (TP50, TP75, TP90, TP95)
- **Match Tier Analysis**: Multi-tier matching evaluation (Top-1, Top-3, Top-5, Top-10)
- **Comparison Testing**: Side-by-side evaluation of selection-enabled vs selection-disabled modes
- **Statistical Reporting**: Comprehensive test run summaries with success rates and missed tool analysis
- **Interactive Chat Mode**: Simple query interface for manual testing
- **Azure OpenAI Integration**: Semantic similarity analysis using text embeddings

## Architecture

### Core Components

- **[`run.py`](run.py)** - Main application entry point with chat and automated testing modes
- **[`utils_test_manager.py`](utils_test_manager.py)** - Core testing framework with `TestRunManager`, `TestResult`, and `TestCase` classes
- **[`utils_request_manager.py`](utils_request_manager.py)** - HTTP client for communicating with the MCP Tool Router Server
- **[`utils_metrics.py`](utils_metrics.py)** - Advanced metrics calculation including semantic analysis and machine learning evaluation metrics
- **[`data/config.ini`](data/config.ini)** - Application configuration settings
- **Test Case Collections** - Multiple JSON files with different test scenarios

### Key Classes

- **`TestRunManager`** - Main orchestrator for test execution and evaluation
- **`RequestHandler`** - HTTP client for communicating with the MCP Tool Router Server
- **`MetricsCalculator`** - Advanced metrics computation including Azure OpenAI integration
- **`TestResult`** - Data structure for storing individual test outcomes with comprehensive metrics
- **`TestCase`** - Data structure for test case definitions
- **`MetricsResult`** - Data structure for storing calculated metrics (precision, recall, nDCG, etc.)

## Configuration

Configure the application through [`data/config.ini`](data/config.ini):

```ini
[TestRun]
SAMPLE_SIZE = 50                                               # Number of test cases to run in batch mode
TEST_CASE_FILE = python/src/app/data/test_cases_complex_50.json # Test case file to use
RUN_SIMPLE_SEARCH_COMPARISON = True                           # Enable comparison with basic search
TOOLS_TO_RETURN = 10                                          # Number of tools to return from server
MAX_TOOLS_TO_RETURN = 100                                     # Maximum tools for comparison testing
```

## Usage

### Automated Testing Mode (Default)

Run comprehensive benchmarks against the test case database:

```python
# Default mode in run.py
test_runner = TestRunManager()
asyncio.run(test_runner.run_multiple_test_cases())
```

**Features:**
- Batch processing of test cases with configurable count
- Concurrent test execution for improved performance
- Advanced metrics evaluation (precision, recall, nDCG, semantic analysis)
- Statistical analysis and reporting with percentile breakdowns

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

Test cases in the various JSON files follow this format:

```json
{
    "question": "Find the machine learning org in GitHub",
    "expected_tools": [
        "GitHub.SearchOrgs"
    ]
}
```

**Properties:**
- `question`: Natural language query to test
- `expected_tools`: List of expected tool matches in "Server.Tool" format

### Available Test Case Collections

- **`test_cases_simple_20_SWE.json`** - 20 simple software engineering test cases
- **`test_cases_simple_100_M365.json`** - 100 simple Microsoft 365 test cases
- **`test_cases_simple_600.json`** - 600 simple test cases across domains
- **`test_cases_complex_50.json`** - 50 complex test scenarios
- **`test_cases_complex_175.json`** - 175 complex test scenarios

## Evaluation Metrics

### Advanced Machine Learning Metrics

- **Precision@K**: Proportion of relevant tools in top-K results
- **Recall@K**: Proportion of relevant tools successfully retrieved
- **Average Precision**: Ranking-sensitive metric rewarding earlier placement of relevant tools
- **nDCG@K**: Normalized Discounted Cumulative Gain with position-based discounting
- **Redundancy Score**: Semantic similarity between selected tools using Azure OpenAI embeddings
- **Confusion Index**: Cognitive load estimation combining list length and redundancy

### Match Tier Analysis

- **Top-1 Match**: Expected tool appears in the first result
- **Top-3 Match**: Expected tool appears in the top 3 results
- **Top-5 Match**: Expected tool appears in the top 5 results
- **Top-10 Match**: Expected tool appears in the top 10 results

### Performance Metrics

- **Response Time Percentiles**: TP50, TP75, TP90, TP95 analysis
- **Success/Failure Rates**: Query processing statistics
- **Missing Tool Analysis**: Detailed breakdown of commonly missed tools

### Sample Output

```
====TEST RUN SUMMARY====
Total queries processed: 50
Successful queries: 50
Failed queries: 0
TP50 response time: 245.67 ms
TP75 response time: 312.45 ms
TP90 response time: 487.23 ms
TP95 response time: 623.12 ms

====TOOL SELECTION QUALITY====
Match success rate: 80.0% (40)
Match miss rate: 20.0% (10)
Matches in first slot: 30 (75.0%)
Matches in top 3: 5 (12.5%)
Matches in top 5: 3 (7.5%)
Matches in top 10: 2 (5.0%)

====TOOL SELECTION ACCURACY====
| Metric             | Description                                                                                                      | Range     | Selection Enabled | Selection Disabled |
|--------------------|------------------------------------------------------------------------------------------------------------------|-----------|-------------------|--------------------|
| Precision@K        | Measures how many of the top-K selected tools are actually relevant                                            | 0.0 - 1.0 | 0.8520           | 0.7234            |
| Recall@K           | Measures how many of the relevant tools were successfully retrieved in the top-K list                         | 0.0 - 1.0 | 0.7850           | 0.6543            |
| Average Precision  | A ranking-sensitive metric that rewards placing relevant tools earlier in the list                             | 0.0 - 1.0 | 0.7654           | 0.6321            |
| nDCG@K             | Normalized Discounted Cumulative Gain. Rewards placing relevant tools higher in the ranking                   | 0.0 - 1.0 | 0.8123           | 0.7234            |
| Redundancy Score   | Measures semantic similarity among selected tools. High scores indicate many tools are too similar            | 0.0 - 1.0 | 0.3456           | 0.4567            |
| Confusion Index    | Combines list length and redundancy to estimate cognitive load on the LLM                                      | 0.0 - inf | 3.4560           | 4.5670            |

====COMMONLY MISSED TOOLS====
Test cases missing tools: 10 (20.0%)
Average missing tools per test case: 1.20
```

## Key Functions

### `TestRunManager.run_multiple_test_cases(count: int)`
Main automated testing function that:
- Loads and shuffles test cases from configured file
- Executes tests concurrently with asyncio
- Calculates comprehensive metrics including semantic analysis
- Generates detailed reports with statistical breakdowns
- Saves results to JSON for further analysis

### `TestRunManager.run_single_test(test_case: TestCase, index: int)`
Core testing function that evaluates a single query and returns:
- Tool matching analysis across multiple tiers
- Performance timing metrics
- Advanced ML metrics (precision, recall, nDCG, etc.)
- Semantic similarity analysis using Azure OpenAI
- Comparison between selection-enabled and selection-disabled modes

### `MetricsCalculator.compute_metrics(selected_tools, expected_tools, top_k)`
Advanced metrics computation including:
- Precision and recall at K
- Average precision with ranking sensitivity
- nDCG with position-based discounting
- Semantic redundancy analysis using embeddings
- Confusion index calculation

### `run_chat()`
Interactive mode for manual query testing with direct server communication.

## Quality Assessment

### Semantic Analysis
The application uses Azure OpenAI embeddings to evaluate:
- **Redundancy Score**: Semantic similarity between selected tools
- **Confusion Index**: Estimated cognitive load for LLMs
- **Tool Overlap Analysis**: Identification of functionally similar tools

### Advanced Metrics
Information retrieval metrics adapted for tool selection:
- **Precision@K**: Relevance of top-K selections
- **Recall@K**: Coverage of relevant tools
- **nDCG@K**: Position-aware relevance scoring
- **Average Precision**: Ranking-sensitive evaluation

### Comparison Testing
Side-by-side evaluation of:
- **Selection-Enabled Mode**: Using the MCP Tool Router's intelligent selection
- **Selection-Disabled Mode**: Using basic Azure Search without selection logic

## Development

### Prerequisites

- Python 3.8+
- Required packages: `azure-identity`, `openai`, `tabulate`, `pydantic`, `scikit-learn`, `numpy`
- MCP Tool Router Server running on localhost:8000
- Azure OpenAI access for semantic analysis

### Running Tests

1. **Configure Settings**: Update [`data/config.ini`](data/config.ini) as needed
2. **Start MCP Server**: Ensure the Tool Router Server is running on localhost:8000
3. **Run Automated Tests**:
   ```bash
   python run.py
   ```

### Adding Test Cases

Add new test cases to any of the JSON files or create new collections:

```json
{
    "question": "Your natural language query",
    "expected_tools": ["Server.Tool1", "Server.Tool2"]
}
```

## Integration

The application integrates with:
- **MCP Tool Router Server**: HTTP API on localhost:8000 with endpoints `/get_mcp_tools/` and `/run_az_search/`
- **Azure OpenAI**: For semantic similarity analysis using text-embedding-3-large model
- **Azure Cognitive Services**: For authentication and embeddings computation

## Performance Features

- **Concurrent Execution**: Parallel test case processing with asyncio
- **Configurable Batch Sizes**: Adjust `SAMPLE_SIZE` for testing needs
- **Random Sampling**: Varied test runs with shuffled test cases
- **Comprehensive Analytics**: Multiple evaluation approaches with statistical analysis
- **Result Persistence**: JSON output for further analysis and visualization

This application provides a robust testing and evaluation framework for the MCP Tool Router, enabling development validation and performance optimization through advanced machine learning metrics and semantic analysis.