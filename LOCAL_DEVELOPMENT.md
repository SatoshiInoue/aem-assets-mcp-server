# Local Development Guide

Guide for running and developing the AEM Assets MCP Server locally.

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Navigate to project
cd "SC Practice 20260130 - Assets MCP"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit with your credentials
nano .env
```

Fill in your AEM credentials:
```env
AEM_BASE_URL=https://author-p12345-e67890.adobeaemcloud.com/api/v1
AEM_ACCESS_TOKEN=your_access_token_here
AEM_ORG_ID=your_org_id@AdobeOrg
AEM_CLIENT_ID=your_client_id_here
```

### 3. Run the Server

```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Or run directly
python -m app.main
```

Server will start at: `http://localhost:8000`

## 🧪 Testing Locally

### Test Server Info

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "name": "aem-assets-mcp-server",
  "version": "1.0.0",
  "description": "MCP Server for Adobe Experience Manager Assets Author API",
  "tools": [...]
}
```

### Test Health Check

```bash
curl http://localhost:8000/health
```

### Test Tool Calls

```bash
# List folders
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_folders",
    "arguments": {"path": "/"}
  }'

# Search assets
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_assets",
    "arguments": {"query": "test", "limit": 10}
  }'
```

## 🐳 Docker Development

### Build and Run

```bash
# Build Docker image
docker build -t aem-mcp-local .

# Run container
docker run -p 8080:8080 \
  --env-file .env \
  aem-mcp-local

# Or with individual env vars
docker run -p 8080:8080 \
  -e AEM_BASE_URL="your_url" \
  -e AEM_ACCESS_TOKEN="your_token" \
  -e AEM_ORG_ID="your_org_id" \
  -e AEM_CLIENT_ID="your_client_id" \
  aem-mcp-local
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  aem-mcp-server:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    restart: unless-stopped
```

Run:
```bash
docker-compose up
```

## 🔧 Development Tools

### Install Dev Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov httpx black ruff mypy
```

### Code Formatting

```bash
# Format with Black
black app/

# Lint with Ruff
ruff check app/

# Type check with mypy
mypy app/ --ignore-missing-imports
```

### Testing

Create `tests/test_main.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "aem-assets-mcp-server"

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

Run tests:
```bash
pytest tests/ -v
```

## 📝 Project Structure Explained

```
app/
├── __init__.py          # Package initialization
├── main.py              # FastAPI app & routes
├── aem_client.py        # AEM API client
└── models.py            # Pydantic models

Key files:
- main.py: Defines all endpoints and tool handlers
- aem_client.py: Handles AEM API communication
- models.py: Data validation and serialization
```

## 🛠️ Common Development Tasks

### Add a New Tool

1. **Add model** in `app/models.py` (if needed)

2. **Add client method** in `app/aem_client.py`:
```python
async def new_operation(self, param: str) -> List[Asset]:
    response = await self.client.get("/endpoint", params={"param": param})
    return [self._map_asset(item) for item in response.json()["items"]]
```

3. **Add endpoint** in `app/main.py`:
```python
elif tool == "new_tool":
    param = args.get("param")
    if not param:
        raise HTTPException(status_code=400, detail="param required")
    result = await aem_client.new_operation(param)
    return ToolResponse(result=[asset.model_dump() for asset in result])
```

4. **Update ServerInfo** tools list

5. **Test locally**

### Debug Requests

Enable detailed logging:

```python
# In app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

### Hot Reload

With `--reload` flag, the server automatically restarts on file changes:

```bash
uvicorn app.main:app --reload --port 8000
```

## 🐛 Common Issues

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Run from project root, not from `app/` directory

### Environment Variables Not Loading

**Error**: `Missing required environment variable`

**Solution**:
```bash
# Check .env exists
ls -la .env

# Manually load for testing
export AEM_BASE_URL="your_url"
```

### Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 PID

# Or use different port
uvicorn app.main:app --port 8001
```

### AEM Connection Errors

**Error**: `Failed to list folders: 401 Unauthorized`

**Solution**:
- Check access token is valid (tokens expire)
- Verify base URL is correct
- Ensure Organization ID matches
- Confirm Client ID is correct

## 💡 Tips & Tricks

### 1. Use HTTPie for Pretty Requests

```bash
pip install httpie

# Pretty formatted requests
http POST localhost:8000/api/mcp \
  tool=list_folders \
  arguments:='{"path": "/"}'
```

### 2. Interactive API Docs

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### 4. Environment Switching

Use multiple `.env` files:

```bash
# Development
cp .env.example .env.dev

# Production
cp .env.example .env.prod

# Load specific env
uvicorn app.main:app --env-file .env.dev
```

### 5. Quick Health Check Script

Create `check_health.sh`:

```bash
#!/bin/bash
curl -s http://localhost:8000/health | jq
```

Make executable:
```bash
chmod +x check_health.sh
./check_health.sh
```

## 📚 Next Steps

1. ✅ Set up local environment
2. ✅ Run and test locally
3. ✅ Make code changes
4. ✅ Test changes
5. ✅ Deploy to Vercel or Cloud Run
6. ✅ Integrate with ChatGPT

---

**Need help?** Check the [main README](./README.md) or deployment guides.
