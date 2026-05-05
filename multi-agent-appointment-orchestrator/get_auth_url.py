import os.path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

def get_url():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(base_dir, 'production', 'credentials.json')
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES, redirect_uri='http://localhost:8080/')
    auth_url, _ = flow.authorization_url(prompt='consent')
    print(f"AUTH_URL: {auth_url}")

if __name__ == "__main__":
    get_url()
