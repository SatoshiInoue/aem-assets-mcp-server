#!/bin/bash

# AEM Assets MCP Server - Setup Script

set -e

echo "🚀 Setting up AEM Assets MCP Server..."

# Check Python version
echo ""
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.11+ required. Current version: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your AEM credentials."
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your AEM credentials before running the server!"
    echo "   Run: nano .env"
else
    echo "✅ .env file already exists"
fi

# Check if .env has been configured
if grep -q "your_access_token_here" .env; then
    echo ""
    echo "⚠️  WARNING: .env file still has placeholder values!"
    echo "   Please update with your actual AEM credentials."
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Edit .env with your AEM credentials: nano .env"
echo "   2. Run the server: uvicorn app.main:app --reload"
echo "   3. Visit: http://localhost:8000"
echo ""
echo "📚 Documentation:"
echo "   - Main README: cat README.md"
echo "   - Local Development: cat LOCAL_DEVELOPMENT.md"
echo "   - Phase 1 Deployment: cat DEPLOYMENT_VERCEL.md"
echo "   - Phase 2 Deployment: cat DEPLOYMENT_CLOUDRUN.md"
echo ""
