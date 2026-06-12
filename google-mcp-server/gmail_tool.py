import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from auth import get_credentials

def create_email_draft(to: str, subject: str, body: str):
    """
    Creates a draft email in Gmail.
    
    Parameters:
        to (str): The email recipient.
        subject (str): The subject of the email.
        body (str): The plain-text body of the email.
    """
    # Retrieve OAuth credentials
    creds = get_credentials()
    
    # Build Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    
    # Build RFC 2822 email message
    message = EmailMessage()
    message['To'] = to
    message['Subject'] = subject
    message.set_content(body)
    
    # Gmail API requires draft messages to be base64url encoded
    raw_bytes = message.as_bytes()
    encoded_message = base64.urlsafe_b64encode(raw_bytes).decode('utf-8')
    
    draft_payload = {
        'message': {
            'raw': encoded_message
        }
    }
    
    # Create the draft in user's drafts
    response = service.users().drafts().create(
        userId='me',
        body=draft_payload
    ).execute()
    
    return response
