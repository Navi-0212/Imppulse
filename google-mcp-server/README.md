# Google MCP Server (Docs & Gmail Integration)

A complete MCP-style FastAPI server written in Python that integrates with Google Docs and Gmail.

## 📁 Project Structure

```text
google-mcp-server/
├── server.py          → FastAPI app with tool endpoints
├── auth.py            → Google OAuth authentication
├── docs_tool.py       → Google Docs tool (append content)
├── gmail_tool.py      → Gmail tool (create draft)
├── requirements.txt   → All dependencies
├── README.md          → Setup and usage instructions
├── credentials.json   → (NOT committed — downloaded from Google Cloud)
└── token.json         → (NOT committed — auto-generated after OAuth)
```

## ⚙️ Features

1. **Google Docs Tool (`/append_to_doc`)**: Appends text to the end of a specified Google Doc.
2. **Gmail Tool (`/create_email_draft`)**: Creates an email draft with recipient, subject, and body.
3. **Interactive Terminal Approval**: Before executing any action, the server outputs the details of the action and its payload to the terminal and requires manual approval (`y/n`).
4. **OAuth 2.0 Token Caching**: Authenticates using OAuth 2.0 with scopes for Google Docs and Gmail. It saves session details to `token.json` so you only have to log in via the browser once.

---

## 🚀 Setup & Execution

### 1. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Configure Google Cloud Credentials

Ensure that `credentials.json` is located in the `google-mcp-server/` directory. (An OAuth client secret credential has already been placed in the folder).

### 3. Run the Server

Start the FastAPI server:

```bash
python server.py
```

The server will start at `http://127.0.0.1:8000`.

---

## 🛠️ API Reference

### 1. Append to Document

Appends text to a Google Doc.

* **Endpoint**: `POST /append_to_doc`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "doc_id": "YOUR_DOCUMENT_ID",
    "content": "Hello World! This is appended text.\n"
  }
  ```

### 2. Create Email Draft

Creates an email draft in Gmail.

* **Endpoint**: `POST /create_email_draft`
* **Content-Type**: `application/json`
* **Request Body**:
  ```json
  {
    "to": "recipient@example.com",
    "subject": "Hello from Google MCP Server",
    "body": "This is the body of the draft email."
  }
  ```

---

## 🔒 Security & Approval Flow

When you call any endpoint:
1. The server halts the request.
2. It displays the action name and request payload in the terminal where `server.py` is running:
   ```text
   [REQUESTED ACTION]: create_email_draft
   Payload:
   {
       "to": "recipient@example.com",
       "subject": "Hello from Google MCP Server",
       "body": "This is the body of the draft email."
   }
   Approve? (y/n)
   ```
3. Type `y` and press Enter to approve and execute, or `n` to reject (returns a `403 Forbidden` response to the API caller).
