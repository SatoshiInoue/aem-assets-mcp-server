# Google Cloud Run Deployment - Complete Setup Guide

## 📋 Overview

This guide covers everything you need to deploy your AEM Assets MCP Server to Google Cloud Run, including handling sensitive credentials and choosing the right deployment method.

---

## 🔐 Question 1: How to Handle service-account.json?

### The Challenge
The `service-account.json` file contains:
- Private RSA keys
- Client secrets
- Technical account credentials

**This file is gitignored and should NEVER be committed to Git.**

### ✅ Recommended Solution: Use GitHub Secrets + GCP Secret Manager

#### Step 1: Store in GitHub Secrets (for CI/CD)

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `AEM_SERVICE_ACCOUNT_JSON`
5. Value: **Paste the entire contents of your `service-account.json` file**

```bash
# Quick way to copy the contents (macOS)
cat service-account.json | pbcopy

# Linux
cat service-account.json | xclip -selection clipboard

# Or manually open the file and copy all contents
```

#### Step 2: Store in GCP Secret Manager (for runtime)

```bash
# Create secret in GCP from your local file
gcloud secrets create aem-service-account-json \
  --data-file=./service-account.json \
  --replication-policy=automatic

# Verify it was created
gcloud secrets describe aem-service-account-json
```

#### Step 3: Grant Cloud Run Access to the Secret

```bash
# Get your Cloud Run service account
export SERVICE_ACCOUNT=$(gcloud run services describe aem-assets-mcp-server \
  --region us-central1 \
  --format 'value(spec.template.spec.serviceAccountName)' \
  2>/dev/null || echo "$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')-compute@developer.gserviceaccount.com")

# Grant access to the secret
gcloud secrets add-iam-policy-binding aem-service-account-json \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### 🔒 Security Best Practices

✅ **DO**:
- Store in GitHub Secrets for CI/CD
- Store in GCP Secret Manager for runtime
- Keep the local file gitignored
- Rotate credentials periodically
- Use least-privilege IAM permissions

❌ **DON'T**:
- Commit to Git (even private repos)
- Share via email or Slack
- Store in plain environment variables
- Include in Docker images
- Log the contents

---

## 🚫 Question 2: Auto-Execution Removed

### What Changed?

The GitHub Actions workflow **no longer triggers automatically** on push to `main`.

**Before** (`.github/workflows/deploy-cloud-run.yml`):
```yaml
on:
  push:
    branches:
      - main
  workflow_dispatch:
```

**After**:
```yaml
on:
  workflow_dispatch:  # Manual trigger only
```

### How to Deploy Manually

1. Go to your GitHub repository
2. Click the **Actions** tab
3. Select **"Deploy to Google Cloud Run"** workflow
4. Click **"Run workflow"** button
5. Select branch (usually `main`)
6. Click **"Run workflow"** green button

This gives you full control over when deployments happen! 🎯

---

## 🔀 Question 3: Deployment Options Comparison

You have **3 ways** to deploy to Google Cloud Run. Here's when to use each:

### Option A: GitHub Actions (Recommended for Production)

**What it does**:
- Builds Docker image
- Pushes to GCP Artifact Registry
- Deploys to Cloud Run
- Runs health checks

**Pros**:
- ✅ Fully automated CI/CD
- ✅ No local Docker/GCP setup needed
- ✅ Consistent deployments
- ✅ Built-in health checks
- ✅ Deployment history in GitHub

**Cons**:
- ❌ Requires GCP Workload Identity setup
- ❌ More initial configuration

**When to use**:
- Production deployments
- Team environments
- You want automation
- You don't have GCP CLI locally

**Workflow**: `.github/workflows/deploy-cloud-run.yml`

---

### Option B: Terraform + GitHub Actions (Recommended for Infrastructure Management)

**What it does**:
- Manages all GCP infrastructure as code
- Creates Cloud Run service, Artifact Registry, Secret Manager, etc.
- Allows plan/apply/destroy operations
- Can be run via GitHub Actions or locally

**Pros**:
- ✅ Infrastructure as Code (reproducible)
- ✅ Easy to replicate to dev/staging/prod
- ✅ Version controlled infrastructure
- ✅ Can destroy everything cleanly
- ✅ Team can review infrastructure changes

**Cons**:
- ❌ More complex setup
- ❌ Need to learn Terraform syntax
- ❌ State management required

**When to use**:
- Managing multiple environments (dev/staging/prod)
- Infrastructure needs to be version controlled
- Team needs to review infrastructure changes
- You want reproducible deployments
- You need to frequently tear down and rebuild

**Workflow**: `.github/workflows/terraform-apply.yml`

**Key Difference from Option A**:
- Option A deploys **application code** to existing infrastructure
- Option B manages **both infrastructure AND application**

---

### Option C: Manual gcloud Commands (Recommended for Testing)

**What it does**:
- You manually build and push Docker image
- You manually deploy to Cloud Run
- Full control over every step

**Pros**:
- ✅ Simple and direct
- ✅ Good for learning
- ✅ Quick iterations during development
- ✅ No GitHub Actions setup needed

**Cons**:
- ❌ Manual process (error-prone)
- ❌ Requires local Docker + gcloud CLI
- ❌ No deployment history
- ❌ Not reproducible

**When to use**:
- Local development and testing
- Quick experiments
- Learning how Cloud Run works
- One-off deployments

**Command**:
```bash
# Build and push
docker build -t us-central1-docker.pkg.dev/PROJECT_ID/aem-mcp-images/aem-mcp-server:latest .
docker push us-central1-docker.pkg.dev/PROJECT_ID/aem-mcp-images/aem-mcp-server:latest

# Deploy
gcloud run deploy aem-assets-mcp-server \
  --image us-central1-docker.pkg.dev/PROJECT_ID/aem-mcp-images/aem-mcp-server:latest \
  --region us-central1 \
  --allow-unauthenticated
```

---

### 📊 Quick Comparison Table

| Feature | GitHub Actions | Terraform | Manual gcloud |
|---------|---------------|-----------|---------------|
| **Automation** | High | Medium | None |
| **Infrastructure as Code** | No | Yes | No |
| **Learning Curve** | Medium | High | Low |
| **Best for** | Production CI/CD | Multi-env management | Quick testing |
| **Setup Time** | 30 mins | 1 hour | 10 mins |
| **Reproducibility** | High | Very High | Low |
| **Team Collaboration** | Excellent | Excellent | Poor |

### 💡 My Recommendation

**Start with**: Manual gcloud (Option C) to understand the basics

**Move to**: GitHub Actions (Option A) for automated deployments

**Consider**: Terraform (Option B) if you need to manage multiple environments or want full IaC

---

## 📝 Question 4: Step-by-Step Guide to Add GitHub Secrets

### Prerequisites

You need:
- Your `service-account.json` file (from Adobe Developer Console)
- Your AEM base URL
- Your AEM OAuth Client ID
- GCP Project ID
- GCP Workload Identity Provider (if using GitHub Actions)

### Steps

#### 1. Navigate to GitHub Secrets

```
Your Repository
  → Settings (top navigation)
    → Secrets and variables (left sidebar)
      → Actions
        → New repository secret (green button)
```

#### 2. Add Each Secret One by One

Add these secrets in order:

##### **Secret 1: GCP_PROJECT_ID**
- Name: `GCP_PROJECT_ID`
- Value: Your GCP project ID (e.g., `my-project-123456`)
- Click **Add secret**

##### **Secret 2: GCP_REGION**
- Name: `GCP_REGION`
- Value: Your preferred Cloud Run region
- Recommended values:
  - `asia-northeast1` (Tokyo, Japan)
  - `asia-northeast2` (Osaka, Japan)
  - `asia-southeast1` (Singapore)
  - `us-central1` (Iowa, USA)
  - `europe-west1` (Belgium)
- Click **Add secret**

##### **Secret 3: GCP_WORKLOAD_IDENTITY_PROVIDER**
- Name: `GCP_WORKLOAD_IDENTITY_PROVIDER`
- Value: Get this by running:
  ```bash
  gcloud iam workload-identity-pools providers describe github-provider \
    --location=global \
    --workload-identity-pool=github-pool \
    --format='value(name)'
  ```
- Should look like: `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`
- Click **Add secret**

##### **Secret 3: GCP_SERVICE_ACCOUNT**
- Name: `GCP_SERVICE_ACCOUNT`
- Value: `github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com`
- Replace `YOUR_PROJECT_ID` with your actual project ID
- Click **Add secret**

##### **Secret 4: AEM_BASE_URL**
- Name: `AEM_BASE_URL`
- Value: `https://author-p12345-e67890.adobeaemcloud.com`
- **No trailing slash!**
- Click **Add secret**

##### **Secret 5: AEM_CLIENT_ID**
- Name: `AEM_CLIENT_ID`
- Value: Your OAuth S2S Client ID from Adobe Developer Console
- Find it in: Developer Console → Your Project → OAuth Server-to-Server → Client ID
- Click **Add secret**

##### **Secret 6: AEM_SERVICE_ACCOUNT_JSON** ⭐ Most Important

- Name: `AEM_SERVICE_ACCOUNT_JSON`
- Value: **The ENTIRE contents of your `service-account.json` file**
- Steps:
  ```bash
  # Open the file
  cat service-account.json
  
  # Or copy to clipboard (macOS)
  cat service-account.json | pbcopy
  ```
- Copy the entire JSON (including `{` and `}`)
- Paste into the "Value" field
- It should start with `{"ok":true,"integration":{...`
- Click **Add secret**

### 3. Verify All Secrets Are Added

You should see 7 secrets listed:
- ✅ GCP_PROJECT_ID
- ✅ GCP_REGION
- ✅ GCP_WORKLOAD_IDENTITY_PROVIDER
- ✅ GCP_SERVICE_ACCOUNT
- ✅ AEM_BASE_URL
- ✅ AEM_CLIENT_ID
- ✅ AEM_SERVICE_ACCOUNT_JSON

### 4. Test the Workflow

1. Go to **Actions** tab
2. Select **"Deploy to Google Cloud Run"**
3. Click **"Run workflow"**
4. Watch the logs to ensure it works!

---

## 🧪 Testing Your Deployment

After deployment, test your service:

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe aem-assets-mcp-server \
  --region us-central1 \
  --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test list folders
curl -X POST $SERVICE_URL/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_folders",
    "arguments": {"path": "/content/dam"}
  }'
```

---

## 🚨 Troubleshooting

### Error: "Secret not found: aem-service-account-json"

**Solution**: Create the secret in GCP Secret Manager:
```bash
gcloud secrets create aem-service-account-json \
  --data-file=./service-account.json
```

### Error: "Permission denied to access secret"

**Solution**: Grant access to Cloud Run service account:
```bash
gcloud secrets add-iam-policy-binding aem-service-account-json \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

### Error: "Invalid service account JSON"

**Solution**: Verify the JSON is valid:
```bash
cat service-account.json | jq .
```

If this errors, your JSON is malformed. Re-download from Adobe Developer Console.

---

## 📚 Related Documentation

- [DEPLOYMENT_CLOUDRUN.md](./DEPLOYMENT_CLOUDRUN.md) - Full deployment guide
- [JWT_SETUP.md](./JWT_SETUP.md) - JWT authentication setup
- [README.md](./README.md) - Main project documentation

---

## ✅ Quick Checklist

Before deploying, ensure you have:

- [ ] `service-account.json` file downloaded locally
- [ ] File is gitignored (never committed)
- [ ] GitHub Secrets configured (all 7 secrets including GCP_REGION)
- [ ] GCP Secret Manager configured
- [ ] Cloud Run service account has secret access
- [ ] Workload Identity Federation set up (for GitHub Actions)
- [ ] GCP APIs enabled (Run, Artifact Registry, Secret Manager)

Ready to deploy! 🚀
