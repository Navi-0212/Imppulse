import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scopes required by the application
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Use absolute paths relative to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')

def get_credentials():
    """
    Retrieves credentials from the environment.
    Loads existing credentials from token.json if available.
    Otherwise, runs local server auth using credentials.json and generates token.json.
    """
    # Check environment variables to support cloud deployments (e.g. Railway)
    if not os.path.exists(CREDENTIALS_PATH) and 'GOOGLE_CREDENTIALS_JSON' in os.environ:
        with open(CREDENTIALS_PATH, 'w') as f:
            f.write(os.environ['GOOGLE_CREDENTIALS_JSON'])
            
    if not os.path.exists(TOKEN_PATH) and 'GOOGLE_TOKEN_JSON' in os.environ:
        with open(TOKEN_PATH, 'w') as f:
            f.write(os.environ['GOOGLE_TOKEN_JSON'])

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}.\n"
                    "Please download your Google OAuth client secrets file and place it in the server directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            
    return creds
