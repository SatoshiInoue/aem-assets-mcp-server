# AEM Assets MCP Server

A Model Context Protocol (MCP) server for Adobe Experience Manager (AEM) Assets Author API built with Python and FastAPI. Can be deployed to **Vercel (Phase 1)** or **Google Cloud Run (Phase 2)** and used with ChatGPT.

## 🚀 Features

This MCP server provides tools to interact with AEM Assets:

- **List folders** - Browse folders in your AEM Assets repository
- **List published assets** - Find all assets that have been published
- **Search assets** - Search for assets by keywords (e.g., "Electric Vehicle")
- **List assets by folder** - Get all assets within a specific folder
- **Bulk update metadata** - Update metadata for all assets in a folder
- **List assets by creator** - Find assets uploaded by a specific user
- **Get asset details** - Retrieve detailed information about a specific asset

## 📋 Prerequisites

### General Requirements
1. **Adobe Experience Manager Assets Author API Access**
   - AEM base URL
   - OAuth Server-to-Server credentials:
     - Client ID (API Key)
     - Client Secret
     - Scopes
   - See [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) for how to obtain these

2. **Python 3.11+**

### Phase 1 Requirements (Vercel)
- Vercel account
- ChatGPT Plus/Pro (to use MCP servers)

### Phase 2 Requirements (Google Cloud Run)
- Google Cloud Platform account
- `gcloud` CLI installed
- Terraform installed (for infrastructure as code)
- Docker installed
- GitHub account (for CI/CD)

## 🛠️ Tech Stack

- **Python 3.11** - Core language
- **FastAPI** - Modern async web framework
- **HTTPX** - Async HTTP client
- **Pydantic** - Data validation
- **OAuth Server-to-Server** - Automatic token refresh
- **Docker** - Containerization
- **Terraform** - Infrastructure as Code
- **GitHub Actions** - CI/CD

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application
│   ├── aem_client.py         # AEM Assets API client
│   └── models.py             # Pydantic models
├── terraform/
│   ├── main.tf               # Main Terraform configuration
│   ├── variables.tf          # Terraform variables
│   └── terraform.tfvars.example
├── .github/workflows/
│   ├── deploy-cloud-run.yml  # Cloud Run deployment
│   ├── terraform-apply.yml   # Terraform workflow
│   └── test.yml              # Testing workflow
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel configuration
├── env.example              # Environment template
└── README.md
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
```bash
cd "SC Practice 20260130 - Assets MCP"
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
# Option 1: Interactive setup (recommended)
./create-env.sh

# Option 2: Manual setup
cp env.example .env
nano .env  # Edit with your AEM credentials
```

See [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) for how to get your OAuth credentials.

5. **Run locally**:
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to see the server info.

### Docker Development

```bash
# Build image
docker build -t aem-mcp-server .

# Run container
docker run -p 8080:8080 \
  -e AEM_BASE_URL="https://author-p12345-e67890.adobeaemcloud.com" \
  -e AEM_CLIENT_ID="your_client_id_here" \
  -e AEM_CLIENT_SECRET="your_client_secret_here" \
  aem-mcp-server
```

## 📦 Phase 1: Deploy to Vercel

See [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md) for detailed instructions.

**Quick steps**:
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Add environment variables in Vercel dashboard
# Deploy to production
vercel --prod
```

Your API will be available at: `https://your-project.vercel.app/api/mcp`

## 🏗️ Phase 2: Deploy to Google Cloud Run

See [DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md) for detailed instructions.

### Option 1: Using GitHub Actions (Recommended)

1. **Set up GCP and GitHub Secrets**
2. **Push to main branch** - Automatically deploys
3. **Service URL** will be shown in Actions log

### Option 2: Using Terraform

```bash
cd terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply
```

### Option 3: Manual Docker Deployment

```bash
# Build and tag
docker build -t gcr.io/YOUR_PROJECT/aem-mcp-server .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT/aem-mcp-server

# Deploy to Cloud Run
gcloud run deploy aem-assets-mcp-server \
  --image gcr.io/YOUR_PROJECT/aem-mcp-server \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# AEM Instance
AEM_BASE_URL=https://author-p12345-e67890.adobeaemcloud.com

# OAuth Server-to-Server Credentials
AEM_CLIENT_ID=your_client_id_here
AEM_CLIENT_SECRET=your_client_secret_here
```

### Get AEM Credentials

**Quick Setup:**
```bash
./create-env.sh  # Interactive credential setup
```

**Manual Setup:**

See [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) for detailed instructions.

**Summary:**
1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
2. Create/select project
3. Add "AEM Assets Author API"
4. Configure "OAuth Server-to-Server" authentication
5. Copy Client ID and Client Secret
6. Copy Scopes from the credential page

**Key Benefits:**
- ✅ Automatic token refresh (every ~1 hour)
- ✅ No manual token management
- ✅ Production-ready authentication
- ✅ Based on [Adobe's OAuth S2S guide](https://experienceleague.adobe.com/en/docs/experience-manager-learn/cloud-service/aem-apis/openapis/invoke-api-using-oauth-s2s)

## 🤖 Connect to ChatGPT

See [CHATGPT_SETUP.md](./CHATGPT_SETUP.md) for complete integration guide.

**Quick summary**:
1. Create Custom GPT in ChatGPT
2. Add Action with OpenAPI schema
3. Point to your deployed URL
4. Test with natural language prompts

## 💬 Usage Examples

Once connected to ChatGPT:

```
✅ "List all the folders in the root directory"
✅ "Show me all published assets"
✅ "Find assets related to Electric Vehicle"
✅ "Update all assets in /content/dam/products with jancode: ABCDEFG"
✅ "List all assets uploaded by user@example.com"
```

## 🔌 API Reference

### Endpoints

- `GET /` - Server information
- `GET /api/mcp` - Server information
- `POST /api/mcp` - Execute MCP tool
- `GET /health` - Health check

### Available Tools

#### 1. `list_folders`
```json
{
  "tool": "list_folders",
  "arguments": {
    "path": "/content/dam"
  }
}
```

#### 2. `list_published_assets`
```json
{
  "tool": "list_published_assets",
  "arguments": {
    "limit": 50
  }
}
```

#### 3. `search_assets`
```json
{
  "tool": "search_assets",
  "arguments": {
    "query": "Electric Vehicle",
    "limit": 100
  }
}
```

#### 4. `list_assets_by_folder`
```json
{
  "tool": "list_assets_by_folder",
  "arguments": {
    "folderPath": "/content/dam/products"
  }
}
```

#### 5. `bulk_update_metadata`
```json
{
  "tool": "bulk_update_metadata",
  "arguments": {
    "folderPath": "/content/dam/products",
    "metadata": {
      "jancode": "ABCDEFG",
      "category": "Electronics"
    }
  }
}
```

#### 6. `list_assets_by_creator`
```json
{
  "tool": "list_assets_by_creator",
  "arguments": {
    "createdBy": "user@example.com",
    "limit": 50
  }
}
```

#### 7. `list_all_assets`
```json
{
  "tool": "list_all_assets",
  "arguments": {
    "path": "/content/dam",
    "limit": 200
  }
}
```

#### 8. `get_asset_details`
```json
{
  "tool": "get_asset_details",
  "arguments": {
    "assetId": "urn:aaid:aem:12345"
  }
}
```

## 🧪 Testing

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test tool call
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_folders",
    "arguments": {"path": "/"}
  }'
```

### Run Tests (when available)
```bash
pytest tests/ -v
```

## 🔐 Security

- ✅ Environment variables for credentials
- ✅ CORS configured for API access
- ✅ Secret Manager for Cloud Run
- ✅ Service Account with minimal permissions
- ✅ HTTPS enforced

**Important**: 
- Never commit `.env` or `terraform.tfvars`
- Rotate AEM tokens regularly
- Use Workload Identity Federation for GitHub Actions
- Restrict Cloud Run access as needed

## 🐛 Troubleshooting

### Common Issues

**Import errors in FastAPI**:
```bash
pip install --upgrade -r requirements.txt
```

**Docker build fails**:
```bash
# Check Docker is running
docker ps

# Build with no cache
docker build --no-cache -t aem-mcp-server .
```

**Terraform errors**:
```bash
# Re-initialize
cd terraform
rm -rf .terraform
terraform init
```

**Cloud Run deployment fails**:
- Check Secret Manager has correct values
- Verify service account permissions
- Check Artifact Registry has image
- Review Cloud Run logs

## 📚 Additional Documentation

- [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md) - Phase 1 deployment guide
- [DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md) - Phase 2 deployment guide
- [CHATGPT_SETUP.md](./CHATGPT_SETUP.md) - ChatGPT integration guide
- [AEM Assets API Docs](https://developer.adobe.com/experience-cloud/experience-manager-apis/api/stable/assets/author/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Run](https://cloud.google.com/run)
- [Terraform Documentation](https://www.terraform.io/docs)
- [Adobe Developer Console](https://developer.adobe.com/console)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## 💡 Tips

1. **Start with Phase 1** (Vercel) for quick testing
2. **Use Terraform** for reproducible infrastructure
3. **Monitor logs** in Cloud Run console
4. **Set up alerts** for production deployments
5. **Use Secret Manager** for all sensitive data

---

**Need Help?** Check the documentation files or open an issue on GitHub.
