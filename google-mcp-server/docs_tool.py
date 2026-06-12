from googleapiclient.discovery import build
from auth import get_credentials

def append_to_doc(doc_id: str, content: str):
    """
    Appends the specified text content to the end of a Google Doc.
    
    Parameters:
        doc_id (str): The ID of the Google Doc to append content to.
        content (str): The text content to be appended.
    """
    # Retrieve OAuth credentials
    creds = get_credentials()
    
    # Build Google Docs API service
    service = build('docs', 'v1', credentials=creds)
    
    # Retrieve the document metadata to calculate the end index
    doc = service.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])
    
    # Use the endIndex of the last element minus 1 to append before the final newline
    if body_content:
        end_index = body_content[-1].get('endIndex', 2) - 1
    else:
        end_index = 1
        
    requests = [
        {
            'insertText': {
                'location': {
                    'index': end_index
                },
                'text': content
            }
        }
    ]
    
    # Execute the update request
    response = service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()
    
    return response
