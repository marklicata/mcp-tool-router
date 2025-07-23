import re, configparser, logging, json
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from typing import List, Dict, Any
from utils_objects import Tool

# Configuration variables from config.ini
config = configparser.ConfigParser()
# config.read('data/config.ini')
config.read('python/src/server/data/config.ini')


class AzureSearchManager():
    """Manager for Azure Search and Azure OpenAI embedding operations."""

    def __init__(self):
        """
        Initialize Azure Search and Azure OpenAI embedding clients.
        This constructor reads configuration from 'core_config.ini' and sets up the necessary clients.
        """
        self.type = "remote"
        # Azure Foundry configuration
        self.azure_foundry_endpoint = config.get('AzureAI', 'AZURE_FOUNDARY_ENDPOINT')
        self.azure_embedding_model = config.get('AzureAI', 'AZURE_EMBEDDING_MODEL')
        self.azure_embedding_deployment = config.get('AzureAI', 'AZURE_EMBEDDING_DEPLOYMENT')
        self.azure_embedding_dimensions = config.getint('AzureAI', 'AZURE_EMBEDDING_DIMENSIONS', fallback=1536)
        self.azure_api_version = config.get('AzureAI', 'AZURE_API_VERSION')

        # Azure Search configuration
        self.azure_search_endpoint = config.get('AzureSearch', 'AZURE_SEARCH_ENDPOINT')
        self.azure_search_index_name = config.get('AzureSearch', 'AZURE_SEARCH_INDEX_NAME')

        # Azure Auth configuration
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

        # Initialize Azure OpenAI embedding model
        self.embedding_client = AzureOpenAI(
            azure_endpoint=self.azure_foundry_endpoint,
            azure_deployment=self.azure_embedding_deployment,
            api_version=self.azure_api_version,
            azure_ad_token_provider=token_provider,
        )

        # Initialize Azure Search client
        self.azure_search_client = SearchClient(
            endpoint=self.azure_search_endpoint,
            index_name=self.azure_search_index_name,
            credential=credential
        )


    async def create_text_embedding(self, text) -> List[float]:
        """
        Embed text using Azure OpenAI embedding model.
        Args:
            text (str): The text to embed.
        Returns:
            List[float]: The embedding vector for the text.
        """
        try:
            response = self.embedding_client.embeddings.create(
                model=self.azure_embedding_model,
                input=[text],
                dimensions=self.azure_embedding_dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error("Error embedding text")
            return None


    async def perform_azure_search(self, search_text: str, top_k: int = 10):
        """
        Performs a hybrid search for documents in the specified Azure Search index.
        Args:
            search_text (str): The text to search for in the index.
            top_k (int): The number of top results to return.
        Returns:
            SearchResults: The search results.
        """
        try:
            results = self.azure_search_client.search(
                search_text=search_text,
                vector_queries=[VectorizedQuery(
                    vector=await self.create_text_embedding(text=search_text),
                    k_nearest_neighbors=top_k,
                    fields="tool_vector"
                )],
                query_type="semantic",
                semantic_configuration_name="default",
                select=["server", "toolset", "name", "description"],
                top=top_k
            )
            return results
        except Exception as e:
            logging.error(f"Error searching documents: {e}")
            return None
    

    async def clear_azure_search_index(self):
        """
        Clear all documents from the specified Azure Search index.
        Args:
            client (SearchClient): The Azure Search client to use for clearing the index.
        Returns:
            None: If the operation is successful, or an error message if it fails.
        """
        try:
            # First, retrieve all document IDs
            results = self.azure_search_client.search(
                search_text="*",
                select=["id"]
            )
            ids_to_delete = [doc['id'] for doc in results]
        except Exception as e:
            logging.error(f"Error retrieving documents for clearing index: {e}")
            ids_to_delete = []

        if not ids_to_delete or len(ids_to_delete) == 0:
            logging.info("No documents to delete.")
            return None

        # Now, delete documents in bulk
        try:
            result = self.azure_search_client.delete_documents(documents=[{"id": id} for id in ids_to_delete])
            return result
        except Exception as e:
            logging.error(f"Error deleting documents from index: {e}")
            return None
        

    async def create_tools_from_file(self, file_path: str) -> bool:
        """
        Create tools from a JSON file and upload them to Azure Search.
        This function reads a JSON file containing MCP server information, extracts tool metadata, and uploads each tool as a document to the Azure Search index.

        Args:
            file_path (str): The path to the JSON file containing MCP server information.
        Returns:
            bool: True if the operation is successful, False otherwise.
        """

        if not file_path or not file_path.endswith('.json'):
            raise ValueError("Invalid file path. Must be a JSON file.")

        with open(file_path, 'r', encoding='utf-8') as f:
            mcp_servers = json.load(f)

        # TEMPORARY: List of servers with more than 5 tools to limit noise in the search index
        servers_with_more_than_5_tools = ['GitHub', 'Azure', 'VSCode', 'ActionKitbyParagon', 'AlibabaCloudOPS', 'AlibabaCloudRDS', 'AllVoiceLab', 'ApacheIoTDB', 'AqaraMCPServer', 'Auth0', 'AWS', 'BoostSpace', 'Campertunity', 'Cloudinary', 'CodeLogic', 'CoinGecko', 'DevRev', 'Drata', 'DumplingAI', 'fetchSERP', 'FluidAttacks', 'Globalping', 'Hiveflow', 'HubSpot', 'Hunter', 'Hyperbolic', 'Hyperbrowser', 'IntegrationApp', 'JFrog', 'Klaviyo', 'klusterai', 'LaunchDarkly', 'LINE', 'Linear', 'Lingodev', 'Liveblocks', 'Logfire', 'MagicMealKits', 'Memgraph', 'Milvus', 'NanoVMs', 'Netdata', 'NormanFinance', 'Notion', 'Nutrient', 'Octagon', 'OctoEverywhere', 'ONLYOFFICEDocSpace', 'OpenSearch', 'PlayCanvas', 'Pluggedin', 'PortIO', 'Putio', 'Rember', 'Riza', 'RobloxStudio', 'RootSignals', 'Shortcut', 'SonarQube', 'Sophtron', 'Tako', 'ThoughtSpot', 'Tianji', 'TradeAgent', 'Twilio', 'UnifAI', 'Upstash', 'WaveSpeed', 'YepCode', 'Yunxin', 'Zapier', 'ZIZAI Recruitment', 'OpsLevel', 'SmoothOperator', 'TextIn']

        for server in mcp_servers.get("servers", []):
            if server.get("name") in servers_with_more_than_5_tools:
                toolset = await self.create_tool_dictionaries(server)
                self.azure_search_client.upload_documents(documents=[tool for tool in toolset])
                logging.info(f"Uploaded {len(toolset)} tools for server '{server.get('name')}' to Azure Search index '{self.azure_search_index_name}'.")
        return True


    async def create_tool_dictionaries(self, server:dict) -> List[Dict[str, Any]]:
        """
        Create a list of tool dictionaries from the server information.
        Args:
            server (dict): The server information containing tools.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing tools.
        """
        def clean_string(s):
            """Removes special characters that the Azure Search index key does not support."""
            return re.sub(r'[^a-zA-Z0-9_\-]', '', s)

        tools_to_return = []
        server_name = server.get("name", "")
        toolsets = server.get("toolsets", [])
        for toolset in toolsets:
            tools = toolset.get("tools", [])
            tools_to_return.append([
                Tool(
                    id=f"{server_name}_{toolset.get('name', '')}_{tool.get('name', '')}",
                    server=server_name,
                    toolset=toolset.get("name", ""),
                    name=tool.get("name", ""),
                    description=f"{tool.get('description', '')} Keywords: {', '.join(tool.get('keywords', []))}. Examples: {'; '.join(tool.get('sample_questions', []))}",
                    tool_vector=await self.create_text_embedding(text=f"Server name: {server_name} Tool name: {tool.get('name', '')}: Description: {tool.get('description', '')}.")
                ) for tool in tools])
        return tools_to_return