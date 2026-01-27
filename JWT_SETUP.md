# JWT Service Account Setup for Classic API

The AEM Classic HTTP API (`/api/assets`) requires **JWT Service Account authentication**, which is different from the OAuth Server-to-Server auth used by the newer OpenAPI endpoints.

## 📚 References

- [Generating Access Tokens for Server-Side APIs](https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/implementing/developing/generating-access-tokens-for-server-side-apis)
- [AEMCS API Client Library](https://github.com/adobe/aemcs-api-client-lib)

## 🔑 Two Authentication Systems

| API | Endpoint | Auth Method | Setup Location |
|-----|----------|-------------|----------------|
| **Classic HTTP API** | `/api/assets` | JWT Service Account | Developer Console → Technical Account |
| **New OpenAPI** | `/adobe/assets`, `/adobe/folders` | OAuth S2S | Developer Console → OAuth Server-to-Server |

## 📋 Setup Steps

### 1. Create Technical Account in Adobe Developer Console

1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
2. Select your project (or create one)
3. Go to **Integrations** tab
4. Click **Create new technical account**
5. Download the JSON file (contains certificate + private key)

### 2. Add the JSON File to Your Project

Save the downloaded JSON file:

```bash
# Save it to your project root
mv ~/Downloads/service-account-xxxxx.json ./service-account.json
```

### 3. Update Your `.env` File

Add the path to your `.env`:

```bash
# ========================================
# JWT Service Account (for /api/* classic endpoints)
# ========================================
AEM_SERVICE_ACCOUNT_JSON=./service-account.json
```

### 4. Install JWT Dependencies

```bash
pip install PyJWT==2.8.0 cryptography==42.0.5
```

Or just:

```bash
pip install -r requirements.txt
```

### 5. Set Permissions for the Technical Account

In AEM, the technical account needs proper permissions:

1. Go to Adobe Admin Console
2. Navigate to **Products** → **AEM as a Cloud Service**
3. Create a **New Profile** (e.g., "AEM Assets API Access")
4. Add your technical account email (e.g., `xxxxx@techacct.adobe.com`)
5. In AEM Author:
   - Go to **Tools** → **Security** → **Permissions**
   - Find the group matching your product profile
   - Grant read permissions to `/content/dam`

## 📝 Service Account JSON Structure

The JSON file contains:

```json
{
  "ok": true,
  "integration": {
    "imsEndpoint": "ims-na1.adobelogin.com",
    "metascopes": "ent_aem_cloud_api",
    "technicalAccount": {
      "clientId": "xxxxx",
      "clientSecret": "xxxxx",
      "id": "xxxxx@techacct.adobe.com",
      "org": "xxxxx@AdobeOrg"
    },
    "email": "xxxxx",
    "cert": "-----BEGIN CERTIFICATE-----\n...",
    "privateKey": "-----BEGIN PRIVATE KEY-----\n..."
  }
}
```

## 🧪 Test the Setup

### Test Locally:

```bash
# Start server
source venv/bin/activate
uvicorn app.main:app --reload

# Test classic API (should work now!)
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_assets_by_folder",
    "arguments": {"folderPath": "/content/dam/H2OR/Hk/canada-goose"}
  }' | jq '.'
```

### Check the Logs:

You should see:

```
✅ JWT Service Account auth available (for /api/assets)
✅ OAuth Server-to-Server auth available (for /adobe/* endpoints)
```

## 🔄 How It Works

### Authentication Flow:

1. **Load Service Account JSON** → Read certificate + private key
2. **Generate JWT Token** → Sign with private key
3. **Exchange JWT for Access Token** → Call Adobe IMS
4. **Use Access Token** → Make `/api/assets` requests

### Code Flow:

```python
# app/jwt_auth.py handles JWT creation and token exchange
jwt_token = create_signed_jwt(private_key, technical_account_id)
access_token = exchange_jwt_for_token(jwt_token)

# app/aem_client.py uses the token for classic API
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{base_url}/api/assets/path.json", headers=headers)
```

## 🔐 Security Best Practices

1. **Never commit** the service account JSON file
   - Added to `.gitignore` automatically
   - Contains private key - treat as secret

2. **Rotate certificates** before expiration (1 year)
   - Download new JSON from Developer Console
   - Update `AEM_SERVICE_ACCOUNT_JSON` path

3. **Use minimal permissions**
   - Grant only necessary read/write access
   - Use separate technical accounts for different APIs

## 🐛 Troubleshooting

### "JWT Service Account authentication not configured"

- Check `AEM_SERVICE_ACCOUNT_JSON` path in `.env`
- Verify the JSON file exists and is readable
- Check file format (should be valid JSON with `integration` key)

### "Failed to exchange JWT for access token"

- Verify technical account is active in Developer Console
- Check certificate hasn't expired (valid for 1 year)
- Ensure `clientId` and `clientSecret` are correct

### "403 Forbidden" from `/api/assets`

- Technical account needs permissions in AEM
- Add to product profile in Admin Console
- Grant read permissions in AEM (Tools → Security → Permissions)

### "JWT token generation failed"

- Check private key format in JSON
- Ensure PyJWT and cryptography libraries are installed
- Verify private key is not corrupted

## 📊 Comparison with OAuth

| Feature | JWT Service Account | OAuth Server-to-Server |
|---------|-------------------|----------------------|
| Setup | Technical Account JSON | Client ID + Secret |
| Token Type | JWT → Access Token | Direct Access Token |
| Complexity | Higher (JWT signing) | Lower (simple POST) |
| Use Case | Classic API | New OpenAPI |
| Expiration | 24 hours | Configurable |

## ✅ Complete Setup Checklist

- [ ] Downloaded service account JSON from Developer Console
- [ ] Saved JSON file to project directory
- [ ] Added `AEM_SERVICE_ACCOUNT_JSON` to `.env`
- [ ] Installed JWT dependencies (`pip install -r requirements.txt`)
- [ ] Created product profile in Admin Console
- [ ] Added technical account to product profile
- [ ] Granted permissions in AEM
- [ ] Tested `/list_assets_by_folder` endpoint
- [ ] Verified logs show JWT auth available

## 🚀 Next Steps

After setup, your MCP server will automatically:
- Use **JWT auth** for `/api/assets` (classic API)
- Use **OAuth S2S** for `/adobe/*` (modern API)
- Fall back gracefully if JWT auth is not configured

The `list_assets_by_folder` tool will now work properly with full access to AEM assets! 🎉
