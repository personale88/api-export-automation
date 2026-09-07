import os
import sys
import smtplib
import ssl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from config import config
except ImportError:
    import config

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    HAS_GOOGLE_OAUTH = True
except ImportError:
    HAS_GOOGLE_OAUTH = False

# Permission scopes for optional OAuth2
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

def is_smtp_configured():
    """Checks if Gmail SMTP App Password credentials are configured."""
    email = config.get("GMAIL_EMAIL")
    password = config.get("GMAIL_APP_PASSWORD")
    return bool(email and password and len(str(password).strip()) >= 12)

def is_oauth_configured():
    """Helper to check if real OAuth can be initiated."""
    return os.path.exists(TOKEN_PATH) or os.path.exists(CREDENTIALS_PATH)

def get_auth_mode():
    """Determines the active authentication mode: 'smtp', 'oauth2', or 'simulation'."""
    if is_smtp_configured():
        return "smtp"
    elif is_oauth_configured():
        return "oauth2"
    return "simulation"

def test_smtp_connection(email=None, password=None):
    """
    Tests SMTP connection and authentication to smtp.gmail.com.
    Returns (True, message) or (False, error_message).
    """
    email = email or config.get("GMAIL_EMAIL")
    password = (password or config.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    
    if not email or not password:
        return False, "Missing Gmail address or App Password."
        
    smtp_host = config.get("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(config.get("SMTP_PORT") or 465)
    
    context = ssl.create_default_context()
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
                server.login(email, password)
                return True, f"Successfully authenticated to {smtp_host}:{smtp_port} (SSL) as {email}."
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls(context=context)
                server.login(email, password)
                return True, f"Successfully authenticated to {smtp_host}:{smtp_port} (STARTTLS) as {email}."
    except smtplib.SMTPAuthenticationError as e:
        err_detail = ""
        if hasattr(e, 'smtp_error'):
            raw_err = getattr(e, 'smtp_error')
            if isinstance(raw_err, bytes):
                err_detail = raw_err.decode('utf-8', errors='replace')
            else:
                err_detail = str(raw_err)
        else:
            err_detail = str(e)
        return False, f"Authentication failed. Please verify your Gmail address and 16-character App Password. ({err_detail})"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_smtp_connection():
    """
    Establishes and returns an authenticated SMTP connection.
    Returns (server, None) on success, or (None, error_msg) on failure.
    """
    email = config.get("GMAIL_EMAIL")
    password = (config.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    smtp_host = config.get("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(config.get("SMTP_PORT") or 465)
    
    context = ssl.create_default_context()
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=20)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
            server.starttls(context=context)
        server.login(email, password)
        return server, None
    except Exception as e:
        return None, str(e)

def get_gmail_service():
    """
    Authenticates the user and returns the Gmail API service instance (OAuth2).
    Returns None if credentials.json is missing.
    """
    if not HAS_GOOGLE_OAUTH:
        return None

    creds = None
    
    # 1. Load saved token if it exists
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"[Gmail Auth] Error loading token.json: {e}")
            creds = None

    # 2. If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[Gmail Auth] Access token expired. Refreshing token...")
                creds.refresh(Request())
            except Exception as e:
                print(f"[Gmail Auth] Token refresh failed: {e}. Initiating new sign-in...")
                creds = None
                
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                return None
                
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0, open_browser=True)
                with open(TOKEN_PATH, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                print(f"[Gmail Auth] OAuth2 flow failed: {e}")
                return None

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"[Gmail Auth] Error building Gmail service: {e}")
        return None
