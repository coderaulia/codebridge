"""
CodeBridge V1 - Data Models & Transfer Schemas
Strict Pydantic v2 validation models for database records and API requests/responses.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProviderSettings(BaseModel):
    id: str = "active_config"
    provider_type: str = Field("ollama", description="ollama, lmstudio, deepseek, openrouter, openai")
    base_url: str = Field(..., description="Base API endpoint URL")
    api_key: Optional[str] = Field("", description="Optional API key")
    model_name: str = Field(..., description="Target model name")
    temperature: float = Field(0.2, ge=0.0, le=2.0)


class ConnectionTestRequest(BaseModel):
    provider_type: str
    base_url: str
    api_key: Optional[str] = ""
    model_name: str


class ConnectionTestResponse(BaseModel):
    success: bool
    latency_ms: Optional[float] = None
    message: str
    available_models: Optional[List[str]] = None


class ProjectBase(BaseModel):
    name: str
    source_type: str = Field(..., description="'local' or 'github'")
    source_path: str


class ProjectCreate(ProjectBase):
    github_token: Optional[str] = None


class Project(ProjectBase):
    id: str
    executive_summary: Optional[str] = None
    created_at: str
    updated_at: str


class SymbolRecord(BaseModel):
    id: str
    file_id: str
    name: str
    symbol_type: str  # 'function', 'class', 'model', 'table', 'endpoint'
    start_line: int
    end_line: int
    signature: Optional[str] = None
    parameters_json: Optional[str] = None


class FileRecord(BaseModel):
    id: str
    project_id: str
    relative_path: str
    file_type: str  # 'code', 'schema', 'config', 'doc'
    language: str
    size_bytes: int
    plain_summary: Optional[str] = None
    business_domain: Optional[str] = None


class FileDetail(FileRecord):
    content: str
    symbols: List[SymbolRecord] = []


class BusinessDomainGroup(BaseModel):
    domain_name: str
    description: Optional[str] = None
    files: List[FileRecord] = []


class TranslationRequest(BaseModel):
    file_id: str
    start_line: int
    end_line: int
    selected_code: str
    surrounding_context: Optional[str] = None


class TranslationBreakdown(BaseModel):
    plain_summary: str
    inputs_and_parameters: str
    outputs_and_effects: str
    business_rule_tie_in: str
    mermaid_diagram: Optional[str] = None
    cached: bool = False
