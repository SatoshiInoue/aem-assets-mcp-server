# Testing Guide for AEM Assets MCP Server

## Quick Local Tests

### 1. Test the Updated `list_assets_by_folder` (Now Uses Classic API)

Start your server:
```bash
cd "/Users/satoshii/Development/Cursor/SC Practice 20260130 - Assets MCP"
source venv/bin/activate
uvicorn app.main:app --reload
```

Then in another terminal:
```bash
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_assets_by_folder",
    "arguments": {"folderPath": "/content/dam/H2OR/Hk/canada-goose"}
  }' | jq '.'
```

### 2. Test Classic API Directly

```bash
# Load environment
source .env

# Get OAuth token
TOKEN=$(curl -s -X POST "$ADOBE_IMS_TOKEN_ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$AEM_CLIENT_ID" \
  -d "client_secret=$AEM_CLIENT_SECRET" \
  -d "scope=openid,AdobeID,aem.assets.author,aem.folders" | jq -r '.access_token')

# Test classic API for folder listing
curl -X GET "${AEM_BASE_URL}/api/assets/content/dam/H2OR/Hk/canada-goose.json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID" \
  -H "Content-Type: application/json" | jq '.entities[] | {class: .class, name: .properties.name}'
```

### 3. Compare APIs

**New OpenAPI (doesn't support path parameter well):**
```bash
curl -X GET "${AEM_BASE_URL}/adobe/assets?path=/content/dam/folder" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID"
# Returns 404
```

**Classic HTTP API (works for folder listing):**
```bash
curl -X GET "${AEM_BASE_URL}/api/assets/content/dam/folder.json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID"
# Returns Siren format with entities array
```

## Understanding the Response

### Classic API Response Structure (Siren Format)

```json
{
  "class": ["assets/folder"],
  "properties": {
    "name": "canada-goose",
    "title": "Canada Goose",
    "created": "2024-01-15T10:00:00.000Z",
    "createdBy": "admin",
    "modified": "2024-01-20T15:30:00.000Z"
  },
  "entities": [
    {
      "class": ["asset/asset"],
      "properties": {
        "name": "image1.jpg",
        "title": "Product Image 1",
        "type": "image/jpeg",
        "path": "/content/dam/H2OR/Hk/canada-goose/image1.jpg"
      },
      "links": [
        {"rel": ["self"], "href": "/api/assets/content/dam/..."}
      ]
    },
    {
      "class": ["assets/folder"],
      "properties": {
        "name": "subfolder",
        "title": "Subfolder"
      }
    }
  ],
  "links": [
    {"rel": ["self"], "href": "/api/assets/content/dam/H2OR/Hk/canada-goose"},
    {"rel": ["parent"], "href": "/api/assets/content/dam/H2OR/Hk"}
  ]
}
```

### Key Differences

| Feature | Classic API (`/api/assets`) | New OpenAPI (`/adobe/assets`) |
|---------|----------------------------|-------------------------------|
| Folder listing | ✅ `GET /api/assets/path.json` | ❌ No direct folder support |
| Response format | Siren (entities array) | JSON array |
| Path parameter | ❌ Not supported | ❌ 404 error |
| URL structure | Path in URL | Query parameters |
| Stability | ✅ Stable, documented | ⚠️ Newer, limited docs |

## Automated Test Scripts

Run the automated test suite:

```bash
# Test via MCP server
./test_assets_api.sh

# Test AEM API directly
./test_aem_direct.sh
```

## Expected Results

After the update, `list_assets_by_folder` should:
- ✅ Return assets from the specified folder
- ✅ Filter out subfolders (only return assets)
- ✅ Map properties correctly to Asset model
- ✅ Work with any valid folder path

## Troubleshooting

### Still Getting 404?

1. **Check the folder path exists:**
   ```bash
   curl -X GET "${AEM_BASE_URL}/api/assets/content/dam.json" \
     -H "Authorization: Bearer $TOKEN" \
     -H "x-api-key: $AEM_CLIENT_ID"
   ```

2. **Check permissions:**
   - Ensure your OAuth credential has `aem.assets.author` scope
   - Verify Product Profile in Adobe Developer Console includes read permissions

3. **Check the path format:**
   - Path should start with `/content/dam/`
   - Don't include leading `/` when constructing endpoint
   - Classic API needs `.json` suffix

### Empty Results?

- The folder might only contain subfolders (no assets)
- Try a parent folder or check in AEM UI

## Reference

- [AEM Assets HTTP API Documentation](https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/assets/admin/mac-api-assets#retrieve-a-folder-listing)
- Classic API endpoint: `/api/assets`
- Siren hypermedia format specification
