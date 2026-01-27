# How to Get Your AEM OAuth Server-to-Server Credentials

This guide shows you how to obtain the OAuth Server-to-Server credentials needed for the AEM Assets MCP Server.

## 📋 What You Need

You need to get these values from Adobe Developer Console:

1. **AEM_BASE_URL** - Your AEM Author instance URL
2. **AEM_CLIENT_ID** - OAuth Client ID (also used as X-Api-Key)
3. **AEM_CLIENT_SECRET** - OAuth Client Secret (keep secret!)
4. **AEM_SCOPES** - OAuth scopes for API access

## 🔑 Step-by-Step Guide

### Step 1: Access Adobe Developer Console

1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
2. Sign in with your Adobe ID
3. Select your organization (if you have multiple)

### Step 2: Create or Open a Project

**Option A: Create New Project**
```
1. Click "Create new project"
2. Click "Add API"
3. Select "Experience Cloud" category
4. Select "AEM Assets Author API"
5. Click "Next"
```

**Option B: Use Existing Project**
```
1. Select your existing project
2. If AEM Assets Author API isn't added yet, click "Add API"
```

### Step 3: Configure OAuth Server-to-Server

1. In the "Configure API" dialog, select **"OAuth Server-to-Server"** authentication
2. Click "Next"
3. Name your credential (e.g., "AEM MCP Server")
4. Click "Save configured API"

### Step 4: Get Your Credentials

After configuration, you'll see the "OAuth Server-to-Server credential" page:

#### 📋 Copy These Values:

1. **Client ID**
   ```
   Location: Credential details → Client credentials → Client ID
   Format: (example) a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   Used as: AEM_CLIENT_ID (and X-Api-Key header)
   ```

2. **Client Secret**
   ```
   Location: Credential details → Client credentials → Client secret
   Action: Click "Retrieve client secret" to reveal
   Format: Long alphanumeric string
   Used as: AEM_CLIENT_SECRET
   IMPORTANT: Keep this secret! Never commit to Git!
   ```

3. **Scopes**
   ```
   Location: Scroll down to "Scopes" section
   Format: Comma-separated list
   Example: openid,AdobeID,read_organizations,additional_info.projectedProductContext,additional_info.roles
   Used as: AEM_SCOPES
   ```

#### 🌐 Your AEM Base URL:

Your AEM Author URL is: `https://author-p12345-e67890.adobeaemcloud.com`

(Remove any `/api` or `/adobe/assets` suffixes)

### Step 5: Assign Product Profile

1. In the same OAuth credential page, scroll to "Product Profiles"
2. Click "Add Product Profiles" (if not already assigned)
3. Select appropriate profile:
   - For READ operations: **"AEM Assets Collaborator Users - author - Program XXX - Environment XXX"**
   - For WRITE operations: **"AEM Administrators - author - Program XXX - Environment XXX"**
4. Click "Save"

### Step 6: Fill in Your .env File

Create a `.env` file in your project root:

```bash
# Copy the example
cp env.example .env

# Edit with your values
nano .env
```

Fill in your credentials:

```env
# Your AEM instance
AEM_BASE_URL=https://author-p12345-e67890.adobeaemcloud.com

# Your OAuth credentials from Adobe Developer Console
AEM_CLIENT_ID=your_client_id_here
AEM_CLIENT_SECRET=your_client_secret_here
AEM_SCOPES=openid,AdobeID,read_organizations,additional_info.projectedProductContext,additional_info.roles

# Adobe IMS endpoint (no need to change)
ADOBE_IMS_TOKEN_ENDPOINT=https://ims-na1.adobelogin.com/ims/token/v3
```

## ✅ Verify Your Setup

### Test Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
uvicorn app.main:app --reload

# In another terminal, test
curl http://localhost:8000/health
```

If successful, you should see:
```json
{
  "status": "healthy",
  "service": "aem-assets-mcp-server"
}
```

### Test Token Generation

The server will automatically fetch an access token on the first API call. Check the logs:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:app.aem_client:Fetching new access token from Adobe IMS
INFO:app.aem_client:Access token obtained, expires in 3600 seconds
INFO:     Application startup complete.
```

## 🔄 Token Management

### Automatic Refresh

The MCP server automatically:
- ✅ Fetches a token on first API call
- ✅ Stores the token and expiration time
- ✅ Checks token validity before each request
- ✅ Refreshes the token 5 minutes before expiration
- ✅ Handles token refresh transparently

You don't need to:
- ❌ Manually generate tokens
- ❌ Update tokens in .env file
- ❌ Worry about token expiration

### Token Lifetime

- **Default lifetime**: 1 hour (3600 seconds)
- **Refresh trigger**: 55 minutes (5 minutes before expiration)
- **Automatic**: No manual intervention needed

## 🐛 Troubleshooting

### Error: "Missing required environment variable"

**Problem**: .env file not configured

**Solution**:
```bash
# Make sure .env exists
ls -la .env

# Copy from example if needed
cp env.example .env
nano .env
```

### Error: "Failed to authenticate with Adobe IMS"

**Problem**: Invalid credentials

**Solution**:
1. Double-check CLIENT_SECRET is correct (it's long!)
2. Verify CLIENT_ID matches Adobe Developer Console
3. Ensure SCOPES are comma-separated, no spaces
4. Check if credentials are still active in Adobe Console

### Error: "401 Unauthorized" when calling API

**Problem**: Product Profile not assigned or insufficient permissions

**Solution**:
1. Go to Adobe Developer Console → Your Project → OAuth credential
2. Check "Product Profiles" section
3. Ensure correct profile is assigned
4. For write operations, use "AEM Administrators" profile

### Error: "403 Forbidden" for PATCH/DELETE requests

**Problem**: Insufficient permissions (READ-only profile)

**Solution**:
1. Update Product Profile to include write permissions
2. Or assign "AEM Administrators" profile
3. Redeploy and test again

## 📚 References

- [Adobe IMS OAuth Server-to-Server](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/)
- [AEM Assets Author API](https://developer.adobe.com/experience-cloud/experience-manager-apis/api/stable/assets/author/)
- [Invoke OpenAPI-based AEM APIs](https://experienceleague.adobe.com/en/docs/experience-manager-learn/cloud-service/aem-apis/openapis/invoke-api-using-oauth-s2s)

## 🔒 Security Best Practices

1. **Never commit .env file**
   ```bash
   # .gitignore already includes .env
   # Verify it's ignored:
   git status  # Should NOT show .env
   ```

2. **Use different credentials for different environments**
   ```
   .env.dev  - Development
   .env.prod - Production
   ```

3. **Rotate Client Secret regularly**
   - Adobe recommends rotating every 90 days
   - Generate new secret in Adobe Console
   - Update .env file
   - Redeploy

4. **Use Secret Manager in production**
   - Vercel: Use Environment Variables
   - Cloud Run: Use Google Secret Manager
   - Never hardcode in source code

---

**Need help?** Check the [main README](./README.md) or open an issue!
