#!/bin/bash

echo "🧪 Testing AEM Assets API calls"
echo "================================"
echo ""

# Test 1: List folders (this works)
echo "1️⃣ Testing list_folders with /content/dam/H2OR/Hk/canada-goose"
curl -s -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_folders",
    "arguments": {"path": "/content/dam/H2OR/Hk/canada-goose"}
  }' | jq '.'

echo ""
echo "================================"
echo ""

# Test 2: List assets by folder (failing)
echo "2️⃣ Testing list_assets_by_folder with /content/dam/H2OR/Hk/canada-goose"
curl -s -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_assets_by_folder",
    "arguments": {"folderPath": "/content/dam/H2OR/Hk/canada-goose"}
  }' | jq '.'

echo ""
echo "================================"
echo ""

# Test 3: Try list_all_assets instead
echo "3️⃣ Testing list_all_assets without path"
curl -s -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_all_assets",
    "arguments": {"limit": 10}
  }' | jq '.'

echo ""
echo "================================"

