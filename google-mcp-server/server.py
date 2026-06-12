import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from docs_tool import append_to_doc
from gmail_tool import create_email_draft

app = FastAPI(
    title="Google MCP Server",
    description="MCP-style server integrating Google Docs and Gmail with terminal approval checks."
)

DISABLE_APPROVAL_CHECK = os.environ.get("DISABLE_APPROVAL_CHECK", "false").lower() == "true"

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
