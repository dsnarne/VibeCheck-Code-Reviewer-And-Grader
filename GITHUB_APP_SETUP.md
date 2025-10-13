# GitHub App Setup Guide for VibeCheck

## Quick Setup (5 minutes)

### 1. Create GitHub App
1. Go to: https://github.com/settings/apps
2. Click: "New GitHub App"
3. Fill out:
   - **App name:** `VibeCheck Analyzer`
   - **Homepage URL:** `http://localhost:3001` (or your domain)
   - **Description:** `Analyzes GitHub repositories for code quality metrics`
4. **Permissions:**
   - Contents: `Read`
   - Metadata: `Read`
   - Pull requests: `Read`
5. Click: "Create GitHub App"

### 2. Get App Credentials
After creating, copy these values:
- **App ID:** `12345` (number)
- **Private Key:** Download the `.pem` file and copy its contents
- **Installation ID:** After installing the app (see step 3)

### 3. Install App
1. In your app's settings, click "Install App"
2. Select your account
3. Choose "All repositories"
4. Click "Install"
5. Copy the **Installation ID** from the URL

### 4. Configure Environment
Create `.env` file:
```bash
# GitHub App Configuration
GITHUB_APP_ID=12345
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
YOUR_PRIVATE_KEY_CONTENT_HERE
-----END RSA PRIVATE KEY-----"
GITHUB_APP_INSTALLATION_ID=67890
```

### 5. Install Dependencies
```bash
source venv/bin/activate
pip install PyJWT[crypto]
```

### 6. Test Setup
```bash
# Restart server
uvicorn Backend.app.main:app --host 0.0.0.0 --port 3001 --reload

# Check status
curl http://localhost:3001/api/rate-limit-status

# Test analysis
curl -X POST http://localhost:3001/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/dsnarne/Tank-Battle-","window_days":365,"max_commits":50}'
```

## Benefits of GitHub App

✅ **15,000 requests/hour** (vs 5,000 for personal tokens)  
✅ **No user setup required** - users just paste GitHub links  
✅ **Professional appearance** - your app handles authentication  
✅ **Independent of personal accounts** - won't break if you leave  
✅ **Granular permissions** - only access what's needed  

## Troubleshooting

**"GitHub App credentials not configured"**
- Check your `.env` file has all three values
- Make sure private key includes the full PEM format

**"Installation not found"**
- Verify the Installation ID is correct
- Make sure you installed the app on your account

**Rate limit errors**
- GitHub App should give you 15,000/hour
- Check the rate limit status endpoint

## Production Deployment

For production, set these environment variables:
```bash
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY="your_private_key"
GITHUB_APP_INSTALLATION_ID=your_installation_id
```

No other changes needed - your app will automatically use the GitHub App for all requests!
