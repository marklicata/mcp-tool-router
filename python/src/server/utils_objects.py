# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import uuid
from typing import Annotated, Any, Union, Optional, Tuple, List, Dict, Literal
from pydantic.dataclasses import dataclass

@dataclass
class Server:
    """Server object representing a remote or local server."""
    id: uuid.UUID
    name: str
    description: Optional[str] = ""
    url: str = ""
    version: Optional[str] = ""
    release_date: Optional[str] = ""
    is_latest: Optional[bool] = True

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
