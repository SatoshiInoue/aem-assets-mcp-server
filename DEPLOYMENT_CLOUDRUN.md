# Phase 2: Google Cloud Run Deployment Guide

Complete guide for deploying the AEM Assets MCP Server to Google Cloud Run using Terraform and GitHub Actions.

## 📋 Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Terraform v1.6.0+ installed
- Docker installed
- GitHub account
- AEM Assets API credentials

## 🏗️ Architecture Overview

```
GitHub Repository
    ↓ (push to main)
GitHub Actions
    ↓ (build Docker image)
Artifact Registry
    ↓ (deploy container)
Cloud Run Service
    ↓ (access secrets)
Secret Manager
```

## 🚀 Deployment Options

Choose one of three deployment methods:

1. **GitHub Actions (Recommended)** - Fully automated CI/CD
2. **Terraform** - Infrastructure as Code
3. **Manual gcloud** - Quick testing

---

## Option 1: GitHub Actions (Recommended)

### Step 1: Set Up Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable iamcredentials.googleapis.com
```

### Step 2: Create Artifact Registry

```bash
gcloud artifacts repositories create aem-mcp-images \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for AEM MCP Server"
```

### Step 3: Create Secrets in Secret Manager

```bash
# Create AEM Client Secret (for OAuth S2S authentication)
echo -n "your_aem_client_secret" | gcloud secrets create aem-client-secret \
  --data-file=- \
  --replication-policy=automatic

# Create AEM Service Account JSON (for JWT authentication with classic API)
# This is the entire JSON file content from Adobe Developer Console
gcloud secrets create aem-service-account-json \
  --data-file=./service-account.json \
  --replication-policy=automatic
```

**Important**: Never commit `service-account.json` to Git. It contains private keys and should only exist:
- Locally (gitignored)
- In GitHub Secrets (for CI/CD)
- In GCP Secret Manager (for Cloud Run runtime)

### Step 4: Set Up Workload Identity Federation

This allows GitHub Actions to authenticate to GCP without service account keys.

```bash
# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor" \
  --attribute-condition="assertion.repository=='YOUR_GITHUB_USERNAME/YOUR_REPO_NAME'"

# Bind service account to Workload Identity
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"
```

**Get your Workload Identity Provider name**:
```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format='value(name)'
```

Save this output - you'll need it for GitHub Secrets.

### Step 5: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123456` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Output from Step 4 | `projects/123.../locations/global/...` |
| `GCP_SERVICE_ACCOUNT` | Service account email | `github-actions@my-project.iam.gserviceaccount.com` |
| `AEM_BASE_URL` | Your AEM instance URL (without trailing slash) | `https://author-p12345-e67890.adobeaemcloud.com` |
| `AEM_CLIENT_ID` | OAuth S2S Client ID from Adobe Developer Console | `abc123...` |
| `AEM_SERVICE_ACCOUNT_JSON` | **Entire contents** of service-account.json file | `{"ok":true,"integration":{...}}` |

**How to add AEM_SERVICE_ACCOUNT_JSON**:
```bash
# Copy the entire JSON content to clipboard
cat service-account.json | pbcopy  # macOS
# Or just copy the file contents manually

# Then paste into GitHub Secrets > New secret
# Name: AEM_SERVICE_ACCOUNT_JSON
# Value: <paste the entire JSON>
```

### Step 6: Deploy

```bash
# Push to main branch
git add .
git commit -m "Deploy to Cloud Run"
git push origin main
```

GitHub Actions will automatically:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Run health check

Watch the deployment in the "Actions" tab of your GitHub repository.

### Step 7: Get Service URL

After successful deployment:

```bash
gcloud run services describe aem-assets-mcp-server \
  --region us-central1 \
  --format 'value(status.url)'
```

Or check the GitHub Actions log output.

---

## Option 2: Terraform Deployment

### Step 1: Prerequisites

Ensure gcloud is authenticated:
```bash
gcloud auth application-default login
```

### Step 2: Prepare Variables

```bash
cd terraform

# Copy example
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Example `terraform.tfvars`:
```hcl
project_id        = "my-gcp-project"
region            = "us-central1"
service_name      = "aem-assets-mcp-server"
image_tag         = "latest"
min_instances     = 0
max_instances     = 10

# AEM Configuration
aem_base_url      = "https://author-p12345-e67890.adobeaemcloud.com/api/v1"
aem_access_token  = "your_aem_access_token"
aem_org_id        = "your_org_id@AdobeOrg"
aem_client_id     = "your_aem_client_id"
```

### Step 3: Build and Push Docker Image

```bash
# Build image
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aem-mcp-images/aem-mcp-server:latest .

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push image
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aem-mcp-images/aem-mcp-server:latest
```

### Step 4: Deploy with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply infrastructure
terraform apply
```

Type `yes` when prompted.

### Step 5: View Outputs

```bash
terraform output service_url
terraform output artifact_registry_url
terraform output service_account_email
```

### Updating the Deployment

```bash
# Make code changes, rebuild image
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aem-mcp-images/aem-mcp-server:latest .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/aem-mcp-images/aem-mcp-server:latest

# Redeploy (Terraform will detect image change)
terraform apply
```

### Destroying Infrastructure

```bash
terraform destroy
```

---

## Option 3: Manual gcloud Deployment

### Step 1: Build and Push Image

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Build image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/aem-mcp-images/aem-mcp-server:latest .

# Configure Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Push image
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/aem-mcp-images/aem-mcp-server:latest
```

### Step 2: Deploy to Cloud Run

```bash
gcloud run deploy aem-assets-mcp-server \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/aem-mcp-images/aem-mcp-server:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars="AEM_BASE_URL=https://author-p12345-e67890.adobeaemcloud.com,AEM_CLIENT_ID=your_client_id" \
  --set-secrets="AEM_CLIENT_SECRET=aem-client-secret:latest,AEM_SERVICE_ACCOUNT_JSON=aem-service-account-json:latest" \
  --min-instances=0 \
  --max-instances=10 \
  --cpu=1 \
  --memory=512Mi \
  --timeout=60
```

**Note**: Both `AEM_CLIENT_SECRET` and `AEM_SERVICE_ACCOUNT_JSON` must be stored in Secret Manager and referenced as secrets (not environment variables) to keep credentials secure.

### Step 3: Get Service URL

```bash
gcloud run services describe aem-assets-mcp-server \
  --region ${REGION} \
  --format 'value(status.url)'
```

---

## 🧪 Testing Deployment

### Health Check

```bash
SERVICE_URL=$(gcloud run services describe aem-assets-mcp-server \
  --region us-central1 \
  --format 'value(status.url)')

curl $SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "aem-assets-mcp-server"
}
```

### Test Tool Call

```bash
curl -X POST $SERVICE_URL/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_folders",
    "arguments": {"path": "/"}
  }'
```

### Load Testing

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 $SERVICE_URL/health
```

---

## 📊 Monitoring & Logging

### View Logs

```bash
gcloud run services logs read aem-assets-mcp-server \
  --region us-central1 \
  --limit 50
```

Or in Cloud Console:
1. Go to Cloud Run
2. Click service name
3. Click "Logs" tab

### Set Up Monitoring

```bash
# Create alerting policy (example)
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Cloud Run High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

### View Metrics

Cloud Console → Cloud Run → Service → Metrics

Key metrics to monitor:
- Request count
- Request latency
- Error rate
- Container CPU utilization
- Container memory utilization
- Container instance count

---

## 🔐 Security Best Practices

### 1. Use Secret Manager

✅ **Already configured** in Terraform and GitHub Actions

### 2. Restrict Access

```bash
# Remove public access
gcloud run services remove-iam-policy-binding aem-assets-mcp-server \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# Add specific user
gcloud run services add-iam-policy-binding aem-assets-mcp-server \
  --region us-central1 \
  --member="user:email@example.com" \
  --role="roles/run.invoker"
```

### 3. Use VPC Connector (Advanced)

For private AEM instances:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create aem-connector \
  --region us-central1 \
  --subnet SUBNET_NAME

# Update Cloud Run to use connector
gcloud run services update aem-assets-mcp-server \
  --region us-central1 \
  --vpc-connector aem-connector
```

### 4. Enable Binary Authorization

```bash
gcloud services enable binaryauthorization.googleapis.com

# Configure policy
gcloud container binauthz policy import policy.yaml
```

---

## 💰 Cost Optimization

### Cloud Run Pricing

- **Free tier**: 2 million requests/month
- **CPU**: $0.00002400/vCPU-second
- **Memory**: $0.00000250/GiB-second
- **Requests**: $0.40 per million

### Optimization Tips

1. **Set min_instances=0** - Pay only for usage
2. **Use appropriate CPU/memory** - Start with 1 CPU, 512Mi
3. **Implement caching** - Reduce AEM API calls
4. **Set request timeout** - Prevent long-running requests
5. **Use Cloud CDN** - Cache static responses

### Estimated Monthly Costs

**Low usage** (1000 requests/day):
- ~$0-5/month

**Medium usage** (10,000 requests/day):
- ~$10-30/month

**High usage** (100,000 requests/day):
- ~$50-150/month

---

## 🔄 CI/CD Workflows

### Automatic Deployment

`.github/workflows/deploy-cloud-run.yml` triggers on:
- Push to `main` branch
- Manual workflow dispatch

### Terraform Management

`.github/workflows/terraform-apply.yml` allows:
- Plan - Preview changes
- Apply - Deploy infrastructure
- Destroy - Tear down resources

Run manually from GitHub Actions tab.

---

## 🐛 Troubleshooting

### Build Failures

**Error**: `ERROR: failed to solve: process "/bin/sh -c pip install..."`

**Solution**:
```bash
# Rebuild with no cache
docker build --no-cache -t your-image .
```

### Deployment Failures

**Error**: `ERROR: (gcloud.run.deploy) Revision 'xxx' is not ready`

**Solution**:
```bash
# Check logs
gcloud run services logs read aem-assets-mcp-server --region us-central1

# Common issues:
# - Missing secrets in Secret Manager
# - Incorrect service account permissions
# - Invalid environment variables
```

### Secret Access Errors

**Error**: `Missing required environment variable: AEM_ACCESS_TOKEN`

**Solution**:
```bash
# Verify secret exists
gcloud secrets list

# Check service account has access
gcloud secrets get-iam-policy aem-access-token

# Grant access
gcloud secrets add-iam-policy-binding aem-access-token \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Terraform State Lock

**Error**: `Error: Error locking state: Error acquiring the state lock`

**Solution**:
```bash
# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

---

## 📈 Scaling Configuration

### Auto-scaling

Cloud Run automatically scales based on:
- Number of requests
- CPU utilization
- Memory usage

Configure in Terraform:
```hcl
scaling {
  min_instance_count = 1  # Keep warm
  max_instance_count = 100
}
```

### Request Limits

```hcl
resources {
  limits = {
    cpu    = "2"      # Up to 4 CPUs
    memory = "1Gi"    # Up to 32Gi
  }
}
```

### Concurrency

```bash
gcloud run services update aem-assets-mcp-server \
  --region us-central1 \
  --concurrency 80  # Max 80 requests per instance
```

---

## 🔄 Updating the Service

### Update Code

```bash
# Make changes
git add .
git commit -m "Update: description"
git push origin main

# GitHub Actions deploys automatically
```

### Update Environment Variables

```bash
gcloud run services update aem-assets-mcp-server \
  --region us-central1 \
  --set-env-vars="NEW_VAR=value"
```

### Update Secrets

```bash
# Add new version
echo -n "new_token_value" | gcloud secrets versions add aem-access-token \
  --data-file=-

# Cloud Run uses latest version automatically
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service aem-assets-mcp-server --region us-central1

# Rollback to specific revision
gcloud run services update-traffic aem-assets-mcp-server \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

---

## 📚 Next Steps

1. ✅ Deploy to Cloud Run
2. ✅ Test all endpoints
3. ✅ Set up monitoring and alerts
4. ✅ Configure ChatGPT integration ([CHATGPT_SETUP.md](./CHATGPT_SETUP.md))
5. ✅ Implement caching if needed
6. ✅ Set up custom domain (optional)
7. ✅ Configure auth (if needed)

---

**Need help?** Check the [main README](./README.md) or [Vercel deployment guide](./DEPLOYMENT_VERCEL.md).
