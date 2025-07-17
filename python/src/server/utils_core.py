# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import asyncio, logging
from typing import Annotated, Any, Union, Optional, Tuple, List, Dict, Literal
from pydantic.dataclasses import dataclass
import configparser, asyncio, logging, json
from azure.search.documents import SearchClient
from typing import List, Optional

# Configuration variables from config.ini
config = configparser.ConfigParser()
config.read('python/src/server/data/config.ini')

Doc = lambda s: s  # Placeholder for Doc metadata

class Server:
    """Represents a server with its metadata."""
    
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

class ToolResult:
    """Result object for a single tool with optional metadata."""
    def __init__(
        self,
        score: float,
        server: Server,
        toolset: Optional[str],
        id: str,
        name: str,
        endpoint: str,
        kwargs: Dict[str, Any]
    ):
        self.score = score
        self.server = server
        self.toolset = toolset
        self.id = id
        self.name = name
        self.endpoint = endpoint
        self.kwargs = kwargs

class ToolListResult:
    """Result object for tool list with optional query for future caching purposes."""
    def __init__(
        self,
        query: str = "",
        tools: List[ToolResult] = []
    ):
        self.query = query
        self.tools = tools


class ToolSearchManager:
    """Manager for Azure Search and Azure OpenAI embedding operations."""

    def __init__(self, embedding_client, search_client: SearchClient = None):
        if embedding_client is None:
            raise ValueError("Embedding client must be provided or initialized.")
        else:
            self.embedding_client = embedding_client

        if search_client is None:
            raise ValueError("Search client must be provided or initialized.")
        else:
            self.search_client = search_client


    async def embed_text(self, text) -> List[float]:
        """
        Embed text using Azure OpenAI embedding model.
        Args:
            text (str): The text to embed.
        Returns:
            List[float]: The embedding vector for the text.
        """
        try:
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=[text],
                dimensions=self.embedding_dimensions
            )
            #     dimensions=self.embedding_dimensions
            # )
            return response.data[0].embedding
        except Exception as e:
            logging.error("Error embedding text")
            return None

    async def upload_document(self, client: SearchClient, document: dict):
        """
        Upload a document to the specified Azure Search index.
        Args:
            client (SearchClient): The Azure Search client to use for uploading.
            document (dict): The document to upload, must match the index schema.

        Returns:
            UploadResult: The result of the upload operation.
        """
        try:
            result = client.upload_documents(documents=[document])
            return result
        except Exception as e:
            logging.error(f"Error uploading document: {e}")
            return None

    async def search(self, client: SearchClient, search_text: str, top_k: int = 10):
        """
        Search for documents in the specified Azure Search index.
        Args:
            client (SearchClient): The Azure Search client to use for searching.
            search_text (str): The text to search for in the index.
            top_k (int): The number of top results to return.
        Returns:
            SearchResults: The search results.
        """
        try:
            results = client.search(search_text=search_text, top=top_k)
            return results
        except Exception as e:
            logging.error(f"Error searching documents: {e}")
            return None
    
    async def clear_index(self, client: SearchClient):
        """
        Clear all documents from the specified Azure Search index.
        Args:
            client (SearchClient): The Azure Search client to use for clearing the index.
        Returns:
            None: If the operation is successful, or an error message if it fails.
        """
        try:
            # First, retrieve all document IDs
            ids = client.search("*", select=["id"])
            ids_to_delete = [doc["id"] for doc in ids]
            if not ids_to_delete:
                logging.info("No documents to delete.")
                return None
            # Now, delete documents in bulk
            result = client.delete_documents(documents=[{"id": id} for id in ids_to_delete])
            return result
        except Exception as e:
            logging.error(f"Error clearing index: {e}")
            return None