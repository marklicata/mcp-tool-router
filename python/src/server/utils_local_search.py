import configparser, asyncio, logging, json
from typing import List, Optional
from dataclasses import dataclass
import sqlite_vec, sqlite3, struct
from src.server.utils_core import Server, ToolResult, ToolListResult
from src.server.utils_azure_search import AzureSearchManager

# Configuration variables from config.ini
config = configparser.ConfigParser()
config.read('python/src/server/data/config.ini')

class LocalSearchManager(AzureSearchManager):
    """Manager for local search operations."""

    def __init__(self):
        super().__init__()
        self.db = sqlite3.connect("my-vectors.sqlite")

        ####
        # TODO: Allow clients to pass their own embedding clients if they want to host embedding models locally.
        # Currently, this class uses the Azure OpenAI embedding client for local search.
        ####
        self.embedding_model = config.get('LocalEmbeddings', 'LOCAL_EMBEDDING_MODEL')
        self.embedding_deployment = config.get('LocalEmbeddings', 'LOCAL_EMBEDDING_DEPLOYMENT')
        self.embedding_dimensions = config.getint('LocalEmbeddings', 'LOCAL_EMBEDDING_DIMENSIONS', fallback=1536)
        self.api_version = config.get('LocalEmbeddings', 'LOCAL_API_VERSION')
    
   
    async def search(self, query:str, top_k:int=5) -> ToolListResult:
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)

        query_vec = await super().embed_text(text=query)
        query_vec_serialized = struct.pack(f"{len(query_vec)}f", *query_vec)
        results = self.db.execute(
            """
            SELECT id, server, toolset, name, description, vec_distance_cosine(embedding, ?) AS distance
            FROM vec_items
            ORDER BY distance
            """,
            (query_vec_serialized,)
        ).fetchmany(size=top_k)

        local_result_list = ToolListResult(tools=[], query=query)
        for t in results:
            _tool = ToolResult(
                score=t[5],
                server=Server(id=t[0], name=t[1], location= "local"),
                toolset=t[2],
                id=f"{t[1]}_{t[2]}_{t[3]}",
                name=f"{t[1]}.{t[3]}",
                endpoint="",
                kwargs={}
            )
            local_result_list.tools.append(_tool)
        if len(local_result_list.tools) == 0:
            logging.info("No results found.")
        return local_result_list
    


    async def create_tools_from_file(self, file_path: str):
        """
        Create tools from a JSON file and upload them to the local SQLite database.
        This function reads a JSON file containing MCP server information, extracts tool metadata,
        and uploads each tool as a document to the local SQLite database.
        It skips tools associated with the "VSCode" server.
        
        Args:
            file_path (str): Path to the JSON file containing MCP server information.
        
        Returns:
            None: If the operation is successful, or an error message if it fails.
        """
        
        def serialize_f32(vector: List[float]) -> bytes:
            return struct.pack(f"{len(vector)}f", *vector)
        try: 
            self.db.enable_load_extension(True)
            sqlite_vec.load(self.db)
            self.db.enable_load_extension(False)
            logging.info("Loaded sqlite_vec extension successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error loading sqlite_vec extension: {e}")
            return
        table_name = "vec_items"
        table_exists = self.db.execute(f"SELECT EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='{table_name}');")
        if table_exists.fetchone()[0] == 1:
            self.db.execute("DROP TABLE vec_items")
            logging.info("Dropped existing table vec_items.")

        self.db.execute(f"""
                CREATE VIRTUAL TABLE vec_items USING vec0(
                id INTEGER PRIMARY KEY,
                server TEXT,
                toolset TEXT,
                name TEXT,
                description TEXT,
                embedding FLOAT[1536]
                );"""
            )
        

        file_path = 'python/src/server/data/mcp_servers.json'
        with open(file_path, 'r') as f:
            mcp_servers = json.load(f)
        
        i = 1
        for server in mcp_servers.get("servers", []):
            server_name = server.get("server", "")
            tool_sets = server.get("toolsets", [])
            for tool_set in tool_sets:
                toolset_name = tool_set.get("name", "")
                tools = tool_set.get("tools", [])
                for tool in tools:
                    name = tool.get("name", "")
                    id = f"{server_name}_{toolset_name}_{name}"
                    description = tool.get("description", "")
                    keywords = tool.get("keywords", [])
                    example_questions = tool.get("examples", [])
                    vectors = await super().embed_text(text=f"Server name: {server_name} Toolset name: {toolset_name} Tool name: {name}: Description: {description}. Keywords: {', '.join(keywords)}. Examples: {'; '.join(example_questions)}")
                    query_bytes = struct.pack(f"{len(vectors)}f", *vectors)
                    i += 1
                    try:
                        self.db.execute("INSERT INTO vec_items (id, server, toolset, name, description, embedding) VALUES (?, ?, ?, ?, ?, ?)", (i, server_name, toolset_name, name, description, query_bytes))
                    except sqlite3.Error as e:
                        logging.error(f"Error inserting vector for tool {name}: {e}")
            self.db.commit()
        logging.info("Tools created and inserted into the database.")