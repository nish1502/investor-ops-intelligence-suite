import os.path
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

def run_auth():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(base_dir, 'production', 'credentials.json')
    token_path = os.path.join(base_dir, 'production', 'token.json')
    
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    # This will start a local server on port 8080 and wait
    # Since we are in a headless environment, we tell it not to open the browser
    creds = flow.run_local_server(port=8080, open_browser=False)
    
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    print("✅ token.json updated successfully!")

if __name__ == "__main__":
    run_auth()
