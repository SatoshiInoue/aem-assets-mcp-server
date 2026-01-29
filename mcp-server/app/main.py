"""FastMCP Server for AEM Assets - Model Context Protocol Implementation"""

import asyncio
import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastmcp import FastMCP
from dotenv import load_dotenv

from shared.aem_client import AEMAssetsClient, AEMConfig
from shared.models import Asset, Folder

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("AEM Assets MCP Server")

# Global AEM client - initialize immediately
try:
    logger.info("🚀 Initializing AEM Assets MCP Server...")
    
    # Get environment variables
    base_url = os.getenv("AEM_BASE_URL")
    client_id = os.getenv("AEM_CLIENT_ID")
    client_secret = os.getenv("AEM_CLIENT_SECRET")
    service_account_json = os.getenv("AEM_SERVICE_ACCOUNT_JSON")
    
    # Log environment status (without revealing secrets)
    logger.info(f"📝 Environment check:")
    logger.info(f"   AEM_BASE_URL: {'✅ Set' if base_url else '❌ Missing'}")
    logger.info(f"   AEM_CLIENT_ID: {'✅ Set' if client_id else '❌ Missing'}")
    logger.info(f"   AEM_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Missing'}")
    logger.info(f"   AEM_SERVICE_ACCOUNT_JSON: {'✅ Set' if service_account_json else '❌ Missing'}")
    
    # Initialize AEM client
    config = AEMConfig(
        base_url=base_url,
        client_id=client_id,
        client_secret=client_secret,
        service_account_json_path=service_account_json,
    )
    aem_client = AEMAssetsClient(config)
    logger.info("✅ AEM client initialized successfully")
    
    # Log authentication methods available
    if service_account_json:
        if os.path.exists(service_account_json):
            logger.info("✅ JWT Service Account auth available (from file: for /api/assets)")
        else:
            logger.info("✅ JWT Service Account auth available (from JSON string: for /api/assets)")
    else:
        logger.warning("⚠️  No service account JSON - classic API (/api/assets) will use fallback")
    
    logger.info("✅ OAuth Server-to-Server auth available (for /adobe/* endpoints)")
    logger.info("✅ AEM Assets MCP Server is ready!")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize AEM client: {e}", exc_info=True)
    logger.warning("⚠️  MCP server will start but AEM operations will fail")
    aem_client = None


@mcp.tool()
async def list_folders(path: str = "/") -> List[Dict[str, Any]]:
    """
    List all folders in the specified AEM path.
    
    Args:
        path: The AEM folder path to list (e.g., "/content/dam/"). Defaults to root "/".
    
    Returns:
        List of folder objects with name, path, and metadata.
    """
    if not aem_client:
        raise RuntimeError("AEM client not initialized")
    
    logger.info(f"📁 Listing folders in: {path}")
    folders = await aem_client.list_folders(path)
    
    result = [
        {
            "name": folder.name,
            "path": folder.path,
            "createdBy": folder.created_by,
            "createdAt": folder.created_at.isoformat() if folder.created_at else None,
            "modifiedBy": folder.modified_by,
            "modifiedAt": folder.modified_at.isoformat() if folder.modified_at else None,
        }
        for folder in folders
    ]
    
    logger.info(f"✅ Found {len(result)} folders")
    return result


@mcp.tool()
async def list_assets_by_folder(folder_path: str) -> List[Dict[str, Any]]:
    """
    List all assets in a specific folder using the classic AEM Assets HTTP API.
    
    Args:
        folder_path: The full AEM folder path (e.g., "/content/dam/MyFolder" or "MyFolder").
    
    Returns:
        List of asset objects with name, path, title, and basic metadata.
    """
    if not aem_client:
        raise RuntimeError("AEM client not initialized")
    
    logger.info(f"🖼️  Listing assets in folder: {folder_path}")
    assets = await aem_client.get_assets_by_folder(folder_path)
    
    result = [
        {
            "name": asset.name,
            "path": asset.path,
            "title": asset.title,
            "mimeType": asset.mime_type,
            "size": asset.size,
            "createdBy": asset.created_by,
            "createdAt": asset.created_at.isoformat() if asset.created_at else None,
            "modifiedBy": asset.modified_by,
            "modifiedAt": asset.modified_at.isoformat() if asset.modified_at else None,
        }
        for asset in assets
    ]
    
    logger.info(f"✅ Found {len(result)} assets")
    return result


@mcp.tool()
async def get_asset_details(asset_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific asset, including all metadata.
    
    Args:
        asset_id: The asset path (e.g., "/content/dam/MyFolder/image.jpg" or "MyFolder/image.jpg").
    
    Returns:
        Complete asset details including all metadata fields.
    """
    if not aem_client:
        raise RuntimeError("AEM client not initialized")
    
    logger.info(f"🔍 Getting asset details: {asset_id}")
    asset = await aem_client.get_asset(asset_id)
    
    result = {
        "name": asset.name,
        "path": asset.path,
        "title": asset.title,
        "description": asset.description,
        "mimeType": asset.mime_type,
        "size": asset.size,
        "width": asset.width,
        "height": asset.height,
        "createdBy": asset.created_by,
        "createdAt": asset.created_at.isoformat() if asset.created_at else None,
        "modifiedBy": asset.modified_by,
        "modifiedAt": asset.modified_at.isoformat() if asset.modified_at else None,
        "metadata": asset.metadata or {},
    }
    
    logger.info(f"✅ Retrieved asset details for: {asset.name}")
    return result


@mcp.tool()
async def update_asset_metadata(
    asset_id: str,
    metadata: Dict[str, str]
) -> Dict[str, Any]:
    """
    Update metadata for a specific asset.
    
    Args:
        asset_id: The asset path (e.g., "/content/dam/MyFolder/image.jpg" or "MyFolder/image.jpg").
        metadata: Dictionary of metadata fields to update (e.g., {"dc:title": "New Title", "dc:description": "New Description"}).
    
    Returns:
        Updated asset information with success status.
    """
    if not aem_client:
        raise RuntimeError("AEM client not initialized")
    
    logger.info(f"✏️  Updating metadata for asset: {asset_id}")
    logger.info(f"   Metadata: {metadata}")
    
    success = await aem_client.update_asset_metadata(asset_id, metadata)
    
    if success:
        logger.info(f"✅ Successfully updated metadata for: {asset_id}")
        return {
            "success": True,
            "assetId": asset_id,
            "message": "Metadata updated successfully"
        }
    else:
        logger.error(f"❌ Failed to update metadata for: {asset_id}")
        return {
            "success": False,
            "assetId": asset_id,
            "message": "Failed to update metadata"
        }


@mcp.tool()
async def bulk_update_metadata(
    metadata: Dict[str, str],
    asset_id: Optional[str] = None,
    folder_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Bulk update metadata for multiple assets in a folder or a single asset.
    
    Args:
        metadata: Dictionary of metadata fields to update (e.g., {"dc:description": "New Description"}).
        asset_id: Optional. Single asset path to update (e.g., "/content/dam/MyFolder/image.jpg").
        folder_path: Optional. Folder path to update all assets within (e.g., "/content/dam/MyFolder").
    
    Returns:
        Summary of bulk update operation with success/failure counts.
    """
    if not aem_client:
        raise RuntimeError("AEM client not initialized")
    
    if not asset_id and not folder_path:
        raise ValueError("Either asset_id or folder_path must be provided")
    
    # If asset_id is provided, update single asset
    if asset_id:
        logger.info(f"📝 Updating single asset: {asset_id}")
        return await update_asset_metadata(asset_id, metadata)
    
    # Otherwise, bulk update folder
    logger.info(f"📝 Bulk updating metadata for folder: {folder_path}")
    logger.info(f"   Metadata: {metadata}")
    
    result = await aem_client.bulk_update_folder_metadata(folder_path, metadata)
    
    logger.info(f"✅ Bulk update complete: {result.successful} succeeded, {result.failed} failed")
    
    return {
        "totalAssets": result.total_assets,
        "successful": result.successful,
        "failed": result.failed,
        "errors": result.errors,
    }


@mcp.tool()
def add(a: int, b: int) -> int:
    """Simple test tool - add two numbers together.
    
    Args:
        a: The first number.
        b: The second number.
    
    Returns:
        The sum of the two numbers.
    """
    logger.info(f">>> Tool: 'add' called with numbers '{a}' and '{b}'")
    result = a + b
    logger.info(f"<<< Result: {result}")
    return result


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 MCP server starting on 0.0.0.0:{port}")
    logger.info(f"📡 Transport: streamable-http")
    
    # Use FastMCP's built-in server like in the blog post
    # This is the correct way according to official Cloud Run MCP docs
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
