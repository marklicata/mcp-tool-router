# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from typing import Annotated, Any, Union, Optional, Tuple, List, Dict, Literal
from pydantic.dataclasses import dataclass


class VectorStoreManager:
    """Manager for vector store operations."""
    def __init__(self, type: Literal["remote", "local"]):
        if type not in ["remote", "local"]:
            raise ValueError("Type must be either 'remote' or 'local'")
        self.type = type


    async def create_tool(self, server_id: str, tool: Any):
        # Step 1: Create the server object Server(id, name, url, location)
        # Step 2: Embed the tool description using Azure OpenAI embedding model (tool_vector)
        # Step 3: Create the Tool object
        # Step 4: Upload the tool document to Azure Search index
        pass

    async def update_tools_by_server_id(self, server_id: str):
        # Step 1: Fetch the tools by calling list_tools on the server
        # Step 2: Create the server object Server(id, name, url, location)
        # Step 3: Loop through each tool and create a Tool object Tool(server, toolset, id, name, description, tool_vector)
        # Step 4: Embed the tool description using Azure OpenAI embedding model (tool_vector)
        # Step 5: Upload the tool document to Azure Search index
        pass

    async def update_tools_on_all_servers(self):
        # Step 1: Fetch the servers by calling the MCP registry.
        # Step 2: Create the server object Server(id, name, url, location).
        # Step 3: Loop through each tool and create a Tool object Tool(server, toolset, id, name, description, tool_vector).
        # Step 4: Embed the tool description using Azure OpenAI embedding model (tool_vector).
        # Step 5: Erase the existing Azure Search index.
        # Step 6: Recreate the Azure Search index and upload the servers and tools.
        pass

    async def create_tools_from_endpoint(self, endpoint: str):
        # Step 1: Fetch the tools by calling list_tools on the server endpoint.
        # Step 2: Create the server object Server(id, name, url, location).
        # Step 3: Loop through each tool and create a Tool object Tool(server, toolset, id, name, description, tool_vector).
        # Step 4: Embed the tool description using Azure OpenAI embedding model (tool_vector).
        # Step 5: Upload the tool document to Azure Search index.
        pass


class Server:
    """Server object representing a remote or local server."""
    
    def __init__(self, id: str, name: str, url: Optional[str] = None, location: Literal["remote", "local"] = "remote"):
        if not id or id == "":
            raise ValueError("Server ID cannot be empty")
        self.id = id

        if not name or name == "":
            raise ValueError("Server name cannot be empty")
        self.name = name
        
        if location not in ["remote", "local"]:
            raise ValueError("Server location must be either 'remote' or 'local'")
        self.location = location
        
        # Handle URL validation - allow None, empty string, or valid URLs
        if url is None or url == "":
            self.url = url
        elif not url.startswith(("http://", "https://")):
            # If URL is provided but doesn't start with http/https, add https://
            self.url = "https://" + url
            if not self.url.endswith("/"):
                self.url += "/"
        else:
            # URL already starts with http/https
            self.url = url
            if not self.url.endswith("/"):
                self.url += "/"

@dataclass
class Tool:
    """Tool object representing a tool on a server."""
    tool_vector: List[float]
    id: str = ""
    server: str = ""
    toolset: Optional[str] = None
    name: str = ""
    description: str = ""
    score: Optional[float] = 0.0

@dataclass
class ToolResults():
    """Results of tool execution."""
    execution_time: float = 0.0
    tools: List[Tool] = None
    kwargs: Dict[str, Any] = None
