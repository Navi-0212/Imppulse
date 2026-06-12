import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

app = FastAPI(
    title="Google MCP Server",
    description="MCP-style server integrating Google Docs and Gmail with terminal approval checks."
)

DISABLE_APPROVAL_CHECK = os.environ.get("DISABLE_APPROVAL_CHECK", "false").lower() == "true"

@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Google MCP Server Status</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-color: #0b0f19;
                --card-bg: rgba(255, 255, 255, 0.03);
                --border-color: rgba(255, 255, 255, 0.08);
                --text-color: #f3f4f6;
                --text-muted: #9ca3af;
                --primary: #4f46e5;
                --primary-glow: rgba(79, 70, 229, 0.4);
                --success: #10b981;
                --success-glow: rgba(16, 185, 129, 0.3);
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                position: relative;
            }
            
            .glow {
                position: absolute;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, var(--primary-glow) 0%, rgba(0,0,0,0) 70%);
                top: 10%;
                left: 10%;
                z-index: 1;
                filter: blur(80px);
            }
            .glow-secondary {
                position: absolute;
                width: 300px;
                height: 300px;
                background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, rgba(0,0,0,0) 70%);
                bottom: 10%;
                right: 10%;
                z-index: 1;
                filter: blur(80px);
            }
            
            .container {
                position: relative;
                z-index: 2;
                width: 90%;
                max-width: 650px;
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-color);
                border-radius: 24px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                animation: fadeIn 0.8s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 30px;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 20px;
            }
            
            .title h1 {
                font-size: 28px;
                font-weight: 700;
                background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .title p {
                color: var(--text-muted);
                font-size: 14px;
                margin-top: 4px;
            }
            
            .status-badge {
                display: flex;
                align-items: center;
                gap: 8px;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.2);
                color: var(--success);
                padding: 8px 16px;
                border-radius: 100px;
                font-weight: 600;
                font-size: 14px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                background-color: var(--success);
                border-radius: 50%;
                box-shadow: 0 0 12px var(--success);
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }
            
            .endpoint-section {
                margin-bottom: 20px;
            }
            
            .endpoint-section h2 {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 16px;
                color: #e5e7eb;
            }
            
            .endpoint-card {
                background: rgba(255,255,255,0.015);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 16px;
                transition: all 0.3s ease;
            }
            
            .endpoint-card:hover {
                border-color: rgba(79, 70, 229, 0.4);
                transform: translateY(-2px);
                background: rgba(79, 70, 229, 0.02);
            }
            
            .endpoint-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 12px;
            }
            
            .method {
                font-size: 12px;
                font-weight: 700;
                padding: 4px 8px;
                border-radius: 6px;
                text-transform: uppercase;
            }
            
            .method.post {
                background: rgba(79, 70, 229, 0.15);
                border: 1px solid rgba(79, 70, 229, 0.3);
                color: #a5b4fc;
            }
            
            .path {
                font-family: monospace;
                font-weight: 600;
                color: #f3f4f6;
                font-size: 15px;
            }
            
            .desc {
                font-size: 14px;
                color: var(--text-muted);
                line-height: 1.5;
            }
            
            .footer {
                text-align: center;
                margin-top: 30px;
                font-size: 12px;
                color: var(--text-muted);
                border-top: 1px solid var(--border-color);
                padding-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="glow"></div>
        <div class="glow-secondary"></div>
        <div class="container">
            <div class="header">
                <div class="title">
                    <h1>Google MCP Server</h1>
                    <p>FastAPI Model Context Protocol Gateway</p>
                </div>
                <div class="status-badge">
                    <div class="status-dot"></div>
                    Online
                </div>
            </div>
            
            <div class="endpoint-section">
                <h2>Available API Endpoints</h2>
                
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <span class="method post">POST</span>
                        <span class="path">/append_to_doc</span>
                    </div>
                    <div class="desc">Appends text content to the end of a specified Google Doc. Requires doc_id and content in the body.</div>
                </div>
                
                <div class="endpoint-card">
                    <div class="endpoint-header">
                        <span class="method post">POST</span>
                        <span class="path">/create_email_draft</span>
                    </div>
                    <div class="desc">Creates an email draft in Gmail with recipient, subject, and body content.</div>
                </div>
            </div>
            
            <div class="footer">
                Powered by FastAPI &bull; Google Workspace API Integration
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


class AppendToDocRequest(BaseModel):
    doc_id: str
    content: str

class CreateEmailDraftRequest(BaseModel):
    to: str
    subject: str
    body: str

def ask_user_approval(action_name: str, payload: dict) -> bool:
    """
    Prints the action and payload to the terminal and waits for user approval.
    """
    print(f"\n[REQUESTED ACTION]: {action_name}")
    print(f"Payload:\n{json.dumps(payload, indent=4)}")
    
    if DISABLE_APPROVAL_CHECK:
        print("Approval check bypassed (DISABLE_APPROVAL_CHECK=true)")
        return True
        
    # Prompt the user exactly as specified
    response = input("Approve? (y/n) ").strip()
    return response.lower() == 'y'

# Defining endpoints as standard def (not async def) ensures FastAPI runs
# them in a separate threadpool, allowing the blocking input() to work safely.
@app.post("/append_to_doc")
def endpoint_append_to_doc(req: AppendToDocRequest):
    payload = {
        "doc_id": req.doc_id,
        "content": req.content
    }
    
    if not ask_user_approval("append_to_doc", payload):
        raise HTTPException(status_code=403, detail="Action rejected by user")
        
    try:
        res = append_to_doc(req.doc_id, req.content)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_email_draft")
def endpoint_create_email_draft(req: CreateEmailDraftRequest):
    payload = {
        "to": req.to,
        "subject": req.subject,
        "body": req.body
    }
    
    if not ask_user_approval("create_email_draft", payload):
        raise HTTPException(status_code=403, detail="Action rejected by user")
        
    try:
        res = create_email_draft(req.to, req.subject, req.body)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the uvicorn server on localhost
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
