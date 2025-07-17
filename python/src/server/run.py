from threading import local
import asyncio, os, sys, logging, json, time, random, configparser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from datetime import datetime
from src.server.utils_azure_search import AzureSearchManager
from src.server.utils_local_search import LocalSearchManager
from src.server.utils_core import ToolListResult, ToolResult, Server
from typing import List, Dict, Any, Literal
from collections import Counter
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# tool_router = FastMCP(
#     name="MCP Tool Router"
# )

# Global router instance
router_instance = None


class ToolRouter:
    """High-performance MCP Tool Router"""
    
    def __init__(self):

        # Configuration variables from config.ini
        self.config = configparser.ConfigParser()
        self.config.read('python/src/server/data/config.ini')
        self.max_concurrent_requests = self.config.getint('ToolRouter', 'MAX_CONCURRENT_REQUESTS', fallback=15)
        self.tool_result_cnt = self.config.getint('ToolRouter', 'TOOL_RESULT_CNT', fallback=10)
        self.tool_return_limit = self.config.getint('ToolRouter', 'TOOL_RETURN_LIMIT', fallback=10)
        self.use_local_tools = self.config.getboolean('ToolRouter', 'USE_LOCAL_TOOLS', fallback=False)
        self.use_search_cache = self.config.getboolean('TestRun', 'USE_SEARCH_CACHE', fallback=False)

        self.azure_search_manager = AzureSearchManager()
        
        if self.use_local_tools:
            from src.server.utils_local_search import LocalSearchManager
            self.local_search_manager = LocalSearchManager()

    async def normalize_NNB_scores(self, scores: list[float]) -> list[float]:
        """
        Normalize scores to a range of 0 to 100
        Args:
            scores (list[float]): List of scores to normalize
        Returns:
            list[float]: Normalized scores
        """

        def rescale(value, old_min, old_max, new_min=0, new_max=1):
            return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
        if not scores:
            return []
        min_s = min(scores) if min(scores) > 0 else 0
        max_s = max(scores) if max(scores) > 0 else 1  # Avoid division by zero
        return [rescale(s, min_s, max_s) for s in scores]



    async def get_local_tools(self, query: str) -> ToolListResult:
        """
        Retrieve local tools based on the query.
        Args:
            query (str): The query string to search for local tools.
        Returns:
            ToolList: A ToolList containing the local tools matching the query.
        """
        logging.info(f"Searching for local tools matching query: '{query}'")
        try:
            local_results = await self.local_search_manager.search(
                query=query,
                top_k=self.tool_result_cnt
            )
        except Exception as e:
            logging.error(f"Error querying Local Search for '{query}': {e}")
            return None

        if local_results is not None:
            return local_results
        else:
            logging.info(f"No local tools found matching query: '{query}'")
            return ToolListResult(tools=[], query=query)


    async def get_remote_tools(self, query: str) -> ToolListResult:
        """
        Retrieve remote tools based on the query.
        Args:
            query (str): The query string to search for remote tools.
        Returns:
            ToolList: A ToolList containing the remote tools matching the query.
        """

        #Timer start
        start_time = time.time()
        try:
            search_result = await self.azure_search_manager.search(
                client=self.azure_search_manager.search_client,
                search_text=query,
                top_k=self.tool_result_cnt
            )
        except Exception as e:
            logging.error(f"Error querying Azure Search for '{query}': {e}")
            return None
        if search_result is not None:
            # Convert to list to check if we have results
            result_list = list(search_result)
            if result_list:
                search_result_list = ToolListResult(tools=[], query=query)
                for result in result_list:
                    parts = result.get('id').split("_")
                    _tool = ToolResult(
                        score=result.get('@search.score', 0.0),
                        server=Server(id="123", name=parts[0], location="remote"),
                        toolset="_".join(parts[1:-1]),                  #### TODO: Fix this to use correct Server ID
                        id=result.get('id'),
                        name=parts[-1],
                        endpoint=result.get('endpoint', ''),
                        kwargs=result.get('kwargs', {})
                    )
                    search_result_list.tools.append(_tool)
                if len(search_result_list.tools) == 0:
                    logging.info("No results found.")                
                return search_result_list
        else:
            logging.info(f"No remote tools found matching query: '{query}'")
            return ToolListResult(tools=[], query=query)


    async def route(self, query: str) -> ToolListResult:
        """
        Process a single query with performance tracking
        Args:
            query (str): The query string to process
        Returns:
            ToolListResult: A ToolListResult containing the results of the query processing
        """

        tasks = [
            asyncio.create_task(self.get_remote_tools(query))
        ]
        if self.use_local_tools:
            tasks.append(asyncio.create_task(self.get_local_tools(query)))

        ToolListResults = await asyncio.gather(*tasks)

        # Combine results from all sources
        combined_results = ToolListResult(tools=[], query=query)
        for tool_list in ToolListResults:
            if tool_list is None or tool_list.tools is None:
                continue
            tool_list.tools.sort(key=lambda x: x.score, reverse=True)
            # Normalize scores
            scores = [tool.score for tool in tool_list.tools]
            normalized_scores = await self.normalize_NNB_scores(scores)
            for tool, norm_score in zip(tool_list.tools, normalized_scores):
                tool.score = norm_score
            
            for tool in tool_list.tools:
                if tool.id not in [t.id for t in combined_results.tools]:
                    combined_results.tools.append(tool)
        
        # Sort and limit results
        combined_results.tools.sort(key=lambda x: x.score, reverse=True)
        return ToolListResult(tools=combined_results.tools[:self.tool_return_limit], query=query)



# @tool_router.tool()
async def get_mcp_tools(query:str) -> ToolListResult:
    """
    Get tools based on the query.
    Args:
        query (str): The query string to search for tools.
    Returns:
        ToolListResult: A ToolListResult containing the tools matching the query.
    """
    global router_instance
    if router_instance is None:
        router_instance = ToolRouter()
    
    # Route the query to get tools
    return await router_instance.route(query)


# @tool_router.tool()
async def get_router_status() -> Dict[str, Any]:
    """
    Get the current status and configuration of the tool router.
    
    Returns:
        Dictionary containing router status and configuration
    """
    global router_instance
    if router_instance is None:
        router_instance = ToolRouter()
    
    try:
        return {
            "status": "active",
            "configuration": {
                "max_concurrent_requests": router_instance.max_concurrent_requests,
                "tool_result_count": router_instance.tool_result_cnt,
                "tool_return_limit": router_instance.tool_return_limit,
                "use_local_tools": router_instance.use_local_tools,
                "use_search_cache": router_instance.use_search_cache
            },
            "services": {
                "azure_search": "initialized" if hasattr(router_instance, 'azure_search_manager') else "not_initialized",
                "local_search": "initialized" if hasattr(router_instance, 'local_search_manager') else "not_initialized"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_router_status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    

async def main():
    """
    Main function to run the tool router.
    This function initializes the tool router and starts the FastMCP server.
    """
    global router_instance
    if router_instance is None:
        router_instance = ToolRouter()
    file_name = 'python/src/server/data/mcp_servers.json'
    # await router_instance.azure_search_manager.create_tools_from_file(file_path=file_name)


if __name__ == "__main__":
    asyncio.run(main())