# Phase 1: Vercel Deployment Guide

Quick deployment guide for deploying the AEM Assets MCP Server to Vercel.

## 📋 Prerequisites

- Vercel account (free tier works)
- Git repository (GitHub, GitLab, or Bitbucket)
- AEM Assets API credentials

## 🚀 Quick Deployment

### Option 1: Vercel CLI (Fastest)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy (from project root)
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Link to existing project? No
# - Project name? (accept default or customize)
# - Directory? ./
# - Override settings? No

# You'll get a preview URL
```

### Option 2: Vercel Dashboard

1. Go to [vercel.com](https://vercel.com/new)
2. Click "Import Project"
3. Select your Git provider (GitHub/GitLab/Bitbucket)
4. Import your repository
5. Configure:
   - **Framework Preset**: Other
   - **Build Command**: `pip install -r requirements.txt` (auto-detected)
   - **Output Directory**: Leave empty
   - **Install Command**: Auto-detected
6. Click "Deploy"

### Option 3: GitHub Actions (Automated CI/CD)

Automatically deploy to Vercel whenever you push changes to `main` branch or manually trigger deployment.

#### Setup Steps:

1. **Get Vercel Credentials**

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Login to Vercel
vercel login

# Link your project (run from project root)
vercel link

# This creates .vercel directory with:
# - project.json (contains projectId)
# - README.txt
```

2. **Get Your Vercel Organization ID**

```bash
# View your .vercel/project.json
cat .vercel/project.json
```

You'll see something like:
```json
{
  "orgId": "team_xxxxxxxxxxxxx",
  "projectId": "prj_xxxxxxxxxxxxx"
}
```

3. **Get Your Vercel Token**

- Go to [Vercel Account Settings → Tokens](https://vercel.com/account/tokens)
- Click "Create Token"
- Name it: `GitHub Actions Deploy`
- Set scope: Full Account (or select specific projects)
- Click "Create"
- Copy the token (you'll only see it once!)

4. **Add GitHub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these three secrets:

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `VERCEL_TOKEN` | `xxx...xxx` | From step 3 above |
| `VERCEL_ORG_ID` | `team_xxx...` | From `.vercel/project.json` (`orgId`) |
| `VERCEL_PROJECT_ID` | `prj_xxx...` | From `.vercel/project.json` (`projectId`) |

5. **Configure Environment Variables in Vercel**

The GitHub Action will use the environment variables already configured in your Vercel project. Make sure you've added them via:
- Vercel Dashboard → Project → Settings → Environment Variables
- Or via CLI: `vercel env add AEM_BASE_URL production`

6. **Trigger Deployment**

The workflow will automatically deploy when:
- ✅ You push changes to `main` branch that affect:
  - `rest-api/**`
  - `shared/**`
  - `vercel.json`
  - `.github/workflows/deploy-vercel.yml`
- ✅ You manually trigger it:
  - Go to GitHub → Actions → "Deploy REST API to Vercel" → "Run workflow"

#### Workflow Features:

- ✅ Automatic deployment on push to `main`
- ✅ Manual deployment via workflow_dispatch
- ✅ Automatic testing after deployment
- ✅ Deployment URL in action logs
- ✅ PR comments with deployment URL (for PRs)

#### View Deployment Status:

1. Go to GitHub → Actions
2. Click on the latest "Deploy REST API to Vercel" workflow run
3. View logs and deployment URL

## 🔧 Configure Environment Variables

After deployment, add environment variables:

### Via Vercel Dashboard

1. Go to your project → Settings → Environment Variables
2. Add each variable:

| Variable Name | Value | Environment |
|---------------|-------|-------------|
| `AEM_BASE_URL` | `https://author-p12345-e67890.adobeaemcloud.com` | Production, Preview, Development |
| `AEM_CLIENT_ID` | Your OAuth Client ID (API Key) | Production, Preview, Development |
| `AEM_CLIENT_SECRET` | Your OAuth Client Secret | Production, Preview, Development |
| `AEM_SERVICE_ACCOUNT_JSON` | Paste entire service account JSON content | Production, Preview, Development |

**Important Notes:**
- `AEM_BASE_URL`: Do NOT include `/api/v1` or trailing slash
- `AEM_SERVICE_ACCOUNT_JSON`: Paste the entire JSON file content (for JWT authentication with classic `/api/assets` API)
- See [GET_CREDENTIALS.md](./GET_CREDENTIALS.md) for how to obtain these credentials

3. Click "Save"

### Via Vercel CLI

```bash
# Add base URL
vercel env add AEM_BASE_URL production
# Enter: https://author-p12345-e67890.adobeaemcloud.com

# Add OAuth credentials
vercel env add AEM_CLIENT_ID production
# Enter your Client ID

vercel env add AEM_CLIENT_SECRET production
# Enter your Client Secret

# Add JWT Service Account JSON
vercel env add AEM_SERVICE_ACCOUNT_JSON production
# Paste the entire JSON content from service-account.json
```

**Pro Tip:** For `AEM_SERVICE_ACCOUNT_JSON`, you can use:
```bash
cat service-account.json | pbcopy  # macOS - copies to clipboard
# Then paste into Vercel CLI prompt
```

## 🎯 Deploy to Production

```bash
# Deploy to production
vercel --prod
```

Your production URL: `https://your-project.vercel.app`

## ✅ Verify Deployment

### Test Health Endpoint

```bash
curl https://your-project.vercel.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "aem-assets-mcp-server"
}
```

### Test Server Info

```bash
curl https://your-project.vercel.app/api/mcp
```

Expected response:
```json
{
  "name": "aem-assets-mcp-server",
  "version": "1.0.0",
  "description": "MCP Server for Adobe Experience Manager Assets Author API",
  "tools": [
    "list_folders",
    "list_published_assets",
    "search_assets",
    "list_assets_by_folder",
    "bulk_update_metadata",
    "list_assets_by_creator",
    "list_all_assets",
    "get_asset_details"
  ]
}
```

### Test Tool Call

```bash
curl -X POST https://your-project.vercel.app/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_folders",
    "arguments": {"path": "/"}
  }'
```

## 🔄 Automatic Deployments

Vercel automatically deploys when you push to Git:

- **Push to `main`** → Production deployment
- **Push to other branches** → Preview deployment
- **Pull requests** → Preview deployment with unique URL

## 📝 Configuration File

The `vercel.json` file configures Vercel deployment:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

## 🔐 Security

### Environment Variable Best Practices

1. **Never commit** `.env` files
2. **Use Vercel secrets** for sensitive data:
   ```bash
   vercel secrets add aem-access-token "your_token"
   ```
3. **Rotate tokens** regularly
4. **Use different tokens** for development/production

### Access Control

Vercel deployments are public by default. To restrict access:

1. **Vercel Password Protection** (Pro plan):
   - Project Settings → Password Protection
   - Enable and set password

2. **Add API Key Authentication** in code:
   ```python
   # In app/main.py
   API_KEY = os.getenv("API_KEY")
   
   @app.middleware("http")
   async def verify_api_key(request: Request, call_next):
       if request.url.path.startswith("/api"):
           api_key = request.headers.get("X-API-Key")
           if api_key != API_KEY:
               return JSONResponse(
                   status_code=401,
                   content={"error": "Unauthorized"}
               )
       return await call_next(request)
   ```

## 📊 Monitoring

### View Logs

1. Go to project → Deployments
2. Click on deployment
3. View "Functions" tab for logs

### Deployment Logs

```bash
# Stream logs
vercel logs your-project.vercel.app
```

### Analytics (Pro plan)

- Go to project → Analytics
- View request counts, response times, errors

## 🐛 Troubleshooting

### Build Fails

**Error**: `ERROR: Could not find a version that satisfies requirement`

**Solution**:
```bash
# Ensure requirements.txt is correct
pip freeze > requirements.txt

# Commit and redeploy
git add requirements.txt
git commit -m "Fix requirements"
git push
```

### Function Timeout

**Error**: `FUNCTION_INVOCATION_TIMEOUT`

**Solution**: 
- Hobby plan: 10s timeout (cannot increase)
- Pro plan: Increase in `vercel.json`:
  ```json
  {
    "functions": {
      "app/main.py": {
        "maxDuration": 60
      }
    }
  }
  ```

### Environment Variables Not Working

**Solution**:
1. Verify variables are set for correct environment
2. Redeploy after adding variables:
   ```bash
   vercel --prod
   ```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Ensure `vercel.json` routes are correct and Python path is set.

## 💰 Costs

### Vercel Pricing

**Hobby (Free)**:
- 100 GB bandwidth/month
- Unlimited deployments
- Serverless function execution included
- 10s function timeout

**Pro ($20/month)**:
- 1 TB bandwidth/month
- 60s function timeout
- Password protection
- Analytics

See [vercel.com/pricing](https://vercel.com/pricing) for details.

## 🔄 Updating Deployment

### Update Code

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Vercel deploys automatically
```

### Update Environment Variables

1. Dashboard: Settings → Environment Variables → Edit
2. Redeploy:
   ```bash
   vercel --prod
   ```

### Rollback

1. Go to Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

Or via CLI:
```bash
vercel rollback
```

## 🌐 Custom Domain

### Add Custom Domain

1. Go to project → Settings → Domains
2. Add domain (e.g., `aem-api.yourdomain.com`)
3. Configure DNS:
   - **CNAME**: Point to `cname.vercel-dns.com`
   - Or follow Vercel's DNS instructions
4. Wait for DNS propagation (up to 48 hours)

### SSL Certificate

Vercel automatically provisions SSL certificates for custom domains.

## 🚀 Performance Tips

### Enable Caching

Add caching headers for read-only operations:

```python
# In app/main.py
@app.get("/api/mcp")
async def get_server_info(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return ServerInfo()
```

### Use Edge Functions (Pro)

Convert to Edge Functions for faster cold starts:

```json
{
  "functions": {
    "app/main.py": {
      "runtime": "edge"
    }
  }
}
```

### Optimize Response Size

- Use compression middleware
- Paginate large responses
- Return only necessary fields

## 📈 Scaling

Vercel automatically scales serverless functions:

- **Concurrent requests**: Unlimited on Pro
- **Regional**: Automatically deployed globally
- **CDN**: Built-in edge caching

No configuration needed - it just works!

## 🔗 Integration with ChatGPT

Once deployed, use your Vercel URL in ChatGPT:

```
https://your-project.vercel.app/api/mcp
```

See [CHATGPT_SETUP.md](./CHATGPT_SETUP.md) for complete integration guide.

## 📚 Next Steps

1. ✅ Deploy to Vercel
2. ✅ Configure environment variables
3. ✅ Test all endpoints
4. ✅ Set up ChatGPT integration
5. ✅ Monitor usage and logs
6. ✅ Consider Phase 2 (Cloud Run) for more control

## 🆚 Vercel vs Cloud Run

| Feature | Vercel | Cloud Run |
|---------|--------|-----------|
| **Setup Time** | 2 minutes | 15-30 minutes |
| **Cost** | $0-20/month | $0-50/month |
| **Scaling** | Automatic | Automatic |
| **Timeout** | 10s (60s Pro) | 60s (900s max) |
| **Control** | Limited | Full |
| **CI/CD** | Built-in | Setup required |
| **Best For** | Quick prototypes | Production systems |

For most use cases, **start with Vercel (Phase 1)** then migrate to **Cloud Run (Phase 2)** if you need more control.

---

**Need help?** Check the [main README](./README.md) or [Cloud Run guide](./DEPLOYMENT_CLOUDRUN.md).
