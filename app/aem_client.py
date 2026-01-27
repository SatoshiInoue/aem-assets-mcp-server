"""AEM Assets API Client with OAuth Server-to-Server Authentication"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.models import Asset, Folder, BulkUpdateResult
from app.constants import AEM_API_ENDPOINT, AEM_FOLDERS_ENDPOINT, ADOBE_IMS_TOKEN_ENDPOINT, AEM_SCOPES

logger = logging.getLogger(__name__)


class AEMConfig:
    """AEM Configuration"""
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = AEM_API_ENDPOINT
        self.folders_endpoint = AEM_FOLDERS_ENDPOINT
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = AEM_SCOPES
        self.ims_token_endpoint = ADOBE_IMS_TOKEN_ENDPOINT


class AEMAssetsClient:
    """Client for AEM Assets Author API with automatic token refresh"""

    def __init__(self, config: AEMConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _get_access_token(self) -> str:
        """
        Obtain an access token from Adobe IMS using OAuth Server-to-Server credentials.
        Based on: https://experienceleague.adobe.com/en/docs/experience-manager-learn/cloud-service/aem-apis/openapis/invoke-api-using-oauth-s2s
        """
        logger.info("Fetching new access token from Adobe IMS")
        
        try:
            response = await self.client.post(
                self.config.ims_token_endpoint,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "scope": self.config.scopes,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Store the access token
            self.access_token = data["access_token"]
            
            # Calculate expiration time (default to 1 hour, refresh 5 minutes early)
            expires_in = data.get("expires_in", 3600)  # seconds
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info(f"Access token obtained, expires in {expires_in} seconds")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to obtain access token: {str(e)}")
            raise Exception(f"Failed to authenticate with Adobe IMS: {str(e)}")

    async def _ensure_valid_token(self) -> str:
        """Ensure we have a valid access token, refreshing if necessary"""
        if not self.access_token or not self.token_expires_at:
            # No token yet, fetch one
            return await self._get_access_token()
        
        if datetime.now() >= self.token_expires_at:
            # Token expired or about to expire, refresh it
            logger.info("Access token expired, refreshing...")
            return await self._get_access_token()
        
        # Token is still valid
        return self.access_token

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        use_folders_api: bool = False,
        **kwargs
    ) -> httpx.Response:
        """Make an authenticated request to AEM API"""
        # Ensure we have a valid token
        access_token = await self._ensure_valid_token()
        
        # Build full URL - use folders endpoint or assets endpoint
        if use_folders_api:
            url = f"{self.config.base_url}{self.config.folders_endpoint}{endpoint}"
        else:
            url = f"{self.config.base_url}{self.config.api_endpoint}{endpoint}"
        
        # Add authentication headers
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {access_token}",
            "x-api-key": self.config.client_id,
            "Content-Type": "application/json",
        })
        
        logger.debug(f"{method} {url}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def list_folders(self, path: str = "/") -> List[Folder]:
        """List folders in a given path"""
        try:
            response = await self._make_request(
                "GET",
                "",  # Empty - the folders_endpoint is already complete
                use_folders_api=True,
                params={"path": path, "limit": 100}
            )
            data = response.json()
            
            # Optional: Log response for debugging
            logger.debug(f"Folders API response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

            # AEM Folders API uses 'children' array
            items = data.get("children", [])
            
            logger.info(f"Found {len(items)} folders in response")
            
            folders = []
            
            for item in items:
                logger.debug(f"Processing folder: {item.get('name')}")
                folders.append(Folder(
                    id=item.get("folderId", ""),  # AEM uses 'folderId' not 'id'
                    path=item.get("path", ""),
                    name=item.get("name", ""),
                    title=item.get("title"),
                    created_at=item.get("createdAt") or item.get("created"),
                    modified_at=item.get("modifiedAt") or item.get("modified"),
                ))
            
            return folders
        except Exception as e:
            raise Exception(f"Failed to list folders: {str(e)}")

    async def list_assets(
        self,
        path: Optional[str] = None,
        published: Optional[bool] = None,
        created_by: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100
    ) -> List[Asset]:
        """List all assets with optional filtering"""
        try:
            params: Dict[str, Any] = {"limit": limit}

            if path:
                params["path"] = path
            if search_query:
                params["fulltext"] = search_query

            response = await self._make_request("GET", "", params=params)
            data = response.json()

            items = data.get("items", []) or data.get("entities", [])

            # Apply filters
            if published is not None:
                items = [
                    item for item in items
                    if (item.get("published") or item.get("dam:published")) == published
                ]

            if created_by:
                items = [
                    item for item in items
                    if (item.get("createdBy") or item.get("dc:creator")) == created_by
                ]

            assets = [self._map_asset(item) for item in items]
            return assets

        except Exception as e:
            raise Exception(f"Failed to list assets: {str(e)}")

    async def search_assets(self, query: str, limit: int = 100) -> List[Asset]:
        """Search assets by query"""
        return await self.list_assets(search_query=query, limit=limit)

    async def get_assets_by_folder(self, folder_path: str) -> List[Asset]:
        """Get assets by folder path"""
        return await self.list_assets(path=folder_path)

    async def get_published_assets(self, limit: int = 100) -> List[Asset]:
        """Get published assets"""
        return await self.list_assets(published=True, limit=limit)

    async def get_assets_by_creator(self, created_by: str, limit: int = 100) -> List[Asset]:
        """Get assets by creator"""
        return await self.list_assets(created_by=created_by, limit=limit)

    async def update_asset_metadata(
        self,
        asset_id: str,
        metadata: Dict[str, Any]
    ) -> Asset:
        """Update asset metadata"""
        try:
            response = await self._make_request(
                "PATCH",
                f"/{asset_id}",
                json={"metadata": metadata}
            )
            return self._map_asset(response.json())
        except Exception as e:
            raise Exception(f"Failed to update asset metadata: {str(e)}")

    async def bulk_update_folder_metadata(
        self,
        folder_path: str,
        metadata: Dict[str, Any]
    ) -> BulkUpdateResult:
        """Bulk update metadata for all assets in a folder"""
        assets = await self.get_assets_by_folder(folder_path)
        results = []
        updated = 0
        failed = 0

        for asset in assets:
            try:
                await self.update_asset_metadata(asset.id, metadata)
                updated += 1
                results.append({"assetId": asset.id, "status": "success"})
            except Exception as e:
                failed += 1
                results.append({
                    "assetId": asset.id,
                    "status": "failed",
                    "error": str(e)
                })

        return BulkUpdateResult(updated=updated, failed=failed, results=results)

    async def get_asset(self, asset_id: str) -> Asset:
        """Get asset details by ID"""
        try:
            response = await self._make_request("GET", f"/{asset_id}")
            return self._map_asset(response.json())
        except Exception as e:
            raise Exception(f"Failed to get asset: {str(e)}")

    def _map_asset(self, item: Dict[str, Any]) -> Asset:
        """Map API response to Asset model"""
        return Asset(
            id=item.get("id") or item.get("repo:id", ""),
            path=item.get("path") or item.get("repo:path", ""),
            name=item.get("name") or item.get("repo:name", ""),
            title=item.get("title") or item.get("dc:title"),
            metadata=item.get("metadata", {}),
            asset_type=item.get("assetType") or item.get("dam:assetType"),
            mime_type=item.get("mimeType") or item.get("dc:format"),
            published=item.get("published") or item.get("dam:published", False),
            created_by=item.get("createdBy") or item.get("dc:creator"),
            created_at=item.get("createdAt") or item.get("repo:createDate"),
            modified_at=item.get("modifiedAt") or item.get("repo:modifyDate"),
        )
