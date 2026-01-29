# AEM Assets Server for AI Integrations

A dual-implementation server for Adobe Experience Manager (AEM) Assets API:
- **REST API** (`rest-api/`) - For ChatGPT Custom GPTs via Actions (FastAPI)
- **MCP Server** (`mcp-server/`) - For ChatGPT Custom GPTs with MCP support (FastMCP)

Both implementations share the same core AEM client logic and provide identical functionality.

## 🏗️ Architecture

```
aem-assets-mcp-server/
├── rest-api/              ← REST API implementation (Vercel)
│   ├── app/              - FastAPI application
│   ├── requirements.txt
│   └── vercel.json
├── mcp-server/            ← MCP Server implementation (Cloud Run)
│   ├── app/              - FastMCP application
│   ├── Dockerfile
│   └── requirements.txt
├── shared/                ← Common AEM client logic
│   ├── aem_client.py     - AEM API client
│   ├── jwt_auth.py       - JWT authentication
│   ├── models.py         - Data models
│   └── constants.py      - Configuration constants
└── .github/workflows/    - CI/CD pipelines
```

## 🚀 Features

Both implementations provide identical tools to interact with AEM Assets:

- **List folders** - Browse folders in your AEM Assets repository
- **List assets by folder** - Get all assets within a specific folder
- **Get asset details** - Retrieve detailed information about a specific asset including metadata
- **Update asset metadata** - Update metadata fields for individual assets
- **Bulk update metadata** - Update metadata for all assets in a folder

## 🎯 Which Implementation Should I Use?

| Feature | REST API (Vercel) | MCP Server (Cloud Run) |
|---------|-------------------|------------------------|
| **Target Platform** | ChatGPT Actions | ChatGPT with MCP support |
| **Protocol** | HTTP REST | JSON-RPC over SSE |
| **Deployment** | Vercel (serverless) | Google Cloud Run (containers) |
| **Schema** | OpenAPI 3.0 | MCP Protocol |
| **Best For** | Standard ChatGPT integrations | Native MCP clients (ChatGPT, Claude Desktop) |

**Recommendation:** 
- Use **REST API** if you're integrating with ChatGPT Custom GPTs via Actions (most common)
- Use **MCP Server** if your ChatGPT supports native MCP protocol connections

## 📋 Prerequisites

### AEM Access
1. **Adobe Experience Manager Assets Author API Access**
   - AEM base URL (e.g., `https://author-pXXXXXX-eXXXXXXX.adobeaemcloud.com`)
   - **OAuth Server-to-Server credentials** (for modern `/adobe/*` APIs):
     - Client ID
     - Client Secret
   - **JWT Service Account credentials** (for classic `/api/assets` API):
     - Service Account JSON file with private key
   - See [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) for detailed setup

### REST API Requirements
- Python 3.12+
- Vercel account (for deployment)
- ChatGPT Plus/Pro with Custom GPTs

### MCP Server Requirements
- Python 3.12+
- Docker
- Google Cloud Platform account
- `gcloud` CLI
- GitHub account (for CI/CD)

## 🛠️ Tech Stack

### Shared Components
- **Python 3.12** - Core language
- **HTTPX** - Async HTTP client
- **Pydantic** - Data validation
- **Dual Authentication**:
  - OAuth Server-to-Server (modern AEM APIs)
  - JWT Service Account (classic AEM APIs)

### REST API Stack
- **FastAPI** - Modern async web framework
- **Vercel** - Serverless deployment

### MCP Server Stack
- **FastMCP** - MCP protocol implementation
- **Docker** - Containerization
- **Google Cloud Run** - Container hosting
- **Terraform** - Infrastructure as Code
- **GitHub Actions** - CI/CD

## 📁 Project Structure

```
.
├── rest-api/                     # REST API Implementation (Vercel)
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI application
│   ├── requirements.txt
│   ├── vercel.json              # Vercel deployment config
│   └── openapi-schema.json      # ChatGPT Actions schema
├── mcp-server/                   # MCP Server Implementation (Cloud Run)
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # FastMCP application
│   ├── requirements.txt
│   └── Dockerfile               # Container configuration
├── shared/                       # Shared AEM Client Logic
│   ├── __init__.py
│   ├── aem_client.py            # AEM API client (OAuth + JWT)
│   ├── jwt_auth.py              # JWT Service Account auth
│   ├── models.py                # Pydantic data models
│   └── constants.py             # Configuration constants
├── terraform/                    # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars.example
├── .github/workflows/            # CI/CD Pipelines
│   ├── deploy-cloud-run.yml     # MCP Server → Cloud Run
│   ├── terraform-apply.yml      # Terraform deployment
│   └── test.yml                 # Testing workflow
├── vercel.json                  # Root Vercel config (points to rest-api/)
└── README.md
```

## 🚀 Quick Start

Choose your implementation path:

### Option A: REST API for ChatGPT Actions

#### Local Development

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
pip install -r rest-api/requirements.txt
```

4. **Configure environment**:
```bash
# Copy example env
cp rest-api/env.example .env

# Edit with your AEM credentials
# Required:
# - AEM_BASE_URL
# - AEM_CLIENT_ID
# - AEM_CLIENT_SECRET
# - AEM_SERVICE_ACCOUNT_JSON (path to service-account.json)
nano .env
```

See [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) for how to get your credentials.

5. **Run REST API locally**:
```bash
cd rest-api
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to see the server info.

#### Deploy to Vercel

See [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md) for detailed instructions.

**Option A: Local Deployment (Fastest)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy (from project root)
vercel

# Add environment variables via Vercel dashboard:
# - AEM_BASE_URL
# - AEM_CLIENT_ID  
# - AEM_CLIENT_SECRET
# - AEM_SERVICE_ACCOUNT_JSON (paste JSON content)

# Deploy to production
vercel --prod
```

**Option B: GitHub Actions (Automated CI/CD)**

Set up once, then automatically deploy on every push to `main`:

1. Get Vercel credentials (see [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md#option-3-github-actions-automated-cicd))
2. Add GitHub Secrets:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
3. Push to `main` or manually trigger workflow

Your API will be available at: `https://your-project.vercel.app/api/mcp`

Use the OpenAPI schema at `rest-api/openapi-schema.json` to configure ChatGPT Actions.

---

### Option B: MCP Server for Native MCP Support

#### Local Development

1. **Install MCP server dependencies**:
```bash
pip install -r mcp-server/requirements.txt
```

2. **Configure environment** (same as REST API):
```bash
cp rest-api/env.example .env
nano .env  # Add your AEM credentials
```

3. **Run MCP server locally**:
```bash
cd mcp-server
python -m app.main
```

The MCP server will start with SSE transport on port 8080.

#### Deploy to Google Cloud Run

See [DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md) for detailed instructions.

**Quick steps using GitHub Actions**:

1. **Set up GCP project and enable APIs**
2. **Configure Workload Identity Federation** (see [CLOUD_RUN_SETUP_GUIDE.md](./CLOUD_RUN_SETUP_GUIDE.md))
3. **Add GitHub Secrets**:
   - `GCP_PROJECT_ID`
   - `GCP_REGION`
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
   - `AEM_BASE_URL`
   - `AEM_CLIENT_ID`
4. **Create GCP secrets**:
   ```bash
   echo -n "your_client_secret" | gcloud secrets create aem-client-secret --data-file=-
   echo -n "$(cat service-account.json)" | gcloud secrets create aem-service-account-json --data-file=-
   ```
5. **Trigger deployment**:
   - Go to GitHub Actions → "Deploy to Google Cloud Run" → "Run workflow"

Your MCP server will be available at: `https://aem-assets-mcp-server-xxxxx.run.app`

Connect from ChatGPT using the MCP server URL.

---

## 🧪 Testing

### Test REST API

```bash
# List folders
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_folders", "arguments": {"path": "/"}}'

# List assets in a folder
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_assets_by_folder", "arguments": {"folderPath": "/MyFolder"}}'
```

### Test MCP Server

See [TESTING.md](./TESTING.md) for comprehensive testing guide including:
- Direct AEM API testing
- JWT token generation
- MCP Inspector usage

---

## 🔧 Configuration

Both implementations use the same environment variables:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `AEM_BASE_URL` | AEM Author instance URL | ✅ | `https://author-pXXXXXX.adobeaemcloud.com` |
| `AEM_CLIENT_ID` | OAuth Client ID | ✅ | `a41e805f8c3042d3bba66ff1c05f1e94` |
| `AEM_CLIENT_SECRET` | OAuth Client Secret | ✅ | `p8e-xxx...` |
| `AEM_SERVICE_ACCOUNT_JSON` | JWT Service Account (file path or JSON string) | ✅ | `./service-account.json` |

**API endpoints and scopes** are configured in `shared/constants.py`:
- Modern API: `/adobe/assets`, `/adobe/folders` (OAuth)
- Classic API: `/api/assets` (JWT)
- IMS Token: `https://ims-na1.adobelogin.com/ims/token/v3`
- Scopes: `openid,AdobeID,aem.assets.author,aem.folders`

---

## 📚 Documentation

- [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) - How to obtain AEM credentials
- [JWT_SETUP.md](./JWT_SETUP.md) - JWT Service Account setup
- [DEPLOYMENT_VERCEL.md](./DEPLOYMENT_VERCEL.md) - REST API deployment to Vercel
- [DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md) - MCP Server deployment to Cloud Run
- [CLOUD_RUN_SETUP_GUIDE.md](./CLOUD_RUN_SETUP_GUIDE.md) - Detailed Cloud Run setup
- [TESTING.md](./TESTING.md) - Testing guide
- [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md) - Local development tips

---

## 🤝 ChatGPT Integration

### For REST API (ChatGPT Actions)
1. Create a Custom GPT in ChatGPT
2. Go to "Configure" → "Actions"
3. Import the schema from `rest-api/openapi-schema.json`
4. Set the server URL to your Vercel deployment
5. Test with prompts like:
   - "List all folders in /content/dam/"
   - "Show me assets in the MyFolder folder"
   - "Update the description for asset XYZ"

### For MCP Server (Native MCP)
1. Create a Custom GPT in ChatGPT with MCP support
2. Configure MCP connection with your Cloud Run URL
3. The MCP server will automatically expose all tools
4. Test with the same natural language prompts

---

## 🔐 Security Notes

- Never commit `.env` files or `service-account.json`
- Use GitHub Secrets for CI/CD
- Use GCP Secret Manager for Cloud Run
- Use Vercel environment variables for Vercel deployment
- Rotate credentials regularly
- Review AEM user permissions

---

## 🐛 Troubleshooting

### Common Issues

**Issue: JWT authentication not working in Cloud Run**
- **Cause**: `AEM_SERVICE_ACCOUNT_JSON` must contain JSON string, not file path
- **Fix**: Create secret with JSON content: `gcloud secrets create aem-service-account-json --data-file=service-account.json`

**Issue: Permission denied on Secret Manager**
- **Cause**: Cloud Run service account lacks permissions
- **Fix**: Grant `roles/secretmanager.secretAccessor`:
  ```bash
  gcloud secrets add-iam-policy-binding aem-client-secret \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
  ```

**Issue: 403 Forbidden from AEM**
- **Cause**: Incorrect authentication or insufficient permissions
- **Fix**: Verify credentials, check AEM user has correct Product Profile (AEM Administrators)

**Issue: Vercel deployment fails**
- **Cause**: Path issues after restructure
- **Fix**: Ensure `vercel.json` points to `rest-api/app/main.py`

See [TESTING.md](./TESTING.md) for more troubleshooting steps.

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Adobe Experience Manager Assets API
- FastAPI and FastMCP teams
- Model Context Protocol specification

---

## Option 2: Using Terraform

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

---

Made with ❤️ for AEM + AI Integration
