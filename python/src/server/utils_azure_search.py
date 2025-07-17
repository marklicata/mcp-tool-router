import configparser, asyncio, logging, json, requests
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from typing import List, Optional
from src.server.utils_core import Server, ToolSearchManager

# Configuration variables from config.ini
config = configparser.ConfigParser()
config.read('python/src/server/data/config.ini')


class AzureSearchManager(ToolSearchManager):
    """Manager for Azure Search and Azure OpenAI embedding operations."""

    def __init__(self):
        """
        Initialize Azure Search and Azure OpenAI embedding clients.
        This constructor reads configuration from 'core_config.ini' and sets up the necessary clients.
        """
        # Azure Foundry configuration
        self.azure_foundry_endpoint = config.get('AzureAI', 'AZURE_FOUNDARY_ENDPOINT')
        self.azure_embedding_model = config.get('AzureAI', 'AZURE_EMBEDDING_MODEL')
        self.azure_embedding_deployment = config.get('AzureAI', 'AZURE_EMBEDDING_DEPLOYMENT')
        self.azure_embedding_dimensions = config.getint('AzureAI', 'AZURE_EMBEDDING_DIMENSIONS', fallback=1536)
        self.azure_api_version = config.get('AzureAI', 'AZURE_API_VERSION')

        # Set attributes expected by the base class
        self.embedding_model = self.azure_embedding_model
        self.embedding_dimensions = self.azure_embedding_dimensions

        # Azure Search configuration
        self.azure_search_endpoint = config.get('AzureSearch', 'AZURE_SEARCH_ENDPOINT')
        self.azure_search_index_name = config.get('AzureSearch', 'AZURE_SEARCH_INDEX_NAME')

        # Azure authentication
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

        # Initialize Azure OpenAI embedding model
        self.embedding_client = AzureOpenAI(
            azure_endpoint=self.azure_foundry_endpoint,
            azure_deployment=self.azure_embedding_deployment,
            api_version=self.azure_api_version,
            azure_ad_token_provider=token_provider,
        )

        # Initialize tool search client
        self.azure_search_client = SearchClient(
            endpoint=self.azure_search_endpoint,
            index_name=self.azure_search_index_name,
            credential=credential
        )
        super().__init__(embedding_client=self.embedding_client, search_client=self.azure_search_client)


    async def update_server(self, server: Server):
        # Step 1: Fetch the tools by calling list_tools on the server
        # Step 2: Create the server object Server(id, name, url, location)
        # Step 3: Loop through each tool and create a Tool object Tool(server, toolset, id, name, description, tool_vector)
        # Step 4: Embed the tool description using Azure OpenAI embedding model (tool_vector)
        # Step 5: Upload the tool document to Azure Search index
        pass


    async def update_all_servers(self):
        # Step 1: Fetch the servers by calling the MCP registry.
        # Step 2: Create the server object Server(id, name, url, location).
        # Step 3: Loop through each tool and create a Tool object Tool(server, toolset, id, name, description, tool_vector).
        # Step 4: Embed the tool description using Azure OpenAI embedding model (tool_vector).
        # Step 5: Erase the existing Azure Search index.
        # Step 6: Recreate the Azure Search index and upload the servers and tools.
        pass


    async def create_tools_from_file(self, file_path: str):
        """
        Create tools from a JSON file and upload them to Azure Search.
        This function reads a JSON file containing MCP server information, extracts tool metadata,
        and uploads each tool as a document to the Azure Search index.
        It skips tools associated with the "VSCode" server.
        """

        if not file_path or not file_path.endswith('.json'):
            raise ValueError("Invalid file path. Must be a JSON file.")

        with open(file_path, 'r', encoding='utf-8') as f:
            mcp_servers = json.load(f)
        
        for server in mcp_servers.get("servers", []):
            server_name = server.get("name", "")
            _server = Server(
                id=f"{server_name}.remote",
                name=server_name,
                url=server.get("url", ""),
                location=server.get("location", "remote")  # Default to 'remote' if not specified
            )
            tool_sets = server.get("toolsets", [])
            for tool_set in tool_sets:
                toolset_name = tool_set.get("name", "")
                tools = tool_set.get("tools", [])
                for tool in tools:
                    _tool = {
                        'id': f"{_server.name}_{toolset_name}_{tool.get('name', '')}",
                        'server': _server.name,
                        'toolset':  toolset_name,
                        'name': tool.get("name", ""),
                        'description': f"{tool.get('description', '')} Keywords: {', '.join(tool.get('keywords', []))}. Examples: {'; '.join(tool.get('sample_questions', []))}",
                        'tool_vector': await super().embed_text(text=f"Server name: {server_name} {f'Toolset name: {toolset_name}' if toolset_name else ''} Tool name: {tool.get('name', '')}: Description: {tool.get('description', '')}.")
                    }
                    result = await super().upload_document(
                        client=self.azure_search_client,
                        document=_tool
                        )
                    if result is None or not result[0].succeeded:
                        logging.error(f"Failed to upload tool {tool.get('name', '')} to Azure Search.")
                    else:
                        logging.info(f"Successfully uploaded tool {tool.get('name', '')} to Azure Search.")



            ## OpenAPI specification for the MCP server
            # {
            #     "openapi": "3.0.0",
            #     "info": {
            #         "title": "Demo MCP server",
            #         "description": "Very basic MCP server that exposes mock tools and prompts.",
            #         "version": "1.0"
            #     },
            #     "servers": [
            #         {
            #         "url": "https://my-mcp-server.contoso.com"
            #         }
            #     ]
            # }
            
            # {
            #   "servers": [
            #     {
            #       "id": "a5e8a7f0-d4e4-4a1d-b12f-2896a23fd4f1",
            #       "name": "io.modelcontextprotocol/filesystem",
            #       "description": "Node.js server implementing Model Context Protocol (MCP) for filesystem operations.",
            #       "repository": {
            #         "url": "https://github.com/modelcontextprotocol/servers",
            #         "source": "github",
            #         "id": "b94b5f7e-c7c6-d760-2c78-a5e9b8a5b8c9"
            #       },
            #       "version_detail": {
            #         "version": "1.0.2",
            #         "release_date": "2023-06-15T10:30:00Z",
            #         "is_latest": true
            #       }
            #     }
            #   ],
            #   "next": "https://registry.modelcontextprotocol.io/servers?offset=50",
            #   "total_count": 1
            # }