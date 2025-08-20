import os, sys, logging, json, time, configparser, uuid
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from datetime import datetime
from utils_azure_search import AzureSearchManager
from utils_objects import Server, Tool, ToolResults
from typing import List, Dict, Any
from fastapi import FastAPI, Request
import uvicorn


# GLOBAL VARIABLES
app = FastAPI()
router_instance = None

class ToolRouter:
    """High-performance MCP Tool Router"""

    def __init__(self, token: str = None):

        # Configuration variables from config.ini
        self.config = configparser.ConfigParser()
        self.config.read('python/src/server/data/config.ini')
        self.max_concurrent_requests = self.config.getint('ToolRouter', 'MAX_CONCURRENT_REQUESTS', fallback=15)
        self.tool_result_cnt = self.config.getint('ToolRouter', 'TOOL_RESULT_CNT', fallback=10)
        self.tool_return_limit = self.config.getint('ToolRouter', 'TOOL_RETURN_LIMIT', fallback=10)
        self.use_local_tools = self.config.getboolean('ToolRouter', 'USE_LOCAL_TOOLS', fallback=False)
        self.use_search_cache = self.config.getboolean('TestRun', 'USE_SEARCH_CACHE', fallback=False)
        self.minimum_tool_score = self.config.getfloat('ToolRouter', 'MINIMUM_TOOL_SCORE', fallback=0.5)

        # Initialize the Azure Search Manager
        self.azure_search_manager = AzureSearchManager()

        ####
        # TODO: When local tools are implemented, initialize the LocalSearchManager
        # First check if self.use_local_tools is True
        ####

    async def normalize_NNB_scores(self, scores: list[float]) -> list[float]:
        """
        Normalize scores to a range of 0 to 100
        Args:
            scores (list[float]): List of scores to normalize
        Returns:
            list[float]: Normalized scores
        """

        def rescale(value, old_min, old_max, new_min=0, new_max=1):
            """Rescale a value from one range to another. Used when multiple vectors have different ranges."""
            return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
        
        if not scores:
            return []
        min_s = min(scores) if min(scores) > 0 else 0
        max_s = max(scores) if max(scores) > 0 else 1  # Avoid division by zero
        return [rescale(s, min_s, max_s) for s in scores]


    ####
    # TODO: When local tools are implemented, implement the get_local_tools method
    # This method should retrieve local tools based on the query.
    # And return a list of Tool objects.
    ####
    async def get_local_tools(self, query: str) -> List[Tool]:
        """
        Retrieve local tools based on the query.
        Args:
            query (str): The query string to search for local tools.
        Returns:
            List[Tool]: A list of local tools matching the query.
        """
        return []  # Placeholder for local tools retrieval logic


    async def get_remote_tools(self, query: str, allowed_tools: List[str] = []) -> List[Tool]:
        """
        Retrieve remote tools based on the query.
        Args:
            query (str): The query string to search for remote tools.
            allowed_tools (List[str]): A list of allowed tool IDs for the query.
        Returns:
            List[Tool]: A list of remote tools matching the query.
        """
        try:
            search_result = await self.azure_search_manager.perform_azure_search(
                search_text=query,
                top_k=self.tool_result_cnt,
                allowed_tools=allowed_tools
            )
        except Exception as e:
            logging.error(f"Error querying Azure Search for '{query}': {e}")
            return [None]
        if search_result is not None:
            # Convert to list to check if we have results
            result_list = list(search_result)
            if result_list:
                search_result_list = [Tool(
                    id=result.get('id'),
                    server=result.get('server', ''),
                    toolset=result.get('toolset', ''),
                    name=result.get('name', ''),
                    description=result.get('description', ''),
                    tool_vector=result.get('tool_vector', []),
                    score=result.get('@search.reranker_score', 0.0),
                ) for result in result_list if result.get('id') and result.get('server') and result.get('name')]

                if len(search_result_list) == 0:
                    logging.info("No results found.")                
                return search_result_list
        else:
            logging.info(f"No remote tools found matching query: '{query}'")
            return []


    async def route(self, query: str, allowed_tools: List[str] = []) -> ToolResults:
        """
        Process a single query with performance tracking
        Args:
            query (str): The query string to process
            allowed_tools (List[str]): A list of allowed tool IDs for the query
        Returns:
            ToolResults: A ToolResults object containing the results of the query processing
        """

        start_execution_time = time.time()
        try:
            remote_tools_list = await self.get_remote_tools(query=query, allowed_tools=allowed_tools)
            remote_tools_list.sort(key=lambda x: x.score if x else 0, reverse=True)
        except Exception as e:
            logging.error(f"Error retrieving remote tools: {e}")
            remote_tools_list = []
   
        if len(remote_tools_list) == 0 or remote_tools_list is None:
            logging.info(f"No remote tools found for query: '{query}'")
            return ToolResults(execution_time=0.0, tools=[])

        ####
        # TODO: When local tools are implemented, add the logic to retrieve local tools. Should be done async with remote call.
        # After retrieveing both remote and local tools, combine & dedupe the results.
        # Then normalize the scores and re-rank the results.
        ####

        # Make sure tools meet the minimum score requirement
        remote_tools_list = [tool for tool in remote_tools_list if tool.score >= self.minimum_tool_score]

        # Limit the number of results if needed
        if len(remote_tools_list) > self.tool_return_limit:
            remote_tools_list = remote_tools_list[:self.tool_return_limit]

        # create execution time for the query
        total_execution_time = time.time() - start_execution_time

        return ToolResults(execution_time=total_execution_time, tools=remote_tools_list)


@app.put("/get_mcp_tools/")
async def get_mcp_tools(request: Request) -> ToolResults:
    """
    Get tools based on the query.
    Args:
        request (Request): The request object containing the query and allowed tools.
    Returns:
        ToolListResult: A ToolListResult containing the tools matching the query.
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header else None
    raw_RQ_body = await request.body()
    query = json.loads(raw_RQ_body.decode("utf-8")).get("query", "")
    allowed_tools = json.loads(raw_RQ_body.decode("utf-8")).get("allowed_tools", [])

    global router_instance
    if router_instance is None:
        router_instance = ToolRouter()

    #Timer start
    start_time = time.time()

    # Check if the query is empty
    if not query or query.strip() == "":
        return {
            "error": "Query cannot be empty",
            "timestamp": datetime.now().isoformat()
        }
    
    # Route the query to get tools
    try:
        results = await router_instance.route(query=query, allowed_tools=allowed_tools)
    except Exception as e:
        logging.error(f"Error routing query '{query}': {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
    if results is None or len(results.tools) == 0:
        logging.info(f"No tools found for query: '{query}'")
        return []
    return results


@app.get("/get_router_status")
async def get_router_status(request: Request) -> Dict[str, Any]:
    """
    Get the current status and configuration of the tool router.
    
    Returns:
        Dictionary containing router status and configuration
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header else None

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
        logging.error(f"Error in get_router_status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
