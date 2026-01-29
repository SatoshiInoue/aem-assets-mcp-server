"""Global constants for AEM Assets MCP Server"""

# Adobe API Endpoints (these are part of Adobe's API specification and don't change)
# Classic Assets HTTP API - stable, public API for folder listing
AEM_CLASSIC_API_ENDPOINT = "/api/assets"

# Newer OpenAPI endpoints - for other operations
AEM_API_ENDPOINT = "/adobe/assets"
AEM_FOLDERS_ENDPOINT = "/adobe/folders"

# Adobe IMS Token Endpoint (standard endpoint, rarely changes)
ADOBE_IMS_TOKEN_ENDPOINT = "https://ims-na1.adobelogin.com/ims/token/v3"

# OAuth Scopes required for AEM Assets and Folders APIs
AEM_SCOPES = "openid,AdobeID,aem.assets.author,aem.folders"
