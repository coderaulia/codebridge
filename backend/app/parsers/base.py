"""
CodeBridge V1 - Base Parser Interface
Common dataclasses and abstract interface for deterministic code and schema extraction.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ParsedSymbol(BaseModel):
    name: str
    symbol_type: str = Field(..., description="'function', 'class', 'model', 'table', 'endpoint'")
    start_line: int
    end_line: int
    signature: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ParsedSchemaModel(BaseModel):
    model_name: str
    fields: List[Dict[str, Any]] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = Field(default_factory=list)
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    start_line: int
    end_line: int


class BaseParser(ABC):
    """Abstract base class for all language and schema parsers."""

    @abstractmethod
    def parse(self, code: str, file_path: str = "") -> List[ParsedSymbol]:
        """Parses source code and returns concrete symbol boundaries."""
        pass
