# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import asyncio, logging
from typing import Annotated, Any, Union, Optional, Tuple, List, Dict
from datetime import datetime
from pydantic.dataclasses import dataclass
from pinecone import Pinecone

Doc = lambda s: s  # Placeholder for Doc metadata


@dataclass
class Tool:
    score: Annotated[float, Doc("Score of the tool based on relevance or other criteria")]
    id: Annotated[str, Doc("Unique identifier for the tool")]
    name: Annotated[str, Doc("The name of the tool")]
    description: Annotated[str, Doc("A brief description of the tool")]
    keywords: Annotated[list[str], Doc("Keywords associated with the tool")]
    sample_questions: Optional[list[str]]   
    server: Annotated[str, Doc("The MCP server hosting the tool")]
    toolset: Annotated[Optional[str], Doc("The toolset this tool belongs to, if any")]

@dataclass
class ToolListResponse:
    embeddings: Annotated[list[float], Doc("The embeddings for the query used to retrieve the tools")]
    tools: Annotated[list[Tool], Doc("A list of tools")]
    execution_time: Annotated[float, Doc("Latency of the tool list retrieval in milliseconds")]
    query: Optional[str] = None  # Add the original query for cache purposes

    def sort_tools_by_score(self, reversed: bool = False, limit: int = 10) -> None:
        """
        Sorts the tools in the list by their score.

        Parameters:
            reversed (bool): If True, sorts in descending order; otherwise, ascending.
            limit (int): The maximum number of tools to return after sorting.

        Returns:
            None: The tools are sorted in place.
        """
        self.tools.sort(key=lambda x: x.score, reverse=reversed)
        self.tools = self.tools[:limit]