# ChatGPT Integration Guide

This guide explains how to connect your deployed AEM Assets MCP Server to ChatGPT.

## Prerequisites

1. ChatGPT Plus or Pro subscription
2. Your MCP server deployed to either:
   - **Vercel** (Phase 1) - See [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md)
   - **Google Cloud Run** (Phase 2) - See [DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md)
3. Your deployment URL:
   - Vercel: `https://your-project.vercel.app`
   - Cloud Run: `https://aem-assets-mcp-server-xxxx.run.app`

## Method 1: Using Custom GPT with Actions (Recommended)

### Step 1: Create a Custom GPT

1. Go to [ChatGPT](https://chat.openai.com)
2. Click on your profile → "My GPTs"
3. Click "Create a GPT"
4. Go to the "Configure" tab

### Step 2: Basic Configuration

**Name:** AEM Assets Manager

**Description:** 
```
An assistant that helps you manage Adobe Experience Manager Assets. Can list folders, search assets, update metadata, and perform various asset management operations.
```

**Instructions:**
```
You are an AEM Assets management assistant. You have access to tools that interact with Adobe Experience Manager Assets API.

When users ask about assets:
- Use list_folders to browse the folder structure
- Use search_assets for keyword-based searches
- Use list_published_assets to find published content
- Use list_assets_by_folder to see assets in a specific folder
- Use bulk_update_metadata to update metadata for multiple assets
- Use list_assets_by_creator to find assets by user
- Use get_asset_details for detailed asset information

Always present results in a clear, organized format. For large result sets, summarize key findings and ask if the user wants more details.
```

### Step 3: Add Actions

1. Scroll down to "Actions"
2. Click "Create new action"
3. Choose "Import from OpenAPI Schema"
4. Paste the following OpenAPI schema:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "AEM Assets MCP Server",
    "description": "API for managing Adobe Experience Manager Assets",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://your-project.vercel.app"
    }
  ],
  "paths": {
    "/api/mcp": {
      "post": {
        "operationId": "executeAEMTool",
        "summary": "Execute an AEM Assets management tool",
        "description": "Call various tools to interact with AEM Assets API",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "tool": {
                    "type": "string",
                    "description": "The tool to execute",
                    "enum": [
                      "list_folders",
                      "list_published_assets",
                      "search_assets",
                      "list_assets_by_folder",
                      "bulk_update_metadata",
                      "list_assets_by_creator",
                      "list_all_assets",
                      "get_asset_details"
                    ]
                  },
                  "arguments": {
                    "type": "object",
                    "description": "Arguments for the tool"
                  }
                },
                "required": ["tool"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "result": {
                      "type": "object",
                      "description": "Result from the tool execution"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Important:** Replace `https://your-project.vercel.app` with your actual Vercel deployment URL.

5. Click "Test" to verify the connection
6. Save the action

### Step 4: Test Your GPT

Try these example prompts:

1. "List all folders in the root directory"
2. "Show me all published assets"
3. "Search for assets related to 'Electric Vehicle'"
4. "What assets are in the /content/dam/marketing folder?"
5. "Update all assets in /content/dam/products with jancode: ABCDEFG"

### Step 5: Publish Your GPT

1. Click "Save" in the top right
2. Choose sharing options:
   - "Only me" - Private use
   - "Anyone with a link" - Share with team
   - "Public" - Share with everyone (requires verification)

## Method 2: Using ChatGPT Plugins (If Available)

If your ChatGPT account has access to plugins:

1. Go to Settings → Beta Features
2. Enable "Plugins"
3. In a chat, click on the plugin icon
4. Select "Plugin store"
5. Choose "Develop your own plugin"
6. Enter your Vercel URL: `https://your-project.vercel.app`
7. Add the `.well-known/ai-plugin.json` manifest (see below)

### Plugin Manifest

Create a file at `api/plugin-manifest.json` in your project:

```json
{
  "schema_version": "v1",
  "name_for_human": "AEM Assets Manager",
  "name_for_model": "aem_assets",
  "description_for_human": "Manage Adobe Experience Manager Assets - list, search, and update assets and folders.",
  "description_for_model": "Plugin for managing AEM Assets. Can list folders, search assets, filter by criteria, and update metadata.",
  "auth": {
    "type": "none"
  },
  "api": {
    "type": "openapi",
    "url": "https://your-project.vercel.app/api/openapi.json"
  },
  "logo_url": "https://your-project.vercel.app/logo.png",
  "contact_email": "your-email@example.com",
  "legal_info_url": "https://your-project.vercel.app/legal"
}
```

## Method 3: Direct API Calls in ChatGPT

If you don't want to create a custom GPT, you can simply tell ChatGPT to make API calls:

**Example prompt:**
```
Call this API endpoint: https://your-project.vercel.app/api/mcp
Method: POST
Body: {
  "tool": "list_folders",
  "arguments": {
    "path": "/"
  }
}

And help me interpret the results.
```

> Note: This method is less convenient but works for quick tests.

## Usage Examples

Once your Custom GPT is set up, you can use natural language:

### Browse Folders
```
User: "What folders do we have in the root?"
GPT: *calls list_folders with path: "/"*
GPT: "I found the following folders in the root directory: ..."
```

### Search Assets
```
User: "Find all assets related to electric vehicles"
GPT: *calls search_assets with query: "electric vehicles"*
GPT: "I found 15 assets related to electric vehicles: ..."
```

### Update Metadata
```
User: "Add jancode 'ABC123' to all assets in /content/dam/products"
GPT: *calls bulk_update_metadata*
GPT: "I've updated metadata for 24 assets. Here's the summary: ..."
```

### Filter by User
```
User: "Show me all assets uploaded by john@example.com"
GPT: *calls list_assets_by_creator*
GPT: "John has uploaded 8 assets: ..."
```

## Tool Mapping Guide

When ChatGPT receives these requests, it should map to:

| User Intent | Tool | Arguments |
|-------------|------|-----------|
| "List folders in X" | `list_folders` | `{ path: "X" }` |
| "Show published assets" | `list_published_assets` | `{ limit: 100 }` |
| "Search for X" | `search_assets` | `{ query: "X" }` |
| "Assets in folder X" | `list_assets_by_folder` | `{ folderPath: "X" }` |
| "Update metadata in X" | `bulk_update_metadata` | `{ folderPath: "X", metadata: {...} }` |
| "Assets by user X" | `list_assets_by_creator` | `{ createdBy: "X" }` |
| "Details for asset X" | `get_asset_details` | `{ assetId: "X" }` |

## Troubleshooting

### Action Not Working

1. **Check Vercel URL**: Ensure you replaced the placeholder URL with your actual deployment
2. **Test endpoint**: Try `curl https://your-project.vercel.app/api/mcp` to verify it's accessible
3. **Check CORS**: The API should allow requests from OpenAI domains (already configured in the code)
4. **Review logs**: Check Vercel function logs for errors

### Authentication Errors

If the API returns 500 errors about missing credentials:
1. Go to Vercel dashboard
2. Navigate to your project
3. Settings → Environment Variables
4. Verify all AEM credentials are set:
   - `AEM_BASE_URL`
   - `AEM_ACCESS_TOKEN`
   - `AEM_ORG_ID`
   - `AEM_CLIENT_ID`

### Rate Limiting

If you hit rate limits:
1. Reduce the `limit` parameter in queries
2. Add delays between bulk operations
3. Consider implementing caching on the server side

## Advanced: Custom Instructions

Add to your Custom GPT instructions for better behavior:

```
When listing assets or folders:
- Always format results as a table or bullet list
- Highlight key metadata like name, path, and creation date
- If results are truncated, inform the user

For bulk operations:
- Always confirm with the user before updating metadata
- Show a preview of what will be changed
- Report success/failure counts after operations

For searches:
- If no results are found, suggest alternative search terms
- Show the most relevant results first
- Ask if the user wants to refine the search
```

## Best Practices

1. **Start Broad**: Begin with folder listings to understand structure
2. **Be Specific**: Use exact folder paths when known
3. **Confirm Changes**: Always review before bulk metadata updates
4. **Use Filters**: Combine tools for complex queries
5. **Check Results**: Verify operations completed successfully

## Example Conversation Flow

```
User: "I need to organize our electric vehicle assets"

GPT: "I can help with that! Let me first see what we have. 
      Let me search for electric vehicle related assets."
      *calls search_assets*
      
GPT: "I found 12 assets. They're currently in different folders.
      Would you like me to:
      1. List the current folders they're in
      2. Show details of specific assets
      3. Update their metadata for better organization?"

User: "Show me what folders they're in"

GPT: *analyzes results and groups by folder path*
     "The assets are distributed across:
     - /content/dam/products (7 assets)
     - /content/dam/marketing (3 assets)  
     - /content/dam/archive (2 assets)"

User: "Add category 'EV' to all of them in products folder"

GPT: "I'll update metadata for 7 assets in /content/dam/products.
      Adding: { category: 'EV' }
      Should I proceed?"

User: "Yes"

GPT: *calls bulk_update_metadata*
     "Done! Successfully updated metadata for all 7 assets."
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Public GPTs**: If you publish your GPT publicly, anyone can use it. Ensure your AEM permissions are appropriate.
2. **API Exposure**: Your Vercel endpoint is publicly accessible. Consider adding authentication if needed.
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Audit Logs**: Monitor Vercel logs for unusual activity
5. **Credentials**: Never share your AEM credentials or Vercel environment variables

## Next Steps

1. ✅ Deploy your MCP server to Vercel
2. ✅ Create and configure your Custom GPT
3. ✅ Test with simple queries
4. ✅ Train your team on available commands
5. ✅ Monitor usage and refine instructions
6. ✅ Add more tools as needed

---

Need help? Check the main [README.md](./README.md) for more details or troubleshooting tips.
