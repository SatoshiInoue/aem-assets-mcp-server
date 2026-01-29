"""FastAPI application for AEM Assets MCP Server"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models import (
    ToolRequest,
    ToolResponse,
    ServerInfo,
)
from app.aem_client import AEMAssetsClient, AEMConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "AEM_BASE_URL",
    "AEM_CLIENT_ID",
    "AEM_CLIENT_SECRET",
]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# Global AEM client
aem_client: AEMAssetsClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global aem_client
    
    # Initialize AEM client with both OAuth and JWT auth
    service_account_json = os.getenv("AEM_SERVICE_ACCOUNT_JSON")
    
    config = AEMConfig(
        base_url=os.getenv("AEM_BASE_URL"),
        client_id=os.getenv("AEM_CLIENT_ID"),
        client_secret=os.getenv("AEM_CLIENT_SECRET"),
        service_account_json_path=service_account_json,
    )
    aem_client = AEMAssetsClient(config)
    
    # Log authentication methods available
    if service_account_json:
        # Check if it's a file path or JSON string
        if os.path.exists(service_account_json):
            logger.info("✅ JWT Service Account auth available (from file: for /api/assets)")
        else:
            # It's a JSON string (Cloud Run environment)
            logger.info("✅ JWT Service Account auth available (from JSON string: for /api/assets)")
    else:
        logger.warning("⚠️  No service account JSON - classic API (/api/assets) will use fallback")
    
    logger.info("✅ OAuth Server-to-Server auth available (for /adobe/* endpoints)")
    
    yield
    
    # Close client on shutdown
    await aem_client.close()


# Create FastAPI app
app = FastAPI(
    title="AEM Assets MCP Server",
    description="Model Context Protocol Server for Adobe Experience Manager Assets Author API",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - returns server info"""
    return ServerInfo()


@app.get("/api/mcp")
async def get_server_info():
    """Get server information"""
    return ServerInfo()


@app.post("/api/mcp", response_model=ToolResponse)
async def call_tool(request: ToolRequest):
    """Execute an MCP tool"""
    tool = request.tool
    args = request.arguments or {}

    try:
        if tool == "list_folders":
            path = args.get("path", "/")
            result = await aem_client.list_folders(path)
            return ToolResponse(result=[folder.model_dump() for folder in result])

        elif tool == "list_published_assets":
            limit = args.get("limit", 100)
            result = await aem_client.get_published_assets(limit)
            return ToolResponse(result=[asset.model_dump() for asset in result])

        elif tool == "search_assets":
            query = args.get("query")
            if not query:
                raise HTTPException(status_code=400, detail="Query parameter is required")
            limit = args.get("limit", 100)
            result = await aem_client.search_assets(query, limit)
            return ToolResponse(result=[asset.model_dump() for asset in result])

        elif tool == "list_assets_by_folder":
            folder_path = args.get("folderPath")
            if not folder_path:
                raise HTTPException(status_code=400, detail="folderPath parameter is required")
            result = await aem_client.get_assets_by_folder(folder_path)
            return ToolResponse(result=[asset.model_dump() for asset in result])

        elif tool == "bulk_update_metadata":
            # Check if it's a single asset or folder
            asset_id = args.get("assetId")
            folder_path = args.get("folderPath")
            metadata = args.get("metadata")
            
            if not metadata:
                raise HTTPException(status_code=400, detail="metadata parameter is required")
            
            if asset_id:
                # Single asset update
                result = await aem_client.update_asset_metadata(asset_id, metadata)
                return ToolResponse(result=result.model_dump())
            elif folder_path:
                # Bulk folder update
                result = await aem_client.bulk_update_folder_metadata(folder_path, metadata)
                return ToolResponse(result=result.model_dump())
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either assetId or folderPath parameter is required"
                )

        elif tool == "list_assets_by_creator":
            created_by = args.get("createdBy")
            if not created_by:
                raise HTTPException(status_code=400, detail="createdBy parameter is required")
            limit = args.get("limit", 100)
            result = await aem_client.get_assets_by_creator(created_by, limit)
            return ToolResponse(result=[asset.model_dump() for asset in result])

        elif tool == "list_all_assets":
            path = args.get("path")
            limit = args.get("limit", 100)
            result = await aem_client.list_assets(path=path, limit=limit)
            return ToolResponse(result=[asset.model_dump() for asset in result])

        elif tool == "get_asset_details":
            asset_id = args.get("assetId")
            if not asset_id:
                raise HTTPException(status_code=400, detail="assetId parameter is required")
            result = await aem_client.get_asset(asset_id)
            return ToolResponse(result=result.model_dump())

        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")

    except HTTPException:
        raise
    except Exception as e:
        return ToolResponse(result=None, error=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "aem-assets-mcp-server"}


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
