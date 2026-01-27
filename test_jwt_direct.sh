#!/bin/bash

echo "🔐 Testing Classic Assets HTTP API with JWT Authentication"
echo "=========================================================="
echo ""

# Activate venv if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if service account JSON exists
SERVICE_ACCOUNT_JSON="./service-account.json"

if [ ! -f "$SERVICE_ACCOUNT_JSON" ]; then
    echo "❌ Service account JSON not found: $SERVICE_ACCOUNT_JSON"
    exit 1
fi

# Parse service account JSON
CLIENT_ID=$(jq -r '.integration.technicalAccount.clientId' $SERVICE_ACCOUNT_JSON)
CLIENT_SECRET=$(jq -r '.integration.technicalAccount.clientSecret' $SERVICE_ACCOUNT_JSON)
ORG_ID=$(jq -r '.integration.org' $SERVICE_ACCOUNT_JSON)
TECHNICAL_ACCOUNT_ID=$(jq -r '.integration.id' $SERVICE_ACCOUNT_JSON)
IMS_ENDPOINT=$(jq -r '.integration.imsEndpoint' $SERVICE_ACCOUNT_JSON)
METASCOPE=$(jq -r '.integration.metascopes' $SERVICE_ACCOUNT_JSON)
PRIVATE_KEY=$(jq -r '.integration.privateKey' $SERVICE_ACCOUNT_JSON)

# Save private key to temp file
TEMP_KEY=$(mktemp)
echo "$PRIVATE_KEY" > "$TEMP_KEY"

echo "📋 Service Account Info:"
echo "   Client ID: $CLIENT_ID"
echo "   Org ID: $ORG_ID"
echo "   Technical Account: $TECHNICAL_ACCOUNT_ID"
echo "   Metascope: $METASCOPE"
echo ""

# Create JWT payload
EXPIRATION=$(($(date +%s) + 3600))
METASCOPE_URL="https://${IMS_ENDPOINT}/s/${METASCOPE}"

JWT_PAYLOAD=$(cat <<EOF
{
  "exp": $EXPIRATION,
  "iss": "$ORG_ID",
  "sub": "$TECHNICAL_ACCOUNT_ID",
  "aud": "https://${IMS_ENDPOINT}/c/${CLIENT_ID}",
  "$METASCOPE_URL": true
}
EOF
)

echo "🔑 JWT Payload:"
echo "$JWT_PAYLOAD" | jq '.'
echo ""

# Check if PyJWT is installed
echo "🔍 Checking dependencies..."
python3 -c "import jwt; import cryptography" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing PyJWT and cryptography..."
    pip install PyJWT==2.8.0 cryptography==42.0.5
fi

# Generate JWT using Python
echo "🔨 Generating JWT token..."
JWT_TOKEN=$(python3 << PYTHON_SCRIPT
import json
import time
import jwt

# Read service account JSON
with open('$SERVICE_ACCOUNT_JSON', 'r') as f:
    service_account = json.load(f)

integration = service_account['integration']
tech_account = integration['technicalAccount']

# Create JWT
current_time = int(time.time())
expiration = current_time + 3600

ims_endpoint = f"https://{integration['imsEndpoint']}"
metascope = integration['metascopes']
metascope_url = f"{ims_endpoint}/s/{metascope}"

payload = {
    'exp': expiration,
    'iss': integration['org'],
    'sub': integration['id'],
    'aud': f"{ims_endpoint}/c/{tech_account['clientId']}",
    metascope_url: True
}

private_key = integration['privateKey']

token = jwt.encode(payload, private_key, algorithm='RS256')
print(token)
PYTHON_SCRIPT
)

if [ $? -ne 0 ]; then
    echo "❌ Failed to generate JWT token"
    rm -f "$TEMP_KEY"
    exit 1
fi

echo "✅ JWT Token generated"
echo "   ${JWT_TOKEN:0:50}..."
echo ""

# Exchange JWT for Access Token
echo "🔄 Exchanging JWT for IMS Access Token..."

TOKEN_RESPONSE=$(curl -s -X POST "https://${IMS_ENDPOINT}/ims/exchange/jwt/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "jwt_token=${JWT_TOKEN}")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    echo "Response:"
    echo "$TOKEN_RESPONSE" | jq '.'
    rm -f "$TEMP_KEY"
    exit 1
fi

echo "✅ Access Token obtained"
echo "   ${ACCESS_TOKEN:0:50}..."
echo ""

# Clean up
rm -f "$TEMP_KEY"

# Load AEM base URL from .env
source .env

echo "=========================================================="
echo "🚀 Ready to Test Classic Assets API!"
echo "=========================================================="
echo ""
echo "📝 Example Commands:"
echo ""
echo "1️⃣ List root /content/dam:"
echo ""
echo "curl -X GET \"${AEM_BASE_URL}/api/assets/content/dam.json\" \\"
echo "  -H \"Authorization: Bearer ${ACCESS_TOKEN}\" \\"
echo "  -H \"Content-Type: application/json\" | jq '.'"
echo ""
echo "=========================================================="
echo ""
echo "2️⃣ List specific folder:"
echo ""
echo "curl -X GET \"${AEM_BASE_URL}/api/assets/content/dam/H2OR/Hk/canada-goose.json\" \\"
echo "  -H \"Authorization: Bearer ${ACCESS_TOKEN}\" \\"
echo "  -H \"Content-Type: application/json\" | jq '.'"
echo ""
echo "=========================================================="
echo ""
echo "3️⃣ Your previous test (which returned 0 assets):"
echo ""
echo "curl -X GET \"${AEM_BASE_URL}/api/assets/H2OR.json\" \\"
echo "  -H \"Authorization: Bearer ${ACCESS_TOKEN}\" \\"
echo "  -H \"Content-Type: application/json\" | jq '.'"
echo ""
echo "=========================================================="
echo ""
echo "💡 Tip: The classic API expects the FULL path starting with /content/dam/"
echo "   Not just /H2OR, but /content/dam/H2OR"
echo ""
echo "⏰ Token expires in 1 hour ($(date -v +1H '+%H:%M:%S'))"
echo ""

# Execute test
echo "🧪 Running Test: List /content/dam/H2OR/Hk/canada-goose"
echo "=========================================================="
echo ""

curl -X GET "${AEM_BASE_URL}/api/assets/content/dam/H2OR/Hk/canada-goose.json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq '.'

echo ""
echo "=========================================================="
echo "✅ Test Complete!"
echo ""
