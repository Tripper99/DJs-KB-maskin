# -*- coding: utf-8 -*-
"""
Gmail authentication handling
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.exceptions import RefreshError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class AuthenticationError(Exception):
    pass

class GmailAuthenticator:
    def __init__(self, credentials_file: str, gmail_account: str):
        self.credentials_file = Path(credentials_file) if credentials_file else None
        self.gmail_account = gmail_account
        self.token_file = self._generate_token_file_path()
        self.service = None
    
    def _generate_token_file_path(self) -> Optional[Path]:
        if not self.gmail_account:
            return None
        safe_email = re.sub(r'[^\w\-_.]', '_', self.gmail_account)
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / f'token_{safe_email}.json'
    
    def validate_credentials_file(self) -> bool:
        if not self.credentials_file or not self.credentials_file.exists():
            return False
        try:
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
                return 'installed' in data or 'web' in data
        except (json.JSONDecodeError, Exception):
            return False
    
    def authenticate(self, progress_callback=None, gui_update_callback=None) -> None:
        if not self.credentials_file or not self.gmail_account:
            raise AuthenticationError("Både credentials-fil och Gmail-konto måste anges")
        if not self.validate_credentials_file():
            raise AuthenticationError(f"Ogiltig credentials-fil: {self.credentials_file}")
        
        try:
            if progress_callback:
                progress_callback(f"Autentiserar Gmail för {self.gmail_account}...", 20)
            if gui_update_callback:
                gui_update_callback()
            
            creds = None
            if self.token_file and self.token_file.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError:
                        creds = None
                
                if not creds:
                    if progress_callback:
                        progress_callback("Öppnar webbläsare för autentisering...", 50)
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), SCOPES)
                    creds = flow.run_local_server(port=0)
            
            if self.token_file:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            if progress_callback:
                progress_callback("Gmail-autentisering slutförd!", 100)
            
            self.service = build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            raise AuthenticationError(f"Autentiseringsfel: {str(e)}")
    
    def get_service(self):
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")
        return self.service