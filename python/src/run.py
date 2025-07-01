"""
High-performance version of the MCP Tool Router execution script.
Demonstrates various performance optimizations including:
- Parallel query processing
- Connection pooling
- Batch operations
- Caching
- Memory optimization
"""

import asyncio
import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Any
from core.semantic_search import SemanticSearch
from core.cache import QueryResponseCache
from core.performance_utils import performance_monitor, ConcurrencyManager, BatchProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration variables
API_KEY = "pcsk_5snYAu_S8CpekGvaej1Ywxv5VdN9pxkYxA2nURBQmqStJ9tSyARLVGbWgrqTxhKGDKJrrd"
ENVIRONMENT = "https://mcp-server-tools-mypk21u.svc.aped-4627-b74a.pinecone.io"
SEARCH_INDEX = "mcp-server-tools"
CACHE_INDEX = "mcp-tool-selection-cache"
SPEC = {
    "cloud": "aws",
    "region": "us-east-1",
    "type": "Dense",
    "Capacity Mode": "Serverless",
    "Model": "multilingual-e5-large"
}

# Optimized query sets with better categorization
QUERY_SETS = {
    "github_questions":[
        "What’s the difference between Git and GitHub?",
        "How do I initialize a Git repository?",
        "How do I clone a private GitHub repo?",
        "What’s the purpose of `.gitignore`?",
        "How do I resolve a merge conflict?",
        "What’s the safest way to revert a commit?",
        "When should I use rebase vs merge?",
        "How do I squash commits before a pull request?",
        "How do I tag a release version?",
        "How can I fork and keep my fork up to date?",
        "How do I open a pull request from a feature branch?",
        "What is the difference between `main` and `develop` branches?",
        "How do I enforce branch protection rules?",
        "How do I request reviewers automatically?",
        "How can I link pull requests to issues?",
        "Can I block PRs with failing checks?",
        "What are GitHub Actions, and how do I set them up?",
        "How do I automate CI/CD using GitHub Actions?",
        "What does `CODEOWNERS` do?",
        "How do I leave feedback or suggest code changes in a PR?",
        "What’s the best way to organize issues with labels?",
        "How do GitHub Projects compare to Jira?",
        "Can GitHub track sprint velocity?",
        "How do I enable Discussions for community Q&A?",
        "What are milestones and how are they used?",
        "How do I generate a personal access token (PAT)?",
        "How does Dependabot work?",
        "What is secret scanning in GitHub?",
        "How do I configure SSO and repository access?",
        "How do I enforce 2FA for organization members?",
        "How can I automate changelog generation?",
        "Can I use GitHub CLI for scripting tasks?",
        "What is GitHub Copilot and how is it used effectively?",
        "How can I publish a GitHub Pages site?",
        "How do I manage monorepos on GitHub?",
        "Can I integrate GitHub with Azure DevOps?",
        "How do I use GitHub API to manage workflows?",
        "What's the rate limit on GitHub’s REST API?",
        "How do I create a new repository on GitHub?",
        "What's the best way to set up GitHub Actions for a Python project?",
        "How can I integrate GitHub with Azure DevOps pipelines?",
        "What are some best practices for using GitHub Pull Requests?",
        "How do I use GitHub CLI to automate issue tracking?",
        "What is the GitHub REST API and how can I use it from Python?",
        "How do I manage secrets in GitHub Actions when deploying to Azure?",
        "Which pull requests have been open the longest without feedback?",
        "Can you auto-label PRs based on file path and prior tags?",
        "What workflows failed most frequently in the last 7 days?"
    ],
    "azure_questions": [
        "What’s the difference between Azure AD and Microsoft Entra ID?",
        "How do I choose between Azure App Service, Azure Functions, and AKS?",
        "What is an Azure Resource Group and why is it needed?",
        "How do I provision infrastructure using Bicep or ARM templates?",
        "Can I use Terraform with Azure?",
        "How do I deploy a Python/Node app to Azure App Service?",
        "How do I set up CI/CD pipelines with GitHub Actions and Azure?",
        "What's the best way to manage environment variables in Azure?",
        "Can I deploy multiple containers to a single Azure Web App?",
        "How do I configure custom domains and SSL certificates?",
        "How do I store and query data in Azure Cosmos DB?",
        "What's the difference between Azure Blob Storage and Data Lake?",
        "How can I integrate OpenAI into my Azure application?",
        "How do I use Azure Cognitive Services for sentiment analysis?",
        "What are best practices for securing data in Azure?",
        "How can I monitor app performance using Application Insights?",
        "What’s the best way to manage logs from multiple Azure services?",
        "How do I set up cost alerts in Azure?",
        "What is Azure Monitor and how does it differ from Log Analytics?",
        "Can I debug Azure Functions locally?",
        "How do I configure Managed Identity in Azure?",
        "What’s the difference between user-assigned and system-assigned identities?",
        "How do I enable role-based access control (RBAC)?",
        "How can I audit Azure activity using logs?",
        "What tools does Azure offer for secure key management?",
        "What is Azure DevOps and how does it compare to GitHub Actions?",
        "How can I run scheduled jobs in Azure?",
        "How do I containerize and deploy using Azure Container Apps?",
        "How do I scale my app based on load?",
        "How do I enable blue-green or canary deployments?",
        "How do I configure API Management in Azure?",
        "Can Azure Functions respond to HTTP triggers with authentication?",
        "How can I test APIs hosted in Azure securely?",
        "What’s the difference between Azure Front Door and Application Gateway?",
        "How do I connect to an on-premise service from Azure?",
        "How do I deploy a web app to Azure App Service from GitHub?",
        "What's the difference between Azure Functions and Azure Logic Apps?",
        "How do I debug Azure Functions locally in VSCode?",
        "How can I visualize Azure resource groups in VSCode?",
        "What's the easiest way to publish a static site from GitHub to Azure Blob Storage?",
        "How do I monitor deployment logs in Azure App Service through VSCode?",
        "What's the role of service principals when deploying to Azure from GitHub?",
        "How do I authenticate to Azure using the Azure CLI inside VSCode?",
        "Can I trigger an Azure Pipeline from a GitHub webhook?",
        "What resource groups have had the highest cost spikes this week?"
    ], 
    "general_dev_questions": [
        "How do I prioritize technical debt vs feature work?",
        "What tools help track engineering velocity?",
        "How do I improve my debugging skills?",
        "How do I write better documentation?",
        "What’s the best way to onboard a new dev to our repo?",
        "When should I use microservices vs monoliths?",
        "What’s a good design pattern for stateful web apps?",
        "How do I evaluate trade-offs in system design?",
        "What is event-driven architecture and when to use it?",
        "How should I handle retries and failures in distributed systems?",
        "What topics should I study to become a senior engineer?",
        "How do I stay current on new technologies?",
        "What are good technical blogs or podcasts to follow?",
        "How can I get better at code reviews?",
        "How do I plan a learning roadmap?",
        "What’s the difference between unit, integration, and E2E tests?",
        "How much test coverage is 'enough'?",
        "How do I mock dependencies in my tests?",
        "What are best practices for writing testable code?",
        "How can I introduce automated testing to a legacy codebase?",
        "How do I give constructive feedback on code?",
        "How do I handle disagreements during architecture discussions?",
        "How should I respond to unexpected production outages?",
        "How do I encourage ownership among developers?",
        "What are good 1:1 questions for mentoring junior devs?",
        "How do I measure developer impact?",
        "How do I communicate technical decisions to execs?",
        "How do I advocate for refactoring initiatives?",
        "What role should I play in roadmap planning?",
        "How can I contribute to building a healthy engineering culture?",
        "What are GitHub Codespaces and how do I use them with VSCode?",
        "How can I use GitHub Copilot in Visual Studio Code?",
        "How do I connect VSCode to a remote GitHub repository?",
        "How do I configure SSH keys for GitHub on Windows using VSCode?",
        "What extensions should I install in VSCode for Azure development?",
        "How do I work with Bicep files in VSCode for Azure ARM templates?",
        "How can I integrate VSCode with GitHub Codespaces and Azure Repos?",
        "Which extensions are consuming the most memory or CPU?",
        "Can you suggest underused features based on my usage patterns?",
        "What files have I spent the most time editing in the last week?"
    ]
}

class OptimizedMCPRouter:
    """High-performance MCP Tool Router"""
    
    def __init__(self):
        self.search = SemanticSearch(
            api_key=API_KEY,
            environment=ENVIRONMENT,
            index_name=SEARCH_INDEX,
            spec=SPEC
        )
        
        self.cache = QueryResponseCache(
            api_key=API_KEY,
            environment=ENVIRONMENT,
            index_name=CACHE_INDEX,
            spec=SPEC
        )
        
        self.concurrency_manager = ConcurrencyManager(max_concurrent=15)
        
    @performance_monitor.track_time("single_query")
    async def process_single_query(self, query: str, category: str) -> Dict[str, Any]:
        """Process a single query with performance tracking"""

        try:
            # Try cache first
            cached_result = await self.cache.get_cached_response(query)
            if cached_result:
                return {
                    'query': query,
                    'category': category,
                    'execution_time': cached_result.execution_time,
                    'cache_hit': True,
                    'tool_count': len(cached_result.tools),
                    'tools': [tool.name for tool in cached_result.tools]
                }
            
            # Perform search
            search_result = await self.search.get_tools(
                query=query, 
                top_k=10, 
                tool_return_limit=10
            )
            
            # Cache the result asynchronously (fire and forget)
            asyncio.create_task(self.cache.create_cache_record(search_result))
            
            return {
                'query': query,
                'category': category,
                'execution_time': search_result.execution_time,
                'cache_hit': False,
                'tool_count': len(search_result.tools),
                'tools': [tool.name for tool in search_result.tools]
            }
            
        except Exception as e:
            logging.error(f"Error processing query '{query}': {e}")
            return {
                'query': query,
                'category': category,
                'execution_time': 0,
                'cache_hit': False,
                'tool_count': 0,
                'error': str(e)
            }
    
    async def run_performance_benchmark(self, sample_size: int):
        """Run comprehensive performance benchmark"""
        logging.info("Starting optimized performance benchmark...")
        
        # Prepare all queries with metadata
        all_queries = []
        for category, queries in QUERY_SETS.items():
            for query in queries:
                all_queries.append((query, category))
        
        if sample_size > 0 and sample_size < len(all_queries):
            random.shuffle(all_queries)
            all_queries = all_queries[:sample_size]
        
        # Process all queries in parallel with controlled concurrency
        start_time = time.time()
        
        async def bounded_query(query_data):
            query, category = query_data
            return await self.concurrency_manager.execute_with_limit(
                self.process_single_query(query, category)
            )
        
        # Use batch processing for memory efficiency
        results = await BatchProcessor.process_in_batches(
            all_queries,
            bounded_query,
            batch_size=10,
            max_concurrent=3
        )
        
        total_time = time.time() - start_time
        
        # Analyze results
        self.analyze_results(results, total_time)
        
        # Log performance statistics
        performance_monitor.log_stats()
        
        return results
    
    def analyze_results(self, results: List[Dict[str, Any]], total_time: float):
        """Analyze and log benchmark results"""
        logging.info("=== Benchmark Results ===")
        
        # Overall statistics
        total_queries = len(results)
        successful_queries = len([r for r in results if 'error' not in r])
        cache_hits = len([r for r in results if r.get('cache_hit', False)])
        
        logging.info(f"Total queries processed: {total_queries}")
        logging.info(f"Successful queries: {successful_queries}")
        logging.info(f"Cache hit rate: {cache_hits/total_queries*100:.1f}%")
        logging.info(f"Total execution time: {total_time:.2f} seconds")
        logging.info(f"Average time per query: {total_time*1000/total_queries:.2f} ms")
        
        # Category-wise analysis
        category_stats = {}
        for result in results:
            category = result['category']
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total_time': 0,
                    'cache_hits': 0,
                    'errors': 0
                }
            
            stats = category_stats[category]
            stats['count'] += 1
            stats['total_time'] += result['execution_time']
            if result.get('cache_hit', False):
                stats['cache_hits'] += 1
            if 'error' in result:
                stats['errors'] += 1
        
        logging.info("\n=== Category Performance ===")
        for category, stats in category_stats.items():
            avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
            cache_rate = stats['cache_hits'] / stats['count'] * 100 if stats['count'] > 0 else 0
            logging.info(f"{category}: count={stats['count']}, avg={avg_time:.1f}ms, cache_rate={cache_rate:.1f}%, "
                        f"errors={stats['errors']}")

async def initialize_tool_records(router: OptimizedMCPRouter):
    # Initialize tool records if needed (batch processing)
    try:
        script_dir = Path(__file__).parent
        await router.search.create_tool_records_from_file_batch(
            f"{script_dir}/core/mcp_servers.json",
            batch_size=12  # Process all tools in one batch
        )
        logging.info("Tool records initialized successfully")
    except Exception as e:
        logging.warning(f"Tool records initialization skipped: {e}")
    return True

async def main():
    """Main execution function"""
    router = OptimizedMCPRouter()

    #### 
    # Util to delete cache records if needed
    ####
    router.cache.index.delete(namespace="__default__", delete_all=True)
    
    ####
    # Perf run of all sample questions.
    ####
    # results = await router.run_performance_benchmark(sample_size=50)

    ####
    # Demo run with user-provided questions.
    ####
    # query = input("Enter a query to test the MCP Tool Router: ")
    # while query is not None and query != "":
    #     results = await router.process_single_query(query=query, category="Custom Query")
    #     for key, value in results.items():
    #         logging.info(f"{key}: {value}")

    #     query = input("Type a new query or press Enter to exit...")
    
if __name__ == "__main__":
    asyncio.run(main())
