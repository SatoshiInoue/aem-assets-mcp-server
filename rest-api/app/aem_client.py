"""AEM Assets API Client with OAuth Server-to-Server and JWT Service Account Authentication"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os
from app.models import Asset, Folder, BulkUpdateResult
from app.constants import AEM_API_ENDPOINT, AEM_FOLDERS_ENDPOINT, AEM_CLASSIC_API_ENDPOINT, ADOBE_IMS_TOKEN_ENDPOINT, AEM_SCOPES

logger = logging.getLogger(__name__)


class AEMConfig:
    """AEM Configuration"""
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        service_account_json_path: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = AEM_API_ENDPOINT
        self.folders_endpoint = AEM_FOLDERS_ENDPOINT
        self.classic_api_endpoint = AEM_CLASSIC_API_ENDPOINT
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = AEM_SCOPES
        self.ims_token_endpoint = ADOBE_IMS_TOKEN_ENDPOINT
        self.service_account_json_path = service_account_json_path


class AEMAssetsClient:
    """Client for AEM Assets Author API with automatic token refresh"""

    def __init__(self, config: AEMConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # JWT Service Account auth (for classic API)
        self.jwt_auth = None
        if config.service_account_json_path:
            try:
                from app.jwt_auth import JWTServiceAccountAuth
                # JWTServiceAccountAuth handles both file paths and JSON strings
                self.jwt_auth = JWTServiceAccountAuth(config.service_account_json_path)
                logger.info("JWT Service Account authentication initialized for classic API")
            except Exception as e:
                logger.warning(f"Failed to initialize JWT auth: {e}. Classic API will not be available.")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        if self.jwt_auth:
            await self.jwt_auth.close()

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
        """
        Get assets by folder path.
        
        Strategy: Try classic API first, fall back to folders API if 403.
        """
        try:
            # Try classic API first (more comprehensive)
            return await self._get_assets_classic_api(folder_path)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning(f"Classic API returned 403, falling back to folders API")
                # Fall back to folders API which lists children
                return await self._get_assets_via_folders_api(folder_path)
            else:
                raise
    
    async def _get_assets_classic_api(self, folder_path: str) -> List[Asset]:
        """
        Get assets using classic Assets HTTP API (/api/assets).
        Uses JWT Service Account authentication.
        
        Note: Classic API expects full repository path starting from root.
        Example: /content/dam/folder (not just /folder)
        
        Reference: https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/assets/admin/mac-api-assets
        """
        if not self.jwt_auth:
            raise Exception("JWT Service Account authentication not configured. Please provide service_account_json_path.")
        
        logger.debug(f"Classic API request for folder_path: {folder_path}")
        
        # Classic API implicitly assumes /content/dam as the root
        # Strip /content/dam prefix if present
        if folder_path.startswith("/content/dam/"):
            relative_path = folder_path[len("/content/dam/"):]
        elif folder_path.startswith("/content/dam"):
            relative_path = folder_path[len("/content/dam"):]
        elif folder_path.startswith("/"):
            relative_path = folder_path[1:]
        else:
            relative_path = folder_path
        
        # Clean up the relative path
        relative_path = relative_path.strip("/")
        
        # Construct the classic API endpoint
        if not relative_path:
            # Root folder: /api/assets.json
            endpoint = ".json"
        else:
            # Specific folder: /api/assets/{path}.json
            endpoint = f"/{relative_path}.json"
        
        # Build full URL with classic API endpoint
        url = f"{self.config.base_url}{self.config.classic_api_endpoint}{endpoint}"
        
        logger.info(f"Classic API path transformation: '{folder_path}' → '{url}'")
        
        # Get JWT-based access token
        access_token = await self.jwt_auth.get_access_token()
        
        # Make request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        logger.debug(f"Fetching assets from classic API: {url}")
        
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Classic API returns Siren format with 'entities' array
        entities = data.get("entities", [])
        
        logger.debug(f"Found {len(entities)} entities in folder")
        
        # Debug: Log what we found
        for entity in entities:
            entity_class = entity.get("class", [])
            entity_name = entity.get("properties", {}).get("name", "unknown")
            logger.debug(f"  Entity '{entity_name}': class={entity_class}")
        
        # Filter for assets only (not folders)
        assets = []
        for entity in entities:
            entity_class = entity.get("class", [])
            # Check if it's an asset (not a folder)
            # Folders have class ["assets/folder"], assets should have ["assets/asset"]
            if "assets/asset" in entity_class:
                # Get properties
                props = entity.get("properties", {})
                
                # Map to our Asset model
                assets.append(Asset(
                    id=props.get("id", ""),
                    path=props.get("path", ""),
                    name=props.get("name", ""),
                    title=props.get("title") or props.get("dc:title") or props.get("jcr:title"),
                    metadata=props,
                    asset_type=props.get("type"),
                    mime_type=props.get("type"),
                    published=props.get("published", False),
                    created_by=props.get("createdBy") or props.get("dc:creator"),
                    created_at=props.get("created") or props.get("jcr:created"),
                    modified_at=props.get("modified") or props.get("jcr:lastModified"),
                ))
        
        logger.info(f"Retrieved {len(assets)} assets (out of {len(entities)} total entities) from folder {folder_path} via classic API")
        return assets
    
    async def _get_assets_via_folders_api(self, folder_path: str) -> List[Asset]:
        """
        Get assets using Folders API as fallback when classic API has no permissions.
        The folders API returns children which can include both folders and assets.
        """
        try:
            response = await self._make_request(
                "GET",
                "",
                use_folders_api=True,
                params={"path": folder_path}
            )
            data = response.json()
            
            children = data.get("children", [])
            
            logger.debug(f"Found {len(children)} children via folders API")
            
            # Filter for assets (children that are not folders)
            assets = []
            for child in children:
                # If it has assetId, it's likely an asset (folders have folderId)
                if "assetId" in child or "asset" in child.get("type", "").lower():
                    # Map folder API response to Asset model
                    # Note: Folders API has limited asset info, might need additional calls
                    assets.append(Asset(
                        id=child.get("assetId", child.get("id", "")),
                        path=child.get("path", ""),
                        name=child.get("name", ""),
                        title=child.get("title"),
                        metadata=child,
                        asset_type=child.get("type"),
                        mime_type=child.get("mimeType"),
                        published=child.get("published", False),
                        created_by=child.get("createdBy"),
                        created_at=child.get("createdAt"),
                        modified_at=child.get("modifiedAt"),
                    ))
            
            logger.info(f"Retrieved {len(assets)} assets from folder {folder_path} via folders API")
            return assets
            
        except Exception as e:
            logger.error(f"Error listing assets via folders API: {str(e)}")
            raise Exception(f"Failed to list assets in folder: {str(e)}")

    async def get_published_assets(self, limit: int = 100) -> List[Asset]:
        """Get published assets"""
        return await self.list_assets(published=True, limit=limit)

    async def get_assets_by_creator(self, created_by: str, limit: int = 100) -> List[Asset]:
        """Get assets by creator"""
        return await self.list_assets(created_by=created_by, limit=limit)

    async def update_asset_metadata(
        self,
        asset_path: str,
        metadata: Dict[str, Any]
    ) -> Asset:
        """
        Update asset metadata using the classic Assets HTTP API.
        
        Args:
            asset_path: Full asset path (e.g., /content/dam/folder/image.jpg)
            metadata: Dictionary of metadata key-value pairs to update
        
        Returns:
            Updated Asset object
        """
        if not self.jwt_auth:
            raise Exception("JWT Service Account authentication not configured. Please provide service_account_json_path.")
        
        logger.debug(f"Updating metadata for asset: {asset_path}")
        
        # Strip /content/dam prefix if present (classic API assumes it)
        if asset_path.startswith("/content/dam/"):
            relative_path = asset_path[len("/content/dam/"):]
        elif asset_path.startswith("/content/dam"):
            relative_path = asset_path[len("/content/dam"):]
        elif asset_path.startswith("/"):
            relative_path = asset_path[1:]
        else:
            relative_path = asset_path
        
        # Clean up the relative path
        relative_path = relative_path.strip("/")
        
        if not relative_path:
            raise ValueError("Asset path cannot be empty")
        
        # Construct the classic API endpoint (without .json extension for PUT)
        endpoint = f"/{relative_path}"
        url = f"{self.config.base_url}{self.config.classic_api_endpoint}{endpoint}"
        
        logger.info(f"Updating metadata via classic API: '{asset_path}' → '{url}'")
        
        # Map common field names to Dublin Core (dc:) namespace
        field_mapping = {
            "title": "dc:title",
            "description": "dc:description",
            "subject": "dc:subject",
            "creator": "dc:creator",
            "language": "dc:language",
            "keywords": "dc:keywords",
        }
        
        # Transform metadata keys to use proper namespaces
        mapped_metadata = {}
        for key, value in metadata.items():
            # If key is in our mapping and doesn't already have a namespace prefix, map it
            if key in field_mapping and ":" not in key:
                mapped_key = field_mapping[key]
            else:
                mapped_key = key
            mapped_metadata[mapped_key] = value
        
        logger.debug(f"Mapped metadata: {metadata} → {mapped_metadata}")
        
        # Get JWT-based access token
        access_token = await self.jwt_auth.get_access_token()
        
        # Headers per Adobe documentation
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        # Payload format per Adobe documentation:
        # PUT /api/assets/myfolder/myAsset.png -H"Content-Type: application/json" 
        # -d '{"class":"asset", "properties":{"dc:title":"My Asset"}}'
        payload = {
            "class": "asset",
            "properties": mapped_metadata
        }
        
        logger.debug(f"Updating metadata with payload: {payload}")
        
        try:
            # Use PUT as per Adobe documentation
            response = await self.client.put(url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully updated metadata for {asset_path}")
            
            # Fetch the updated asset to return
            return await self.get_asset(asset_path)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating asset metadata: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to update asset metadata: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            logger.error(f"Error updating asset metadata: {str(e)}")
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
                await self.update_asset_metadata(asset.path, metadata)  # Use path instead of id
                updated += 1
                results.append({"assetPath": asset.path, "status": "success"})
            except Exception as e:
                failed += 1
                results.append({
                    "assetPath": asset.path,
                    "status": "failed",
                    "error": str(e)
                })

        return BulkUpdateResult(updated=updated, failed=failed, results=results)

    async def get_asset(self, asset_path: str) -> Asset:
        """
        Get asset details by path using the classic Assets HTTP API.
        
        Args:
            asset_path: Full asset path (e.g., /content/dam/folder/image.jpg)
        
        Returns:
            Asset object with full details
        """
        if not self.jwt_auth:
            raise Exception("JWT Service Account authentication not configured. Please provide service_account_json_path.")
        
        logger.debug(f"Getting asset details for: {asset_path}")
        
        # Strip /content/dam prefix if present (classic API assumes it)
        if asset_path.startswith("/content/dam/"):
            relative_path = asset_path[len("/content/dam/"):]
        elif asset_path.startswith("/content/dam"):
            relative_path = asset_path[len("/content/dam"):]
        elif asset_path.startswith("/"):
            relative_path = asset_path[1:]
        else:
            relative_path = asset_path
        
        # Clean up the relative path
        relative_path = relative_path.strip("/")
        
        # Construct the classic API endpoint
        if not relative_path:
            raise ValueError("Asset path cannot be empty")
        
        endpoint = f"/{relative_path}.json"
        url = f"{self.config.base_url}{self.config.classic_api_endpoint}{endpoint}"
        
        logger.info(f"Classic API path transformation: '{asset_path}' → '{url}'")
        
        # Get JWT-based access token
        access_token = await self.jwt_auth.get_access_token()
        
        # Make request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Classic API returns Siren format with 'properties' for single asset
            props = data.get("properties", {})
            
            if not props:
                raise ValueError(f"No asset found at path: {asset_path}")
            
            # Extract full metadata - the classic API includes all metadata fields in properties
            # Fields like predictedTags, autogen:*, Smart Color Tags, etc. should be here
            # Create a clean metadata dict with all available fields
            metadata = {}
            
            # Copy all properties to metadata
            for key, value in props.items():
                metadata[key] = value
            
            logger.debug(f"Extracted {len(metadata)} metadata fields from asset")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Available metadata keys: {list(metadata.keys())}")
            
            # Map to our Asset model
            asset = Asset(
                id=props.get("id", ""),
                path=asset_path,  # Use the original path
                name=props.get("name", ""),
                title=props.get("title") or props.get("dc:title") or props.get("jcr:title"),
                metadata=metadata,  # Full metadata including predictedTags, autogen:*, etc.
                asset_type=props.get("type"),
                mime_type=props.get("type"),
                published=props.get("published", False),
                created_by=props.get("createdBy") or props.get("dc:creator"),
                created_at=props.get("created") or props.get("jcr:created"),
                modified_at=props.get("modified") or props.get("jcr:lastModified"),
            )
            
            logger.info(f"Retrieved asset details with {len(metadata)} metadata fields for {asset_path}")
            return asset
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting asset: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to get asset: {e.response.status_code} {e.response.reason_phrase}")
        except Exception as e:
            logger.error(f"Error getting asset details: {str(e)}")
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
