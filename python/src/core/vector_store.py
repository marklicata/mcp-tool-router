import asyncio, logging
from typing import Annotated, Any, Union, Optional, Tuple, List, Dict
from datetime import datetime
from pinecone import Pinecone

class VectorStore:
    """
    A base class for vector stores using Pinecone for similarity search.
    Provides methods for initializing the store, generating embeddings, and searching vectors.
    """
    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        spec: dict,
    ):
        self.api_key = api_key
        self.environment = environment
        self.spec = spec
        self.index_name = index_name
        self._embedding_cache = {}  # Add embedding cache
        
        try:
            self.pc = Pinecone(api_key=api_key, environment=environment, spec=spec)
            self.index = self.pc.Index(index_name)
            self.namespaces = list(self.index.describe_index_stats()['namespaces'].keys())
            if len(self.namespaces) == 1 and self.namespaces[0] == "":
                self.namespaces = ["__default__"]
        except Exception as e:
            raise ValueError(f"Error initializing Pinecone: {e}")
    

    async def get_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for the query text with caching.
        If the query is already cached, it returns the cached embedding.

        Parameters:
            query (str): The query text to generate an embedding for.
        
        Returns:
            list[float]: The embedding vector for the query.
        """
        # Check cache first
        if query in self._embedding_cache:
            return self._embedding_cache[query]
            
        try:
            embedding_response = await asyncio.to_thread(
                self.pc.inference.embed,
                model="multilingual-e5-large",
                inputs=[query],
                parameters={"input_type": "query"}
            )
            embeddings = embedding_response[0]['values']
            
            # Cache the result (limit cache size to prevent memory issues)
            if len(self._embedding_cache) < 1000:
                self._embedding_cache[query] = embeddings
                
            return embeddings
        except Exception as e:
            raise ValueError(f"Error generating query embedding: {e}")
    

    async def search_vector(self, namespace: str = "", query: str = "", embeddings: list = [], fields: list = [], top_k: int = 10) -> List[Dict]:
        """
        Asynchronously searches for vectors in a specific namespace with improved performance.

        Parameters:
            namespace (str): The namespace to search in. Defaults to "__default__".
            query (str): The query text to search for.
            embeddings (list): Precomputed embeddings to use for the search.
            fields (list): Fields to include in the search results.
            top_k (int): Number of top results to return.

        Returns:
            List[Dict]: A list of search results, each containing metadata and vector information.
        """
        try:
            # Use embeddings directly if provided, otherwise generate them
            if not embeddings and query:
                embeddings = await self.get_query_embedding(query)
            
            search_results = await asyncio.to_thread(
                self.index.query,
                namespace=namespace,
                vector=embeddings,
                top_k=top_k,
                include_metadata=True
            )
            return search_results.get('matches', [])
            
        except Exception as e:
            # Fallback to inference-based search if available
            try:
                search_results = await asyncio.to_thread(
                    self.index.search,
                    namespace=namespace,
                    query={
                        "top_k": top_k,
                        "inputs": {"text": query}
                    },
                    fields=fields,
                )
                return search_results['result']['hits']
            except Exception as e2:
                raise ValueError(f"Error querying records: {e2}")