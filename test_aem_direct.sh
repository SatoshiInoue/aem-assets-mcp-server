#!/bin/bash

echo "🔬 Testing AEM Assets API Directly"
echo "===================================="
echo ""
echo "This will call AEM API directly to see what parameters work"
echo ""

# Load environment
source .env

# Get OAuth token
echo "1️⃣ Getting OAuth token..."
TOKEN_RESPONSE=$(curl -s -X POST "$ADOBE_IMS_TOKEN_ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$AEM_CLIENT_ID" \
  -d "client_secret=$AEM_CLIENT_SECRET" \
  -d "scope=$AEM_SCOPES")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Failed to get access token"
  echo $TOKEN_RESPONSE | jq '.'
  exit 1
fi

echo "✅ Got access token"
echo ""

# Test different API calls
echo "================================"
echo "2️⃣ Test: Classic API - GET /api/assets/content/dam.json"
echo "================================"
curl -s -X GET "${AEM_BASE_URL}/api/assets/content/dam.json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "================================"
echo "3️⃣ Test: Classic API - GET /api/assets/content/dam/H2OR/Hk/canada-goose.json"
echo "================================"
curl -s -X GET "${AEM_BASE_URL}/api/assets/content/dam/H2OR/Hk/canada-goose.json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID" \
  -H "Content-Type: application/json" | jq '.entities[] | {class: .class, name: .properties.name, type: .properties.type}'

echo ""
echo "================================"
echo "4️⃣ Test: GET /adobe/folders for that path"
echo "================================"
curl -s -X GET "${AEM_BASE_URL}/adobe/folders?path=/content/dam/H2OR/Hk/canada-goose" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "================================"
echo "5️⃣ Test: Search in that folder"
echo "================================"
curl -s -X POST "${AEM_BASE_URL}/adobe/assets/search" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-api-key: $AEM_CLIENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "path": "/content/dam/H2OR/Hk/canada-goose"
    },
    "limit": 5
  }' | jq '.'

echo ""
echo "================================"

