# 🚀 Quick Start Guide

Get the AEM Assets MCP Server running in minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] AEM Assets API credentials ready
- [ ] Choose deployment platform (Vercel or Google Cloud Run)

## ⚡ 60-Second Local Setup

```bash
# 1. Run setup script
./setup.sh

# 2. Edit environment variables
nano .env

# 3. Run server
source venv/bin/activate
uvicorn app.main:app --reload

# 4. Test
curl http://localhost:8000/health
```

✅ **Done!** Server running at http://localhost:8000

## 🌐 Deploy to Vercel (Fastest)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Add env vars in dashboard
# Deploy to production
vercel --prod
```

🎉 **Live!** Your API is now at `https://your-project.vercel.app/api/mcp`

## ☁️ Deploy to Cloud Run (Production-Ready)

```bash
# Set up GCP
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Create artifact registry
gcloud artifacts repositories create aem-mcp-images \
  --repository-format=docker \
  --location=us-central1

# Build and push
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT/aem-mcp-images/aem-mcp-server:latest .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT/aem-mcp-images/aem-mcp-server:latest

# Deploy
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values
terraform init
terraform apply
```

🚀 **Deployed!** Get URL with `terraform output service_url`

## 🤖 Connect to ChatGPT

1. Create Custom GPT at https://chat.openai.com
2. Add Action with this OpenAPI schema:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "AEM Assets MCP Server",
    "version": "1.0.0"
  },
  "servers": [
    {"url": "https://your-deployment-url.com"}
  ],
  "paths": {
    "/api/mcp": {
      "post": {
        "operationId": "callTool",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "tool": {
                    "type": "string",
                    "enum": ["list_folders", "list_published_assets", "search_assets", "list_assets_by_folder", "bulk_update_metadata", "list_assets_by_creator", "list_all_assets", "get_asset_details"]
                  },
                  "arguments": {"type": "object"}
                },
                "required": ["tool"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {"type": "object"}
              }
            }
          }
        }
      }
    }
  }
}
```

3. Test with: *"List all folders in the root directory"*

## 📚 Full Documentation

- **[README.md](./README.md)** - Complete overview
- **[LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md)** - Development guide
- **[DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md)** - Phase 1 deployment
- **[DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md)** - Phase 2 deployment
- **[CHATGPT_SETUP.md](./CHATGPT_SETUP.md)** - ChatGPT integration

## 🆘 Troubleshooting

### Server won't start
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt

# Check .env file
cat .env
```

### Import errors
```bash
# Make sure you're in project root
pwd

# Activate virtual environment
source venv/bin/activate
```

### Environment variables missing
```bash
# Make sure .env exists and has values
cp env.example .env
nano .env
```

### AEM connection errors
- Verify access token is valid (they expire!)
- Check base URL is correct
- Ensure Organization ID format: `xxxxx@AdobeOrg`

## 💡 Example Prompts for ChatGPT

Once connected:

- ✅ *"List all folders in the root directory"*
- ✅ *"Show me published assets"*
- ✅ *"Find assets related to Electric Vehicle"*
- ✅ *"Update all assets in /content/dam/products with jancode: ABC123"*
- ✅ *"List assets uploaded by user@example.com"*

## 🎯 Next Steps

1. ✅ Get it running locally
2. ✅ Deploy (Vercel for quick start, Cloud Run for production)
3. ✅ Connect to ChatGPT
4. ✅ Test with your AEM instance
5. ✅ Customize for your needs

---

**Questions?** Check the full documentation or open an issue!
