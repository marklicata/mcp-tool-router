import json, os, asyncio, time, logging
from core.objects import Tool, ToolListResponse
from core.vector_store import VectorStore


class SemanticSearch(VectorStore):
    """
    A semantic search class that handles tool records and queries using Pinecone.
    It allows for efficient batch processing of tool records and retrieval of tools based on queries.
    """
    def __init__(
        self,
        api_key: str,
        environment: str,
        spec: dict,
        index_name: str,
    ):
        self.api_key = api_key
        self.environment = environment
        self.spec = spec
        self.index_name = index_name
        super().__init__(api_key=api_key, environment=environment, index_name=index_name, spec=spec)

    async def create_tool_records_from_file_batch(self, file_path: str, batch_size: int = 10) -> bool:
        """
        Efficiently reads a JSON file and batch processes tool records for better performance.
        
        Parameters:
            file_path (str): Path to the JSON file containing server and tool data.
            batch_size (int): Number of tools to process in each batch.
        
        Returns:
            bool: True if records were successfully created, False otherwise.
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            raise ValueError(f"Error loading JSON file: {e}")

        # Prepare all tool records for batch processing
        tool_records = []
        for server in data['servers']:
            server_name = server.get('server')
            toolsets = server.get('toolsets', [])
            for toolset in toolsets:
                toolset_name = toolset.get('name', '')
                tools = toolset.get('tools', [])
                for tool in tools:
                    tool_records.append({
                        'server_name': server_name,
                        'toolset': toolset_name,
                        'tool_id': f"{server_name}_{toolset_name}_{tool.get('name', '')}",
                        'tool_name': tool.get('name', ''),
                        'tool_description': tool.get('description', ''),
                        'tools_sample_questions': ', '.join(tool.get('examples', [])),
                        'tool_keywords': ', '.join(tool.get('keywords', []))
                    })

        # Process records in batches
        for i in range(0, len(tool_records), batch_size):
            batch = tool_records[i:i + batch_size]
            await self.create_tool_records_batch(batch)
            
        return True

    async def create_tool_records_batch(self, tool_records: list) -> bool:
        """
        Creates multiple tool records in a single batch operation for better performance.
        This method generates embeddings for the tool records and upserts them into the Pinecone index.
        Parameters:
            tool_records (list): List of dictionaries containing tool information.

        Returns:
            bool: True if records were successfully created, False otherwise.
        """
        try:
            # Generate embeddings for all tools in batch
            tool_texts = [
                f"{record['server_name']} {record['tool_name']} {record['tool_description']} {record['tool_keywords']}"
                for record in tool_records
            ]
            
            # Batch embedding generation
            embeddings_response = await asyncio.to_thread(
                self.pc.inference.embed,
                model="multilingual-e5-large",
                inputs=tool_texts,
                parameters={"input_type": "query"}
            )
            
            # Prepare upsert data
            upsert_data = []
            for i, record in enumerate(tool_records):
                upsert_data.append({
                    "id": record['tool_id'],
                    "values": embeddings_response[i]['values'],
                    "metadata": {
                        "server": record['server_name'],
                        "toolset": record['toolset'],
                        "name": record['tool_name'],
                        "description": record['tool_description'],
                        "sample_questions": "",
                        "keywords": record['tool_keywords']
                    }
                })
            
            # Batch upsert
            await asyncio.to_thread(self.index.upsert, upsert_data)
            logging.info(f"Batch upserted {len(tool_records)} tools")
            return True
            
        except Exception as e:
            raise ValueError(f"Error in batch upsert: {e}")


    def create_tool_record(
        self,
        server_name: str,
        tool_id: str,
        tool_name: str,
        tool_description: str,
        tools_sample_questions: str,
        tool_keywords: str
    ):
        """
        Creates a tool record in the Pinecone index.
        Parameters:
            server_name (str): The name of the server.
            tool_id (str): Unique identifier for the tool.
            tool_name (str): The name of the tool.
            tool_description (str): Description of the tool.
            tools_sample_questions (str): Sample questions for the tool.
            tool_keywords (str): Keywords associated with the tool.
        
        Returns:
            bool: True if the record was successfully created, False otherwise.
        """
        tool_text = f"{server_name} {tool_name} {tool_description} {tool_keywords}"
        try:
            # Generate embeddings for the tool text
            if not self.pc.inference:
                raise ValueError("Inference service is not available in Pinecone client.")
            embeddings = self.pc.inference.embed(
                model="multilingual-e5-large",
                inputs=[tool_text],
                parameters={"input_type": "query"}
            )[0]['values']
        except Exception as e:
            raise ValueError(f"Error generating embeddings: {e}")
        
        try: 
            # Upsert the tool record into the Pinecone index
            self.index.upsert([
                {
                    "id": tool_id,
                    "values": embeddings,
                    "metadata": {
                        "server": server_name,
                        "name": tool_name,
                        "description": tool_description,
                        "sample_questions": tools_sample_questions,
                        "keywords": tool_keywords
                    }
                }])
            logging.info(f"Upserted tool: {tool_name} from server: {server_name}")
            return True
        except Exception as e:
            raise ValueError(f"Error upserting records: {e}")   




    async def get_tools(self, query: str, top_k: int = 10, tool_return_limit: int = 10) -> ToolListResponse:
        """
        Asynchronously retrieves tools based on a query across multiple namespaces.
        Parameters:
            query (str): The search query.  
            top_k (int): The number of top results to return from each namespace.
            tool_return_limit (int): The maximum number of tools to return across all namespaces.
        
        Returns:
            ToolListResponse: A response containing matching tools and execution metadata.
        """
        start_time = time.time()

        # Generate embeddings once and reuse
        embeddings = await self.get_query_embedding(query)
        
        # Search across all namespaces in parallel
        fields = ["server", "name", "description", "sample_questions", "keywords", "toolset"]
        search_tasks = [
            self.search_vector(namespace=namespace, embeddings=embeddings, fields=fields, top_k=top_k) 
            for namespace in self.namespaces
        ]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process results more efficiently - create tools in bulk
        tools = []
        for result_set in results:
            if isinstance(result_set, Exception):
                logging.warning(f"Search error in namespace: {result_set}")
                continue
                
            for hit in result_set:
                metadata = hit.get('metadata', {})  # Updated to use 'metadata' instead of 'fields'
                tool = Tool(
                    score=hit.get('score', 0.0),
                    id=hit.get('id', ''),
                    name=metadata.get('name', ''),
                    description=metadata.get('description', ''),
                    keywords=metadata.get('keywords', '').split(","),
                    sample_questions=metadata.get('sample_questions', '').split(","),
                    server=metadata.get('server', ''),
                    toolset=metadata.get('toolset', '')
                )
                tools.append(tool)

        # Create and optimize ToolListResponse
        tool_list = ToolListResponse(
            query=query, 
            embeddings=embeddings, 
            tools=tools, 
            execution_time=0.0
        )
        tool_list.sort_tools_by_score(reversed=True, limit=tool_return_limit)
        tool_list.execution_time = round((time.time() - start_time) * 1000)
        
        return tool_list