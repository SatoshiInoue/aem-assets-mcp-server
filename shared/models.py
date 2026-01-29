"""Pydantic models for request/response validation"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Request model for tool execution"""
    tool: str = Field(..., description="Name of the tool to execute")
    arguments: Optional[Dict[str, Any]] = Field(default={}, description="Tool arguments")


class ToolResponse(BaseModel):
    """Response model for tool execution"""
    result: Any = Field(..., description="Result from tool execution")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class Asset(BaseModel):
    """AEM Asset model"""
    id: str
    path: str
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}
    asset_type: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    published: bool = False
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    modified_by: Optional[str] = None
    modified_at: Optional[str] = None


class Folder(BaseModel):
    """AEM Folder model"""
    id: str
    path: str
    name: str
    title: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    modified_by: Optional[str] = None
    modified_at: Optional[str] = None


class BulkUpdateResult(BaseModel):
    """Result of bulk metadata update"""
    updated: int
    failed: int
    results: List[Dict[str, Any]]


class ServerInfo(BaseModel):
    """Server information"""
    name: str = "aem-assets-mcp-server"
    version: str = "1.0.0"
    description: str = "MCP Server for Adobe Experience Manager Assets Author API"
    tools: List[str] = [
        "list_folders",
        "list_published_assets",
        "search_assets",
        "list_assets_by_folder",
        "bulk_update_metadata",
        "list_assets_by_creator",
        "list_all_assets",
        "get_asset_details"
    ]
