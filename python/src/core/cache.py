import json, os, asyncio, time, logging 
from datetime import datetime, timedelta
from core.objects import Tool, ToolListResponse
from core.vector_store import VectorStore
from typing import Optional


class QueryResponseCache(VectorStore):
    """
    A structured RAG cache that stores user queries and their ToolList responses.
    Uses Pinecone for vector similarity matching and SQLite for metadata storage.
    """

    def __init__(
        self,
        api_key: str,
        environment: str,
        spec: dict,
        index_name: str,
        similarity_threshold: float = 0.9,
    ):
        """
            Initialize the query response cache.
            Args:
                api_key: Pinecone API key
                environment: Pinecone environment URL
                spec: Pinecone index specification
                index_name: Name of the Pinecone index for caching
                similarity_threshold: Minimum similarity score to consider a cached response valid
        """
        self.api_key = api_key
        self.environment = environment
        self.spec = spec
        self.index_name = index_name
        self.similarity_threshold = similarity_threshold
        super().__init__(api_key=api_key, environment=environment, index_name=index_name, spec=spec)
        

    async def create_cache_record(self, toolListResponse:ToolListResponse) -> bool:
        """
        Store a query and its corresponding ToolList response.
        
        Args:
            tool_list_response: The response objet including the query, tools, execution time
            
        Returns:
            True if stored successfully, False otherwise
        """
        try: 
            # Convert Tool objects to dictionaries for JSON serialization
            tools_as_dicts = []
            for tool in toolListResponse.tools:
                if hasattr(tool, '__dict__'):
                    tools_as_dicts.append(tool.__dict__)
                else:
                    # If it's already a dict, use it as-is
                    tools_as_dicts.append(tool)
            
            # Upsert response record into the Pinecone index
            self.index.upsert([
                {
                    "id": str(datetime.now()),
                    "values": toolListResponse.embeddings,
                    "metadata": {
                        "create_datetime": str(datetime.now()),
                        "expire_datetime": str(datetime.now() + timedelta(hours=24)),
                        "tools": str(tools_as_dicts),
                        "execution_time": toolListResponse.execution_time
                    }
                }])
            return True
        except Exception as e:
            raise ValueError(f"Error upserting records: {e}")   
    
   
    async def get_cached_response(self, query: str, top_k: int = 1) -> Optional[ToolListResponse]:
        """
        Retrieve a cached response for a query or similar query using Pinecone similarity search.
        
        Args:
            query: The user query
            top_k: Number of similar queries to retrieve from Pinecone
            
        Returns:
            ToolListResponse object if found and similarity is above threshold, None otherwise
        """
        start_time = time.time()

        try:
            # Generate embeddings for the query
            embeddings = await self.get_query_embedding(query)
            
            # Search for similar cached queries
            result = await self.search_vector(
                namespace='__default__', 
                embeddings=embeddings, 
                fields=["tools", "execution_time"], 
                top_k=top_k
            )
           
            if not result or len(result) == 0:
                return None
                
            # Check similarity threshold
            if result[0].get('score', 0.0) < self.similarity_threshold:
                return None
                
            # Parse cached tools more efficiently
            cached_metadata = result[0].get('metadata', {})
            tools_str = cached_metadata.get('tools', '[]')
            
            # Handle string parsing more robustly
            try:
                if isinstance(tools_str, str):
                    # Replace single quotes with double quotes for valid JSON
                    tools_str = tools_str.replace("'", '"')
                    tools_data = json.loads(tools_str)
                else:
                    tools_data = tools_str
            except json.JSONDecodeError:
                logging.warning("Failed to parse cached tools data")
                return None
            

            # Create Tool objects efficiently
            tools = [
                Tool(
                    score=tool.get('score', 0.0),
                    id=tool.get('id', ''),
                    name=tool.get('name', ''),
                    description=tool.get('description', ''),
                    keywords=tool.get('keywords', []),
                    sample_questions=tool.get('sample_questions', []),
                    server=tool.get('server', ''),
                    toolset=tool.get('toolset', None)
                ) for tool in tools_data
            ]
            
            response = ToolListResponse(
                embeddings=embeddings, 
                query=query, 
                tools=tools, 
                execution_time=round((time.time() - start_time) * 1000)
            )
            
            return response
            
        except Exception as e:
            logging.warning(f"Error searching for cached response: {e}")
            return None