#!/bin/bash

# Script to create .env file with your AEM credentials

echo "🔧 AEM Assets MCP Server - Environment Setup"
echo "============================================="
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. Edit .env manually if needed."
        exit 0
    fi
fi

echo "Please provide your AEM OAuth Server-to-Server credentials."
echo "Get these from: https://developer.adobe.com/console"
echo ""

# AEM Base URL
read -p "AEM Base URL [https://author-p12345-e67890.adobeaemcloud.com]: " aem_url
aem_url=${aem_url:-https://author-p12345-e67890.adobeaemcloud.com}

# Client ID
read -p "AEM Client ID: " client_id

# Client Secret
echo ""
echo "⚠️  CLIENT SECRET is sensitive - it will not be displayed"
read -sp "AEM Client Secret: " client_secret
echo ""

if [ -z "$client_secret" ]; then
    echo "❌ Client Secret cannot be empty!"
    exit 1
fi

# Create .env file
cat > .env << EOF
# Adobe Experience Manager Configuration
# Generated on $(date)

# AEM Instance
AEM_BASE_URL=${aem_url}

# OAuth Server-to-Server Credentials
AEM_CLIENT_ID=${client_id}
AEM_CLIENT_SECRET=${client_secret}
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "📋 Configuration:"
echo "   AEM URL: ${aem_url}"
echo "   Client ID: ${client_id}"
echo "   Client Secret: ****** (hidden)"
echo ""
echo "🚀 Next steps:"
echo "   1. Verify your credentials are correct"
echo "   2. Run: source venv/bin/activate"
echo "   3. Run: uvicorn app.main:app --reload"
echo "   4. Test: curl http://localhost:8000/health"
echo ""
echo "📚 For help, see:"
echo "   - GET_CREDENTIALS.md - How to get credentials"
echo "   - OAUTH_SETUP_SUMMARY.md - OAuth setup guide"
echo "   - LOCAL_DEVELOPMENT.md - Development guide"
echo ""
