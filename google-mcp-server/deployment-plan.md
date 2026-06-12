# Deployment Plan: Google MCP Server on Railway

This document details the steps required to deploy your Google MCP FastAPI server on Railway.

---

## 🔒 1. Secrets Management

Do **not** commit `credentials.json` or `token.json` to GitHub. The server is configured to load them from environment variables if the physical files do not exist.

You will configure these as Environment Variables in your Railway Dashboard:

| Key | Value | Description |
| :--- | :--- | :--- |
| `GOOGLE_CREDENTIALS_JSON` | `<content of credentials.json>` | The raw JSON contents of your OAuth Client ID file. |
| `GOOGLE_TOKEN_JSON` | `<content of token.json>` | The authorized user credentials containing access and refresh tokens. |
| `DISABLE_APPROVAL_CHECK` | `true` | **Crucial:** Prevents the server from pausing requests for terminal inputs (`Approve? (y/n)`) in a headless environment. |

---

## 🚀 2. Preparation (Local Machine)

Before deploying to Railway, you must generate `token.json` locally using your developer credential (since Google OAuth requires a local browser window to grant permission).

1. Ensure `credentials.json` is in `google-mcp-server/`.
2. Run the token generator locally:
   ```bash
   python get_token.py
   ```
3. Complete the login flow in your web browser. This generates `token.json` in your local directory.
4. Keep the contents of `credentials.json` and `token.json` handy to copy into Railway.

---

## 📂 3. Railway Setup Steps

### Step 1: Create a Git Repository
If you haven't already, initialize a Git repository and commit the server code.
Add a `.gitignore` to prevent sensitive credentials from being uploaded:
```text
# .gitignore
credentials.json
token.json
__pycache__/
*.pyc
.venv/
```

### Step 2: Create a New Project on Railway
1. Go to [Railway.app](https://railway.app) and sign in.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select the repository containing your `google-mcp-server` directory.

### Step 3: Configure Environment Variables
In your Railway Service Dashboard, navigate to the **Variables** tab and add:
- `GOOGLE_CREDENTIALS_JSON`: *(Paste the entire contents of credentials.json)*
- `GOOGLE_TOKEN_JSON`: *(Paste the entire contents of token.json)*
- `DISABLE_APPROVAL_CHECK`: `true`

### Step 4: Configure Start Command
In the **Settings** tab of your service on Railway:
1. Locate the **Deploy** section.
2. Set the **Start Command** to:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
   *Note: Railway assigns a dynamic port variable `$PORT` automatically.*

---

## 🧪 4. Testing the Deployment

Once deployed, Railway will generate a public domain URL (e.g., `https://your-mcp-server.up.railway.app`).

You can verify it works by sending a test payload using Curl:

### Test Docs Append:
```bash
curl -X POST "https://your-mcp-server.up.railway.app/append_to_doc" \
     -H "Content-Type: application/json" \
     -d '{
       "doc_id": "YOUR_GOOGLE_DOC_ID",
       "content": "Hello from Railway!\n"
     }'
```

### Test Gmail Draft:
```bash
curl -X POST "https://your-mcp-server.up.railway.app/create_email_draft" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "your-email@example.com",
       "subject": "Hello from Railway Deployment",
       "body": "This draft was successfully created from the Railway deployed MCP server."
     }'
```
