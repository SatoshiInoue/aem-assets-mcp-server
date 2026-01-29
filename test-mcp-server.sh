#!/bin/bash

echo "🧪 Testing MCP Server Deployment"
echo "=================================="
echo ""

MCP_URL="https://aem-assets-mcp-server-3asyfvcagq-an.a.run.app"

echo "1️⃣ Testing basic connectivity..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" $MCP_URL
echo ""

echo "2️⃣ Testing SSE endpoint..."
curl -N -H "Accept: text/event-stream" -m 5 $MCP_URL/sse 2>&1 | head -10
echo ""

echo "3️⃣ Testing with MCP Inspector..."
echo "Run this command to test interactively:"
echo "npx @modelcontextprotocol/inspector $MCP_URL"
echo ""

echo "4️⃣ For Cursor integration:"
echo "Add to Cursor MCP settings:"
echo '{
  "mcpServers": {
    "aem-assets": {
      "url": "'$MCP_URL'",
      "transport": "sse"
    }
  }
}'
echo ""

echo "✅ Testing complete!"
