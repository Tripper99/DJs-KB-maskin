# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
DJs app för hantering av filer från "Svenska Tidningar".
dan@josefsson.net
Kod skriven med hjälp av Claud ai, Grok och Cursor.
"""

import os
import base64
import datetime
import json
import time
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
import re
from collections import defaultdict
import sys
import subprocess

# GUI imports
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
except ImportError:
    print("Error: ttkbootstrap not installed. Install with: pip install ttkbootstrap")
    exit(1)

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import RefreshError
    GMAIL_AVAILABLE = True
except ImportError:
    print("Warning: Google API libraries not installed. Gmail functionality will be disabled.")
    print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    GMAIL_AVAILABLE = False

# Image processing imports
try:
    from PIL import Image, ImageTk
    import pandas as pd
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    print("Warning: PIL or pandas not installed. KB processing functionality will be disabled.")
    print("Install with: pip install Pillow pandas openpyxl")
    IMAGE_PROCESSING_AVAILABLE = False

# Constants
VERSION = "1.1"  # Updated version
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CONFIG_FILE = "combined_app_config.json"

# Global variables
cancel_requested = False

# ============================
# LOGGING SETUP
# ============================
def setup_logging():
    """Setup logging to file in the same directory as the script"""
    script_dir = Path(__file__).parent
    log_filename = script_dir / f"combined_app_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return str(log_filename)

logger = logging.getLogger(__name__)

# ============================
# CONFIGURATION MANAGEMENT
# ============================
def load_config():
    """Load application configuration"""
    default_config = {
        "gmail_enabled": False,
        "kb_enabled": False,
        "gmail_account": "",
        "credentials_file": "",
        "sender_email": "noreply@kb.se",
        "start_date": "",
        "end_date": "",
        "gmail_output_dir": str(Path.home() / "Downloads" / "Gmail-nedladdningar"),
        "excel_path": "",
        "kb_output_dir": "",
        "keep_renamed": False
    }
    
    if Path(CONFIG_FILE).exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (json.JSONDecodeError, IOError):
            return default_config
    return default_config

def save_config(config):
    """Save application configuration"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        logger.error(f"Could not save configuration: {e}")

# ============================
# GMAIL CLASSES
# ============================
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
        script_dir = Path(__file__).parent
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

class GmailSearcher:
    def __init__(self, gmail_service):
        self.service = gmail_service
    
    def build_search_query(self, sender_email: str, start_date: str, end_date: str, has_attachment: bool = True) -> str:
        query_parts = []
        if sender_email:
            query_parts.append(f"from:{sender_email}")
        if start_date:
            query_parts.append(f"after:{start_date}")
            logger.info(f"📅 Start date: Including from {start_date} using after:{start_date}")
        
        # Only add end date if it's different from start date
        if end_date and end_date != start_date:
            try:
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                next_day = end_dt + datetime.timedelta(days=1)
                next_day_str = next_day.strftime("%Y-%m-%d")
                query_parts.append(f"before:{next_day_str}")
                logger.info(f"📅 End date: Including {end_date} by using before:{next_day_str}")
            except ValueError as e:
                logger.error(f"Invalid end date format: {end_date}")
                raise ValueError(f"Invalid end date format: {end_date}")
        elif start_date and not end_date:
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                next_day = start_dt + datetime.timedelta(days=1)
                next_day_str = next_day.strftime("%Y-%m-%d")
                query_parts.append(f"before:{next_day_str}")
                logger.info(f"📅 Single day: Searching {start_date} using before:{next_day_str}")
            except ValueError as e:
                logger.error(f"Invalid date format: {start_date}")
                raise ValueError(f"Invalid date format: {start_date}")
        
        if has_attachment:
            query_parts.append("has:attachment")
        query = " ".join(query_parts)
        logger.info(f"🔍 Built search query: '{query}'")
        return query
    
    def search_emails(self, query: str, progress_callback=None, gui_update_callback=None, cancel_check=None) -> List[str]:
        try:
            if progress_callback:
                progress_callback("Söker efter emails...", 0)
            if gui_update_callback:
                gui_update_callback()
            logger.info(f"🔍 Starting email search with query: '{query}'")
            
            all_messages = []
            page_token = None
            page_count = 0
            
            while True:
                if cancel_check and cancel_check():
                    logger.info("Email search cancelled by user")
                    return []
                try:
                    search_params = {'userId': 'me', 'q': query}
                    if page_token:
                        search_params['pageToken'] = page_token
                    results = self.service.users().messages().list(**search_params).execute()
                except HttpError as e:
                    logger.error(f"Gmail API error during search: {e}")
                    raise Exception(f"Gmail API fel vid sökning: {e}")
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                page_count += 1
                logger.info(f"📄 Page {page_count}: Found {len(messages)} messages (Total: {len(all_messages)})")
                
                if progress_callback:
                    progress_callback(f"Hämtat {len(all_messages)} emails från {page_count} sidor...", 0)
                if gui_update_callback:
                    gui_update_callback()
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"🎯 FINAL RESULT: Found {len(all_messages)} emails matching query '{query}'")
            return [msg['id'] for msg in all_messages]
            
        except HttpError as error:
            logger.error(f"HTTP error during email search: {error}")
            raise Exception(f"Ett fel uppstod vid sökning: {error}")
        except Exception as e:
            logger.error(f"Unexpected error during email search: {e}")
            raise

class AttachmentProcessor:
    def __init__(self, gmail_service):
        self.service = gmail_service
    
    def get_email_details(self, message_id: str) -> Optional[Dict]:
        try:
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Inget ämne')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Okänd avsändare')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Okänt datum')
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'payload': message['payload']
            }
        except HttpError as error:
            logger.warning(f"Failed to get email details for {message_id}: {error}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error getting email details: {e}")
            return None
    
    def _process_email_part(self, part: Dict, attachments: List[Dict]) -> None:
        if part.get('filename'):
            filename = part['filename']
            if filename.lower().endswith(('.jpg', '.jpeg')):
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachments.append({
                        'filename': filename,
                        'attachment_id': attachment_id,
                        'size': part['body'].get('size', 0)
                    })
        if 'parts' in part:
            for subpart in part['parts']:
                self._process_email_part(subpart, attachments)
    
    def extract_attachments(self, payload: Dict) -> List[Dict]:
        attachments = []
        self._process_email_part(payload, attachments)
        return attachments
    
    def download_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        try:
            attachment = self.service.users().messages().attachments().get(userId='me', messageId=message_id, id=attachment_id).execute()
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            return file_data
        except HttpError as error:
            logger.warning(f"Failed to download attachment {attachment_id}: {error}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error downloading attachment: {e}")
            return None

class DownloadManager:
    def __init__(self, output_dir: str):
        self.output_path = Path(output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.overwrite_all = False
        self.skip_all = False
    
    def handle_filename_conflict(self, original_filename: str, root: tk.Tk) -> Optional[str]:
        file_path = self.output_path / original_filename
        if not file_path.exists():
            return original_filename
        
        if self.overwrite_all:
            logger.info(f"Overwriting file (Overwrite All selected): {original_filename}")
            return original_filename
        
        if self.skip_all:
            logger.info(f"Skipping file (Skip All selected): {original_filename}")
            return "SKIP"  # Special value to indicate skip
        
        # Show dialog for file conflict
        dialog = tk.Toplevel(root)
        dialog.title("Filkonflikt")
        dialog.geometry("500x400")
        dialog.transient(root)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (200)
        dialog.geometry(f"500x400+{x}+{y}")
        
        tk.Label(dialog, text=f"Filen {original_filename} finns redan.\nVad vill du göra?", font=("Arial", 12)).pack(pady=20)
        
        result = tk.StringVar(value="cancel")
        
        def set_overwrite():
            result.set("overwrite")
            dialog.destroy()
        
        def set_overwrite_all():
            self.overwrite_all = True
            result.set("overwrite")
            dialog.destroy()
        
        def set_skip():
            result.set("skip")
            dialog.destroy()
        
        def set_skip_all():
            self.skip_all = True
            result.set("skip")
            dialog.destroy()
        
        def set_cancel():
            result.set("cancel")
            dialog.destroy()
        
        # Button frame for better layout
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Skriv över", command=set_overwrite, width=15, font=("Arial", 10)).pack(pady=5)
        tk.Button(button_frame, text="Skriv över alla", command=set_overwrite_all, width=15, font=("Arial", 10)).pack(pady=5)
        tk.Button(button_frame, text="Hoppa över", command=set_skip, width=15, font=("Arial", 10)).pack(pady=5)
        tk.Button(button_frame, text="Hoppa över alla", command=set_skip_all, width=15, font=("Arial", 10)).pack(pady=5)
        tk.Button(button_frame, text="Avbryt", command=set_cancel, width=15, font=("Arial", 10)).pack(pady=5)
        
        root.wait_window(dialog)
        
        if result.get() == "overwrite":
            logger.info(f"Overwriting file: {original_filename}")
            return original_filename
        elif result.get() == "skip":
            logger.info(f"Skipping file: {original_filename}")
            return "SKIP"  # Special value to indicate skip
        else:
            logger.info(f"Download cancelled by user for file: {original_filename}")
            return None  # None means cancel entire operation
    
    def save_file(self, filename: str, file_data: bytes) -> bool:
        file_path = self.output_path / filename
        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
            file_size = len(file_data)
            logger.info(f"✅ Downloaded: {filename} ({self.format_file_size(file_size)})")
            return True
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            return False
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def get_output_path(self) -> str:
        return str(self.output_path.absolute())

class GmailDownloader:
    def __init__(self, credentials_file: str = None, gmail_account: str = None):
        self.authenticator = GmailAuthenticator(credentials_file, gmail_account) if credentials_file and gmail_account else None
        self.cancel_requested = False
        self.searcher = None
        self.attachment_processor = None
        self.download_manager = None
        self.root = None  # Reference to root window for dialogs
    
    def set_root(self, root: tk.Tk):
        """Set the root window for dialog purposes"""
        self.root = root
    
    def cancel_operation(self):
        self.cancel_requested = True
        logger.info("Download cancellation requested")
    
    def reset_cancel_state(self):
        self.cancel_requested = False
    
    def _check_cancellation(self) -> bool:
        return self.cancel_requested
    
    def authenticate(self, progress_callback=None, gui_update_callback=None):
        if not self.authenticator:
            raise AuthenticationError("Authenticator not initialized")
        self.authenticator.authenticate(progress_callback, gui_update_callback)
        service = self.authenticator.get_service()
        self.searcher = GmailSearcher(service)
        self.attachment_processor = AttachmentProcessor(service)
    
    def _process_single_email(self, message_id: str, email_num: int, total_emails: int, 
                             progress_callback=None, gui_update_callback=None) -> Tuple[int, int, int]:
        downloaded = 0
        skipped = 0
        total_size = 0
        
        progress = int((email_num / total_emails) * 100)
        if progress_callback:
            progress_callback(f"Bearbetar email {email_num}/{total_emails}", progress)
        if gui_update_callback:
            gui_update_callback()
        
        email_details = self.attachment_processor.get_email_details(message_id)
        if not email_details:
            return downloaded, skipped, total_size
        
        logger.info(f"📨 Processing email from: {email_details['sender']}")
        
        attachments = self.attachment_processor.extract_attachments(email_details['payload'])
        jpg_attachments = [att for att in attachments if att['filename'].lower().endswith(('.jpg', '.jpeg'))]
        
        if not jpg_attachments:
            logger.info(f"   No JPG attachments found in this email")
            return downloaded, skipped, total_size
        
        logger.info(f"   Found {len(jpg_attachments)} JPG attachment(s)")
        
        for att_num, attachment in enumerate(jpg_attachments, 1):
            if self._check_cancellation():
                return downloaded, skipped, total_size
            
            if len(jpg_attachments) > 1:
                if progress_callback:
                    progress_callback(f"Email {email_num}/{total_emails} - Bilaga {att_num}/{len(jpg_attachments)}", progress)
                if gui_update_callback:
                    gui_update_callback()
            
            file_data = self.attachment_processor.download_attachment(message_id, attachment['attachment_id'])
            if not file_data:
                continue
            
            original_filename = attachment['filename']
            final_filename = self.download_manager.handle_filename_conflict(original_filename, self.root)
            
            if final_filename is None:
                self.cancel_operation()  # Cancel the entire process if user chooses to cancel
                return downloaded, skipped, total_size
            elif final_filename == "SKIP":
                skipped += 1
                logger.info(f"Skipped file: {original_filename}")
                continue  # Continue with next attachment
            
            if self.download_manager.save_file(final_filename, file_data):
                downloaded += 1
                total_size += len(file_data)
        
        return downloaded, skipped, total_size
    
    def download_attachments(self, sender_email: str, start_date: str, end_date: str, 
                           output_dir: str, progress_callback=None, gui_update_callback=None) -> Dict:
        """Download JPG attachments from Gmail"""
        self.reset_cancel_state()
        
        # Use default sender if empty
        sender_email = sender_email or "noreply@kb.se"
        
        try:
            logger.info(f"🚀 Starting download process")
            logger.info(f"📧 Sender: {sender_email}")
            logger.info(f"📅 Date range: {start_date} to {end_date if end_date else 'same day'}")
            
            self.download_manager = DownloadManager(output_dir)
            
            if progress_callback:
                progress_callback("Bygger sökfråga...", 5)
            if gui_update_callback:
                gui_update_callback()
            
            query = self.searcher.build_search_query(sender_email, start_date, end_date)
            message_ids = self.searcher.search_emails(query, progress_callback, gui_update_callback, self._check_cancellation)
            
            if self._check_cancellation():
                return {"cancelled": True}
            
            if not message_ids:
                logger.warning(f"❌ No emails found with query: '{query}'")
                return {
                    "total_emails": 0, 
                    "downloaded": 0, 
                    "skipped": 0,
                    "total_size": 0,
                    "search_query": query,
                    "output_path": output_dir
                }
            
            total_downloaded = 0
            total_size = 0
            skipped_count = 0
            processed_emails = 0
            
            for i, message_id in enumerate(message_ids, 1):
                if self._check_cancellation():
                    logger.info(f"Download cancelled after processing {processed_emails} emails")
                    return {"cancelled": True}
                
                downloaded, skipped, size = self._process_single_email(
                    message_id, i, len(message_ids), 
                    progress_callback, gui_update_callback)
                
                total_downloaded += downloaded
                skipped_count += skipped
                total_size += size
                if downloaded > 0 or skipped > 0:
                    processed_emails += 1
            
            result = {
                "total_emails": len(message_ids),
                "processed_emails": processed_emails,
                "downloaded": total_downloaded,
                "skipped": skipped_count,
                "total_size": total_size,
                "output_path": self.download_manager.get_output_path(),
                "search_query": query
            }
            
            logger.info(f"🎯 Download completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during download process: {e}")
            raise Exception(f"Ett fel uppstod under nedladdningen: {str(e)}")

# ============================
# KB PROCESSING CLASSES
# ============================
class KBProcessor:
    def __init__(self):
        self.cancel_requested = False
    
    def cancel_operation(self):
        self.cancel_requested = True
    
    def reset_cancel_state(self):
        self.cancel_requested = False
    
    def validate_excel_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate Excel file format and content"""
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                return False, "Pandas inte installerat - KB-funktionalitet inte tillgänglig"
            
            df = pd.read_excel(file_path, header=None)
            
            if df.shape[1] < 2:
                return False, "Excel-filen måste ha minst 2 kolumner (bib-kod och tidningsnamn)"
            
            if df.shape[0] == 0:
                return False, "Excel-filen är tom"
            
            return True, f"Excel-filen validerad: {len(df)} bib-koder hittades"
            
        except Exception as e:
            return False, f"Fel vid läsning av Excel-fil: {str(e)}"
    
    def validate_directories(self, input_dir: str, output_dir: str) -> Tuple[bool, List[str]]:
        """Validate input and output directories"""
        errors = []
        
        if not input_dir or not os.path.exists(input_dir):
            errors.append("Input-mappen existerar inte")
        
        if not output_dir:
            errors.append("Output-mapp måste väljas")
        else:
            try:
                os.makedirs(output_dir, exist_ok=True)
                if not os.access(output_dir, os.W_OK):
                    errors.append("Output-mappen kan inte skrivas till")
            except Exception as e:
                errors.append(f"Kan inte skapa/komma åt output-mappen: {str(e)}")
        
        return len(errors) == 0, errors
    
    def process_files(self, excel_path: str, input_dir: str, output_dir: str, 
                     keep_renamed: bool = False, progress_callback=None, 
                     gui_update_callback=None) -> Dict:
        """Process KB files - real implementation"""
        self.reset_cancel_state()
        
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                raise Exception("PIL/Pandas inte installerat - KB-funktionalitet inte tillgänglig")
            
            logger.info(f"=== Starting KB processing ===")
            logger.info(f"Excel file: {excel_path}")
            logger.info(f"Input dir: {input_dir}")
            logger.info(f"Output dir: {output_dir}")
            logger.info(f"Keep renamed: {keep_renamed}")
            
            # Load Excel file
            if progress_callback:
                progress_callback("Läser Excel-fil...", 2)
            if gui_update_callback:
                gui_update_callback()
            
            try:
                bib_df = pd.read_excel(excel_path, header=None)
                bib_dict = dict(zip(bib_df[0].astype(str), bib_df[1].astype(str)))
                logger.info(f"Loaded {len(bib_dict)} bib codes from Excel")
            except Exception as e:
                raise Exception(f"Kunde inte läsa Excel-filen: {str(e)}")
            
            # Setup directories
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if keep_renamed:
                temp_path = output_path / "Jpg-filer med fina namn"
                temp_path.mkdir(parents=True, exist_ok=True)
            else:
                temp_path = Path(tempfile.mkdtemp(prefix="renamed_jpgs_"))
            
            # Find JPG files
            jpg_files = sorted(f for f in input_path.glob("*.jpg") if f.is_file())
            
            if not jpg_files:
                return {
                    "total_files": 0,
                    "created_count": 0,
                    "error": "Inga JPG-filer hittades"
                }
            
            logger.info(f"Found {len(jpg_files)} JPG files to process")
            
            # Phase 1: Rename files
            if progress_callback:
                progress_callback("Fas 1: Döper om filer...", 5)
            if gui_update_callback:
                gui_update_callback()
            
            renamed_files = []
            total_files = len(jpg_files)
            
            for i, file in enumerate(jpg_files):
                if self.cancel_requested:
                    return {"cancelled": True}
                
                # Update progress for renaming phase with percentage
                rename_progress = 5 + int((i / total_files) * 30)  # 5-35%
                percentage = int(((i + 1) / total_files) * 100)
                if progress_callback:
                    progress_callback(f"Döper om fil {i+1}/{total_files} ({percentage}%): {file.name}", rename_progress)
                if gui_update_callback:
                    gui_update_callback()
                
                stem = file.stem
                suffix = file.suffix
                extra = ""
                
                # Handle duplicate numbering in parentheses
                if "(" in stem and ")" in stem[-3:]:
                    base, extra = stem.rsplit("(", 1)
                    extra = "(" + extra
                    stem = base.strip("_ ")
                
                parts = stem.split("_")
                if len(parts) < 5:
                    logger.warning(f"Skipping file with unexpected format: {file.name}")
                    continue
                
                bib = parts[0]
                date_raw = parts[1]
                
                # Format date
                try:
                    date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
                except:
                    date = "0000-00-00"
                    logger.warning(f"Could not parse date from: {date_raw}")
                
                siffergrupper = "_".join(parts[2:5])
                tidning = bib_dict.get(bib, "OKÄND").upper()
                
                # Create new filename with bib code included
                new_name = f"{date} {tidning} {bib} {siffergrupper}{extra}{suffix}"
                dest = temp_path / new_name
                
                try:
                    shutil.copy(file, dest)
                    renamed_files.append(dest)
                    logger.debug(f"Renamed: {file.name} -> {new_name}")
                except Exception as e:
                    logger.error(f"Failed to copy {file.name}: {e}")
                    continue
            
            logger.info(f"Successfully renamed {len(renamed_files)} files")
            
            # Group files for PDF creation
            if progress_callback:
                progress_callback("Grupperar filer för PDF-skapande...", 35)
            if gui_update_callback:
                gui_update_callback()
            
            grouped = {}
            for f in renamed_files:
                parts = f.stem.split()
                if len(parts) < 4:  # date, newspaper, bib, numbers
                    logger.warning(f"Unexpected renamed file format: {f.name}")
                    continue
                
                # Group by date and newspaper (excluding bib and numbers)
                key = (parts[0], " ".join(parts[1:-2]))
                grouped.setdefault(key, []).append(f)
            
            logger.info(f"Grouped {len(renamed_files)} files into {len(grouped)} PDF groups")
            
            # Phase 2: Create PDFs
            created_count = 0
            overwritten_count = 0
            skipped_count = 0
            pdfs_per_tidning = defaultdict(int)
            
            total_pdfs = len(grouped)
            
            for pdf_num, ((date, newspaper), files) in enumerate(grouped.items(), 1):
                if self.cancel_requested:
                    return {"cancelled": True}
                
                # Update progress for PDF creation phase with percentage
                pdf_progress = 35 + int((pdf_num / total_pdfs) * 60)  # 35-95%
                percentage = int((pdf_num / total_pdfs) * 100)
                if progress_callback:
                    progress_callback(f"Skapar PDF {pdf_num}/{total_pdfs} ({percentage}%): {newspaper}", pdf_progress)
                if gui_update_callback:
                    gui_update_callback()
                
                if not files:
                    continue
                
                # Sort files for consistent ordering
                sorted_files = sorted(files)
                
                # Determine PDF filename - always include page count
                pdf_name = f"{date} {newspaper} ({len(sorted_files)} sid).pdf"
                
                pdf_path = output_path / pdf_name
                
                # Handle existing PDF files with dialog
                if pdf_path.exists():
                    # Show dialog for PDF file conflict
                    dialog = tk.Toplevel(self.root)
                    dialog.title("PDF-filkonflikt")
                    dialog.geometry("500x400")
                    dialog.transient(self.root)
                    dialog.grab_set()
                    dialog.lift()
                    dialog.focus_force()
                    dialog.attributes('-topmost', True)
                    dialog.after(100, lambda: dialog.attributes('-topmost', False))
                    
                    # Center the dialog
                    dialog.update_idletasks()
                    x = (dialog.winfo_screenwidth() // 2) - (250)
                    y = (dialog.winfo_screenheight() // 2) - (200)
                    dialog.geometry(f"500x400+{x}+{y}")
                    
                    tk.Label(dialog, text=f"PDF-filen {pdf_name} finns redan.\\nVad vill du göra?", 
                            font=("Arial", 12)).pack(pady=20)
                    
                    # Variables for dialog result
                    dialog_result = {"action": None}
                    
                    def set_overwrite():
                        dialog_result["action"] = "overwrite"
                        dialog.destroy()
                    
                    def set_overwrite_all():
                        dialog_result["action"] = "overwrite_all"
                        dialog.destroy()
                    
                    def set_skip():
                        dialog_result["action"] = "skip"
                        dialog.destroy()
                    
                    def set_skip_all():
                        dialog_result["action"] = "skip_all"
                        dialog.destroy()
                    
                    def set_cancel():
                        dialog_result["action"] = "cancel"
                        dialog.destroy()
                    
                    # Button frame for better layout
                    button_frame = tk.Frame(dialog)
                    button_frame.pack(pady=20)
                    
                    tk.Button(button_frame, text="Skriv över", command=set_overwrite, 
                             width=15, font=("Arial", 10)).pack(pady=3)
                    tk.Button(button_frame, text="Skriv över alla", command=set_overwrite_all, 
                             width=15, font=("Arial", 10)).pack(pady=3)
                    tk.Button(button_frame, text="Hoppa över", command=set_skip, 
                             width=15, font=("Arial", 10)).pack(pady=3)
                    tk.Button(button_frame, text="Hoppa över alla", command=set_skip_all, 
                             width=15, font=("Arial", 10)).pack(pady=3)
                    tk.Button(button_frame, text="Avbryt", command=set_cancel, 
                             width=15, font=("Arial", 10)).pack(pady=3)
                    
                    # Wait for dialog result
                    dialog.wait_window()
                    
                    # Handle dialog result
                    if dialog_result["action"] == "cancel":
                        return {"cancelled": True}
                    elif dialog_result["action"] == "skip":
                        skipped_count += 1
                        logger.info(f"Skipped existing PDF: {pdf_name}")
                        continue
                    elif dialog_result["action"] == "skip_all":
                        # Skip all remaining PDFs
                        for remaining_pdf in grouped.items():
                            if remaining_pdf[0] != (date, newspaper):
                                skipped_count += 1
                        logger.info(f"Skipping all remaining PDFs")
                        break
                    elif dialog_result["action"] == "overwrite_all":
                        # Overwrite all remaining PDFs
                        overwritten_count += 1
                        logger.info(f"Overwriting existing PDF: {pdf_name}")
                    else:  # overwrite
                        overwritten_count += 1
                        logger.info(f"Overwriting existing PDF: {pdf_name}")
                else:
                    created_count += 1
                
                # Create PDF using PIL
                try:
                    # Verify first image is valid
                    with Image.open(sorted_files[0]) as first_img:
                        if first_img.mode != 'RGB':
                            first_img = first_img.convert('RGB')
                        
                        # Stream images directly to PDF to minimize memory usage
                        with first_img as base_img:
                            base_img.save(
                                pdf_path,
                                save_all=True,
                                append_images=[
                                    Image.open(f).convert('RGB') if Image.open(f).mode != 'RGB' 
                                    else Image.open(f)
                                    for f in sorted_files[1:]
                                    if not self.cancel_requested
                                ]
                            )
                    
                    pdfs_per_tidning[newspaper] += 1
                    logger.info(f"Created PDF: {pdf_name} ({len(sorted_files)} pages)")
                    
                except Exception as e:
                    logger.error(f"Failed to create PDF {pdf_name}: {e}")
                    continue
            
            # Cleanup temporary files
            if not keep_renamed:
                if progress_callback:
                    progress_callback("Städar temporära filer...", 98)
                if gui_update_callback:
                    gui_update_callback()
                
                try:
                    shutil.rmtree(temp_path, ignore_errors=True)
                    logger.info("Cleaned up temporary files")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp files: {e}")
            
            if progress_callback:
                progress_callback("KB-bearbetning slutförd!", 100)
            if gui_update_callback:
                gui_update_callback()
            
            result = {
                "total_files": len(jpg_files),
                "created_count": created_count,
                "overwritten_count": overwritten_count,
                "skipped_count": skipped_count,
                "pdfs_per_tidning": dict(pdfs_per_tidning),
                "output_path": str(output_path.absolute())
            }
            
            logger.info(f"KB processing completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"KB processing error: {e}")
            raise Exception(f"KB processing error: {str(e)}")

# ============================
# MAIN GUI APPLICATION
# ============================
class CombinedApp:
    def __init__(self):
        self.setup_gui()
        self.config = load_config()
        self.gmail_downloader = None
        self.kb_processor = KBProcessor()
        self.load_config_to_gui()
        
        # Track which operations are running
        self.gmail_running = False
        self.kb_running = False
    
    def get_app_directory(self):
        """Get the directory where the application is located (works for both .py and .exe)"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            return Path(sys.executable).parent
        else:
            # Running as Python script
            return Path(__file__).parent
    
    def setup_gui(self):
        """Setup the main GUI window"""
        self.root = tb.Window(themename="superhero")
        self.root.title("DJs app för hantering av filer från 'Svenska Tidningar'")
        
        # Set window icon
        try:
            icon_path = Path(__file__).parent / "Agg-med-smor-v4-transperent.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")
        
        self.root.geometry("1320x1440")  # 20% larger: 1100*1.2=1320, 1200*1.2=1440
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (660)  # 1320/2=660
        y = 10  # Position window very close to the top of the screen
        self.root.geometry(f"1320x1440+{x}+{y}")
        # Add a canvas+scrollbar for main content
        canvas = tk.Canvas(self.root)
        scrollbar = tb.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.main_canvas = canvas
        self.main_scrollbar = scrollbar
        main_frame = tb.Frame(canvas)
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        main_frame.bind("<Configure>", on_configure)
        self.main_frame = main_frame
        
        # Add menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=help_menu)
        help_menu.add_command(label="Manual", command=self.open_manual)
        help_menu.add_command(label="Om appen", command=self.show_about)
        
        self.create_variables()
        self.create_widgets()
    
    def create_variables(self):
        """Create tkinter variables"""
        # Tool selection
        self.gmail_enabled = tk.BooleanVar()
        self.kb_enabled = tk.BooleanVar()
        
        # Gmail variables
        self.gmail_account_var = tk.StringVar()
        self.credentials_file_var = tk.StringVar()
        self.sender_var = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.gmail_output_dir_var = tk.StringVar()
        
        # KB variables
        self.excel_path_var = tk.StringVar()
        self.kb_input_dir_var = tk.StringVar()
        self.kb_output_dir_var = tk.StringVar()
        self.keep_renamed_var = tk.BooleanVar()
        
        # Status
        self.status_var = tk.StringVar(value="Redo att börja")
        
        # Progress
        self.progress_message_var = tk.StringVar(value="")
        
        # Bind checkbox events
        self.gmail_enabled.trace('w', self.on_gmail_toggle)
        self.kb_enabled.trace('w', self.on_kb_toggle)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = tb.Frame(self.main_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = tb.Label(main_frame, text="DJs app för hantering av filer från 'Svenska Tidningar'", 
                              font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Tool selection frame
        selection_frame = tb.LabelFrame(main_frame, text="Välj verktyg", padding=15)
        selection_frame.pack(fill="x", pady=(0, 20))
        
        self.gmail_check = tb.Checkbutton(selection_frame, text="Ladda ned jpg-bilagor från Svenska Tidningar via Gmail API", 
                                         variable=self.gmail_enabled, bootstyle="success-round-toggle")
        self.gmail_check.pack(anchor="w", pady=5)
        
        self.kb_check = tb.Checkbutton(selection_frame, text="Gör om jpg-filer till pdf-filer, ge begripliga namn och slå ihop flersidiga artiklar", 
                                      variable=self.kb_enabled, bootstyle="success-round-toggle")
        self.kb_check.pack(anchor="w", pady=5)
        

        
        # Gmail section
        self.create_gmail_section(main_frame)
        
        # KB section  
        self.create_kb_section(main_frame)
        
        # Action buttons and progress
        self.create_action_section(main_frame)
        
        # Status
        self.create_status_section(main_frame)
        
        # Version label
        version_label = tb.Label(self.root, text=f"v{VERSION}", 
                                font=('Arial', 8), foreground="gray")
        version_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        
        # Initial state
        self.update_ui_state()
    
    def validate_date_entry(self, input_str: str) -> bool:
        # Allow empty input (user deleting)
        if not input_str:
            return True
        # Allow only digits and dashes, max 10 chars (YYYY-MM-DD = 10 chars)
        if not re.match(r"^[0-9-]{0,10}$", input_str):
            return False
        # Only allow at most 2 dashes, and not at the start
        if input_str.count('-') > 2 or input_str.startswith('-'):
            return False
        # Allow up to 10 characters for full date format
        if len(input_str) > 10:
            return False
        return True

    def full_date_validation(self, field: str):
        # Get the value
        value = self.start_date_var.get() if field == "start" else self.end_date_var.get()
        # Only validate if length is 10 (full date)
        if len(value) == 10:
            self.validate_date(value, field)
        else:
            self.update_date_validation_label(value, field, False)

    def create_gmail_section(self, parent):
        """Create Gmail downloader section"""
        self.gmail_frame = tb.LabelFrame(parent, text="Gmail JPG Nedladdare", padding=20)
        
        # Gmail account
        gmail_account_frame = tb.Frame(self.gmail_frame)
        gmail_account_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(gmail_account_frame, text="Gmail-konto:", font=('Arial', 10)).pack(side="left")
        gmail_entry = tb.Entry(gmail_account_frame, textvariable=self.gmail_account_var, 
                              width=40, font=('Arial', 10))
        gmail_entry.pack(side="left", padx=(15, 0), fill="x", expand=True)
        
        # Credentials file
        creds_frame = tb.Frame(self.gmail_frame)
        creds_frame.pack(fill="x", pady=(0, 15))
        
        # Frame for "Credentials-fil:" label and question mark
        cred_label_frame = tb.Frame(creds_frame)
        cred_label_frame.pack(anchor="w")
        tb.Label(cred_label_frame, text="Credentials-fil:", font=('Arial', 10)).pack(side="left")
        help_label = tb.Label(cred_label_frame, text=" ?", font=('Arial', 10, "bold"), foreground="green", cursor="hand2")
        help_label.pack(side="left")
        def open_manual_event(event=None):
            manual_path = self.get_app_directory() / "Manual.docx"
            if manual_path.exists():
                try:
                    if sys.platform.startswith('win'):
                        # Use os.startfile instead of subprocess for better Windows compatibility
                        import os
                        os.startfile(str(manual_path))
                    elif sys.platform.startswith('darwin'):
                        subprocess.run(['open', str(manual_path)])
                    else:
                        subprocess.run(['xdg-open', str(manual_path)])
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte öppna Manual.docx: {e}")
            else:
                messagebox.showerror("Fel", f"Manual.docx hittades inte i programmets mapp.\nSökte i: {manual_path}")
        help_label.bind("<Button-1>", open_manual_event)
        
        creds_path_frame = tb.Frame(creds_frame)
        creds_path_frame.pack(fill="x")
        
        creds_entry = tb.Entry(creds_path_frame, textvariable=self.credentials_file_var, 
                              font=('Arial', 10), state="readonly")
        creds_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_creds_btn = tb.Button(creds_path_frame, text="Välj fil...", 
                                    command=self.browse_credentials_file, 
                                    bootstyle=INFO, width=12)
        browse_creds_btn.pack(side="right")
        
        # Sender email
        sender_frame = tb.Frame(self.gmail_frame)
        sender_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(sender_frame, text="Avsändar-email:", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        sender_entry_frame = tb.Frame(sender_frame)
        sender_entry_frame.pack(fill="x")
        sender_entry = tb.Entry(sender_entry_frame, textvariable=self.sender_var, 
                               width=40, font=('Arial', 10))
        sender_entry.pack(side="left", padx=(0, 0), fill="x", expand=True)
        
        tb.Label(sender_frame, text="Lämna tomt för noreply@kb.se", 
                 font=('Arial', 9), foreground="lightblue").pack(anchor="w", pady=(5, 0))
        
        # Date range
        date_frame = tb.Frame(self.gmail_frame)
        date_frame.pack(fill="x", pady=(0, 15))
        
        # Start date with validation
        start_date_frame = tb.Frame(date_frame)
        start_date_frame.pack(side="left", padx=(0, 20))
        tb.Label(start_date_frame, text="Startdatum:", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        vcmd_start = (self.root.register(self.validate_date_entry), '%P')
        start_date_entry = tb.Entry(start_date_frame, textvariable=self.start_date_var, 
                                   width=15, font=('Consolas', 11), 
                                   validate="key", 
                                   validatecommand=vcmd_start)
        start_date_entry.pack(side="left")
        self.start_date_validation_label = tb.Label(start_date_frame, text="", font=('Arial', 10))
        self.start_date_validation_label.pack(side="left", padx=(5, 0))
        start_date_entry.bind('<KeyRelease>', lambda e: self.full_date_validation('start'))
        start_date_entry.bind('<FocusOut>', lambda e: self.full_date_validation('start'))
        
        # End date with validation
        end_date_frame = tb.Frame(date_frame)
        end_date_frame.pack(side="left")
        tb.Label(end_date_frame, text="Slutdatum:", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        vcmd_end = (self.root.register(self.validate_date_entry), '%P')
        end_date_entry = tb.Entry(end_date_frame, textvariable=self.end_date_var, 
                                 width=15, font=('Consolas', 11),
                                 validate="key", 
                                 validatecommand=vcmd_end)
        end_date_entry.pack(side="left")
        self.end_date_validation_label = tb.Label(end_date_frame, text="", font=('Arial', 10))
        self.end_date_validation_label.pack(side="left", padx=(5, 0))
        end_date_entry.bind('<KeyRelease>', lambda e: self.full_date_validation('end'))
        end_date_entry.bind('<FocusOut>', lambda e: self.full_date_validation('end'))
        
        # Date explanation
        date_info_frame = tb.Frame(self.gmail_frame)
        date_info_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(date_info_frame, text="Lämna slutdatum tomt om du bara vill hämta från ett specifikt datum", 
                 font=('Arial', 9), foreground="lightblue").pack(anchor="w")
        
        # Output directory
        gmail_output_frame = tb.Frame(self.gmail_frame)
        gmail_output_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(gmail_output_frame, text="Nedladdningsmapp:", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        gmail_output_path_frame = tb.Frame(gmail_output_frame)
        gmail_output_path_frame.pack(fill="x")
        
        gmail_output_entry = tb.Entry(gmail_output_path_frame, textvariable=self.gmail_output_dir_var, 
                                     font=('Arial', 10))
        gmail_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_gmail_output_btn = tb.Button(gmail_output_path_frame, text="Bläddra...", 
                                           command=self.browse_gmail_output_dir, 
                                           bootstyle=INFO, width=12)
        browse_gmail_output_btn.pack(side="right")
    
    def validate_date(self, input_str: str, field: str) -> bool:
        """Validate date format and trigger cross-field validation"""
        # Allow empty input
        if not input_str:
            self.update_date_validation_label(input_str, field, True)
            self.cross_validate_dates(field)
            return True

        # Check format and validate date
        normalized = None
        if re.match(r"^\d{4}-\d{2}-\d{2}$", input_str):
            # Already in correct format
            normalized = input_str
        elif re.match(r"^\d{8}$", input_str):
            # Convert YYYYMMDD to YYYY-MM-DD
            normalized = f"{input_str[:4]}-{input_str[4:6]}-{input_str[6:]}"
        else:
            # Invalid format
            self.update_date_validation_label(input_str, field, False)
            return False

        # Validate the actual date
        try:
            datetime.datetime.strptime(normalized, "%Y-%m-%d")
            # Update the variable with normalized format
            if field == "start":
                self.start_date_var.set(normalized)
            else:
                self.end_date_var.set(normalized)
            self.update_date_validation_label(normalized, field, True)
            self.cross_validate_dates(field)
            return True
        except ValueError:
            # Invalid date (like 2024-13-15 or 2024-01-32)
            self.update_date_validation_label(input_str, field, False)
            return False

    def update_date_validation_label(self, input_str: str, field: str, is_format_valid: bool):
        """Update validation label for date fields"""
        start_label = self.start_date_validation_label
        end_label = self.end_date_validation_label
        target_label = start_label if field == "start" else end_label

        # Clear if empty
        if not input_str:
            target_label.config(text="", foreground="green")
            return

        # Show validation result
        if is_format_valid:
            target_label.config(text="✓", foreground="green")
        else:
            target_label.config(text="✗", foreground="red")

    def cross_validate_dates(self, updated_field: str) -> bool:
        """Cross-validate start and end dates"""
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        start_label = self.start_date_validation_label
        end_label = self.end_date_validation_label

        # If either field is empty, just show format validation
        if not start_date or not end_date:
            return True

        # Parse dates
        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return False

        # Check if start <= end
        if start_dt <= end_dt:
            start_label.config(text="✓", foreground="green")
            end_label.config(text="✓", foreground="green")
            return True
        else:
            # Mark the inconsistent field
            invalid_label = start_label if updated_field == "start" else end_label
            valid_label = end_label if updated_field == "start" else start_label
            invalid_label.config(text="✗", foreground="red")
            valid_label.config(text="✓", foreground="green")
            return False
    
    def create_kb_section(self, parent):
        """Create KB processor section"""
        self.kb_frame = tb.LabelFrame(parent, text="KB Filbearbetning", padding=20)
        
        # Excel file
        excel_frame = tb.Frame(self.kb_frame)
        excel_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(excel_frame, text="Excel-fil med bib-koder översatta till tidningsnamn):", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        excel_path_frame = tb.Frame(excel_frame)
        excel_path_frame.pack(fill="x")
        
        excel_entry = tb.Entry(excel_path_frame, textvariable=self.excel_path_var, 
                              font=('Arial', 10), state="readonly")
        excel_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_excel_btn = tb.Button(excel_path_frame, text="Välj fil...", 
                                    command=self.browse_excel_file, 
                                    bootstyle=INFO, width=12)
        browse_excel_btn.pack(side="right")
        
        # Excel validation label
        self.excel_validation_label = tb.Label(excel_frame, text="", font=('Arial', 9), foreground="green")
        self.excel_validation_label.pack(anchor="w", pady=(5, 0))
        
        # Input directory
        kb_input_frame = tb.Frame(self.kb_frame)
        kb_input_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(kb_input_frame, text="Mapp där jpg-filerna finns:", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        kb_input_path_frame = tb.Frame(kb_input_frame)
        kb_input_path_frame.pack(fill="x")
        
        self.kb_input_entry = tb.Entry(kb_input_path_frame, textvariable=self.kb_input_dir_var, 
                                      font=('Arial', 10))
        self.kb_input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.browse_kb_input_btn = tb.Button(kb_input_path_frame, text="Bläddra...", 
                                            command=self.browse_kb_input_dir, 
                                            bootstyle=INFO, width=12)
        self.browse_kb_input_btn.pack(side="right")
        
        # Auto-link info
        self.kb_auto_info = tb.Label(kb_input_frame, 
                                    text="📁 Om båda verktygen är aktiverade så används samma mapp där jpg-filerna sparades.",
                                    font=('Arial', 9), foreground="lightgreen")
        
        # Output directory
        kb_output_frame = tb.Frame(self.kb_frame)
        kb_output_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(kb_output_frame, text="Var ska pdf:erna sparas?", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        kb_output_path_frame = tb.Frame(kb_output_frame)
        kb_output_path_frame.pack(fill="x")
        
        kb_output_entry = tb.Entry(kb_output_path_frame, textvariable=self.kb_output_dir_var, 
                                  font=('Arial', 10))
        kb_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_kb_output_btn = tb.Button(kb_output_path_frame, text="Bläddra...", 
                                        command=self.browse_kb_output_dir, 
                                        bootstyle=INFO, width=12)
        browse_kb_output_btn.pack(side="right")
        
        # Keep renamed files checkbox (moved under output directory)
        keep_frame = tb.Frame(self.kb_frame)
        keep_frame.pack(fill="x", pady=(0, 10))
        
        # Create a frame for the checkbox and colored text
        checkbox_frame = tb.Frame(keep_frame)
        checkbox_frame.pack(anchor="w")
        
        # Create the checkbox without text
        tb.Checkbutton(checkbox_frame, text="", variable=self.keep_renamed_var, 
                      bootstyle="info-round-toggle").pack(side="left")
        
        # Create a text widget for colored text
        text_widget = tk.Text(checkbox_frame, height=1, width=70, wrap="word", 
                             borderwidth=0, relief="flat", background="SystemButtonFace", 
                             font=('Arial', 9), cursor="hand2")
        text_widget.pack(side="left", padx=(5, 0))
        text_widget.insert("1.0", "Spara omdöpta jpg-filer i en underkatalog?")
        text_widget.config(state="disabled")  # Make it read-only
        
        # Bind click events to toggle the checkbox
        def toggle_checkbox(event):
            self.keep_renamed_var.set(not self.keep_renamed_var.get())
        
        text_widget.bind("<Button-1>", toggle_checkbox)
    
    def create_action_section(self, parent):
        """Create action buttons and progress section"""
        action_frame = tb.Frame(parent)
        action_frame.pack(fill="x", pady=(30, 0))
        
        button_frame = tb.Frame(action_frame)
        button_frame.pack(pady=(0, 10))
        
        self.start_btn = tb.Button(button_frame, text="Starta bearbetning", 
                                  command=self.start_processing, 
                                  bootstyle=SUCCESS, width=25)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        self.cancel_btn = tb.Button(button_frame, text="Avbryt", 
                                   command=self.cancel_processing, 
                                   bootstyle=DANGER, width=15, state="disabled")
        self.cancel_btn.pack(side="left")
        
        # Progress frame
        self.progress_frame = tb.Frame(action_frame)
        self.progress_label = tb.Label(self.progress_frame, textvariable=self.progress_message_var, font=("Arial", 10))
        self.progress_label.pack(pady=(8, 0))
        
        self.progress_bar = tb.Progressbar(self.progress_frame, length=600, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(0, 8))
    
    def create_status_section(self, parent):
        """Create status section"""
        status_label = tb.Label(parent, textvariable=self.status_var, font=('Arial', 10))
        status_label.pack(pady=(15, 0))
    
    def show_about(self):
        """Show about window"""
        about_win = tb.Toplevel()
        about_win.title("Om appen")
        about_win.geometry("600x500")
        
        # Center window
        about_win.update_idletasks()
        x = (about_win.winfo_screenwidth() // 2) - (300)
        y = (about_win.winfo_screenheight() // 2) - (250)
        about_win.geometry(f"600x500+{x}+{y}")
        
        content_frame = tb.Frame(about_win)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tb.Label(content_frame, 
                 text="Detta program ladda automatiskt ned alla jpg-bilagor som kommit från KB:s Svenska Tidningar, konverterar dem till pdf:er, "
                      "slår samma flersidia artiklar till en fil med sidantalet angivet och ger filerna begripliga namn bestående av datum för publicering och tidningsnamn.\n\n"
                      "Om så önskas kan även omdöpta jpg-filer sparas för använding av redigerare som då slipper konvertera tillbaka från pdf till jpg.\n\n"
                      "Prrogrammet är skapat av Dan Josefsson 2025.\n"
                      "Python-kodningen är gjord med hjälp av ai-motorerna Claude, Cursor och Grok.",
                 font=("Arial", 10), wraplength=550).pack(anchor="w", pady=10)
        
        tb.Button(content_frame, text="Stäng", command=about_win.destroy, bootstyle=PRIMARY).pack(side="right", pady=10)
    
    def open_manual(self):
        """Open Manual.docx with the default application"""
        manual_path = self.get_app_directory() / "Manual.docx"
        if not manual_path.exists():
            messagebox.showerror("Fel", f"Manual.docx hittades inte i programmets mapp.\nSökte i: {manual_path}")
            return
        try:
            if sys.platform.startswith('win'):
                # Use os.startfile instead of subprocess for better Windows compatibility
                import os
                os.startfile(str(manual_path))
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', str(manual_path)])
            else:
                subprocess.run(['xdg-open', str(manual_path)])
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte öppna Manual.docx: {e}")
    
    def on_gmail_toggle(self, *args):
        """Handle Gmail checkbox toggle"""
        self.update_ui_state()
        if not GMAIL_AVAILABLE and self.gmail_enabled.get():
            messagebox.showwarning("Gmail ej tillgängligt", 
                                 "Google API-biblioteken är inte installerade.\n" +
                                 "Gmail-funktionalitet är inte tillgänglig.")
            self.gmail_enabled.set(False)
    
    def on_kb_toggle(self, *args):
        """Handle KB checkbox toggle"""
        self.update_ui_state()
        if not IMAGE_PROCESSING_AVAILABLE and self.kb_enabled.get():
            messagebox.showwarning("KB-bearbetning ej tillgänglig", 
                                 "PIL eller pandas är inte installerade.\n" +
                                 "KB-funktionalitet är inte tillgänglig.")
            self.kb_enabled.set(False)
    
    def update_ui_state(self):
        """Update UI state based on enabled tools"""
        gmail_on = self.gmail_enabled.get()
        kb_on = self.kb_enabled.get()
        both_on = gmail_on and kb_on
        
        # Always show Gmail section first if enabled, then KB section
        # First, hide both sections to reset order
        self.gmail_frame.pack_forget()
        self.kb_frame.pack_forget()
        
        # Show Gmail section first if enabled
        if gmail_on:
            self.gmail_frame.pack(fill="x", pady=(0, 20))
        
        # Show KB section after Gmail if enabled
        if kb_on:
            self.kb_frame.pack(fill="x", pady=(0, 20))
        
        # Show auto-link info when both are enabled
        if both_on:
            self.kb_auto_info.pack(anchor="w", pady=(5, 0))
            # Disable KB input browsing when auto-linked and clear the field
            self.kb_input_entry.config(state="readonly")
            self.browse_kb_input_btn.config(state="disabled")
            # Clear KB input field since it will use Gmail output dir
            self.kb_input_dir_var.set("")
        else:
            self.kb_auto_info.pack_forget()
            # Enable KB input browsing when not auto-linked
            if kb_on:
                self.kb_input_entry.config(state="normal")
                self.browse_kb_input_btn.config(state="normal")
        
        # Update start button text
        if both_on:
            self.start_btn.config(text="Kör igång")
        elif gmail_on:
            self.start_btn.config(text="Starta hämtning av jpg-bilagor")
        elif kb_on:
            self.start_btn.config(text="Starta filkonvertering och omdöpning")
        else:
            self.start_btn.config(text="Välj minst ett verktyg")
            
        # Enable/disable start button
        self.start_btn.config(state="normal" if (gmail_on or kb_on) else "disabled")
    
    def load_config_to_gui(self):
        """Load saved configuration to GUI"""
        # Always start with both tools enabled, regardless of saved config
        self.gmail_enabled.set(True)
        self.kb_enabled.set(True)
        self.gmail_account_var.set(self.config.get("gmail_account", ""))
        self.credentials_file_var.set(self.config.get("credentials_file", "Ingen fil vald"))
        self.sender_var.set(self.config.get("sender_email", "noreply@kb.se"))
        self.start_date_var.set("")  # Always empty on start
        self.end_date_var.set("")    # Always empty on start
        self.gmail_output_dir_var.set(self.config.get("gmail_output_dir", str(Path.home() / "Downloads" / "Gmail-nedladdningar")))
        self.excel_path_var.set(self.config.get("excel_path", "Ingen fil vald"))
        
        # Only load KB input dir if not both tools are enabled
        if not (self.config.get("gmail_enabled", False) and self.config.get("kb_enabled", False)):
            self.kb_input_dir_var.set(self.config.get("kb_input_dir", ""))
        else:
            self.kb_input_dir_var.set("")  # Clear if both tools enabled
        
        # Set KB output dir to same as Gmail output dir by default
        default_kb_output = self.config.get("kb_output_dir", "")
        if not default_kb_output:
            default_kb_output = self.config.get("gmail_output_dir", str(Path.home() / "Downloads" / "Gmail-nedladdningar"))
        self.kb_output_dir_var.set(default_kb_output)
        # Always start with keep_renamed enabled, regardless of saved config
        self.keep_renamed_var.set(True)
        self.update_ui_state()
    
    def save_config_from_gui(self):
        """Save current GUI state to configuration"""
        self.config.update({
            "gmail_enabled": self.gmail_enabled.get(),
            "kb_enabled": self.kb_enabled.get(),
            "gmail_account": self.gmail_account_var.get(),
            "credentials_file": self.credentials_file_var.get(),
            "sender_email": self.sender_var.get(),
            "start_date": self.start_date_var.get(),
            "end_date": self.end_date_var.get(),
            "gmail_output_dir": self.gmail_output_dir_var.get(),
            "excel_path": self.excel_path_var.get(),
            "kb_input_dir": self.kb_input_dir_var.get(),
            "kb_output_dir": self.kb_output_dir_var.get(),
            "keep_renamed": self.keep_renamed_var.get()
        })
        save_config(self.config)
    
    def browse_credentials_file(self):
        """Browse for credentials file"""
        file_path = filedialog.askopenfilename(
            title="Välj Gmail API Credentials-fil",
            filetypes=[("JSON-filer", "*.json"), ("Alla filer", "*.*")],
            initialdir=Path.home() / "Downloads"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'installed' in data or 'web' in data:
                        self.credentials_file_var.set(file_path)
                        self.status_var.set("Credentials-fil vald")
                    else:
                        messagebox.showerror("Ogiltig fil", 
                                           "Den valda filen verkar inte vara en giltig Google API credentials-fil.")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte läsa filen: {str(e)}")
    
    def browse_gmail_output_dir(self):
        """Browse for Gmail output directory"""
        directory = filedialog.askdirectory(
            title="Välj mapp för Gmail-nedladdning",
            initialdir=self.gmail_output_dir_var.get()
        )
        if directory:
            self.gmail_output_dir_var.set(directory)
    
    def browse_excel_file(self):
        """Browse for Excel file and validate it"""
        file_path = filedialog.askopenfilename(
            title="Välj Excel-fil med bib-kod översättning",
            filetypes=[("Excel-filer", "*.xlsx"), ("Alla filer", "*.*")]
        )
        if file_path:
            is_valid, message = self.kb_processor.validate_excel_file(file_path)
            if is_valid:
                self.excel_path_var.set(file_path)
                self.excel_validation_label.config(text=f"✓ {message}", foreground="green")
                self.status_var.set("Excel-fil vald och validerad")
            else:
                self.excel_validation_label.config(text="", foreground="green")
                messagebox.showerror("Ogiltig Excel-fil", message)
    
    def browse_kb_input_dir(self):
        """Browse for KB input directory"""
        directory = filedialog.askdirectory(
            title="Välj mapp med KB JPG-filer"
        )
        if directory:
            self.kb_input_dir_var.set(directory)
    
    def browse_kb_output_dir(self):
        """Browse for KB output directory"""
        directory = filedialog.askdirectory(
            title="Välj mapp för PDF-utdata"
        )
        if directory:
            self.kb_output_dir_var.set(directory)
    
    def validate_settings(self):
        """Validate current settings"""
        gmail_on = self.gmail_enabled.get()
        kb_on = self.kb_enabled.get()
        
        if not gmail_on and not kb_on:
            return False, ["Du måste välja minst ett verktyg."]
        
        errors = []
        
        # Validate Gmail settings
        if gmail_on:
            if not self.gmail_account_var.get().strip():
                errors.append("Gmail-konto måste anges")
            if self.credentials_file_var.get() == "Ingen fil vald" or not self.credentials_file_var.get().strip():
                errors.append("Credentials-fil måste väljas")
            if not self.start_date_var.get().strip():
                errors.append("Startdatum måste anges")
            if self.start_date_var.get().strip() and self.start_date_validation_label.cget("text") != "✓":
                errors.append("Startdatum är ogiltigt eller inkonsekvent med slutdatum")
            if self.end_date_var.get().strip() and self.end_date_validation_label.cget("text") != "✓":
                errors.append("Slutdatum är ogiltigt eller inkonsekvent med startdatum")
            if not self.gmail_output_dir_var.get().strip():
                errors.append("Gmail nedladdningsmapp måste anges")
        
        # Validate KB settings
        if kb_on:
            if self.excel_path_var.get() == "Ingen fil vald" or not self.excel_path_var.get().strip():
                errors.append("Excel-fil måste väljas")
            
            # Check KB input directory (unless auto-linked)
            if not (gmail_on and kb_on):  # Not auto-linked
                if not self.kb_input_dir_var.get().strip():
                    errors.append("KB input-mapp måste anges")
            
            if not self.kb_output_dir_var.get().strip():
                errors.append("KB output-mapp måste anges")
        
        return len(errors) == 0, errors
    
    def update_progress(self, message: str, progress: int):
        """Update progress bar and message"""
        self.progress_message_var.set(message)
        self.progress_bar['value'] = progress
    
    def update_status(self, message: str):
        """Update status message"""
        self.status_var.set(message)
    
    def gui_update(self):
        """Update GUI"""
        self.root.update()
    
    def cancel_processing(self):
        """Cancel current processing"""
        global cancel_requested
        cancel_requested = True
        
        if self.gmail_downloader:
            self.gmail_downloader.cancel_operation()
        self.kb_processor.cancel_operation()
        
        self.status_var.set("Avbryter...")
        self.root.update()
    
    def start_processing(self):
        """Start the processing workflow"""
        # Validate settings before starting
        is_valid, errors = self.validate_settings()
        if not is_valid:
            messagebox.showerror("Valideringsfel", 
                               "Följande problem måste fixas:\n\n" + "\n".join(f"• {error}" for error in errors))
            return
        
        # Save configuration
        self.save_config_from_gui()
        
        # Setup logging
        log_file = setup_logging()
        logger.info(f"=== Startar kombinerad bearbetning - version {VERSION} ===")
        
        global cancel_requested
        cancel_requested = False
        
        # Disable controls
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        
        # Show progress
        self.progress_frame.pack(pady=(10, 0), fill="x")
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
        
        gmail_on = self.gmail_enabled.get()
        kb_on = self.kb_enabled.get()
        both_on = gmail_on and kb_on
        
        try:
            gmail_result = None
            kb_result = None
            
            # Phase 1: Gmail Download
            if gmail_on:
                self.gmail_running = True
                self.update_status("Fas 1: Gmail nedladdning...")
                logger.info("Starting Gmail download phase")
                
                # Initialize Gmail downloader
                self.gmail_downloader = GmailDownloader(
                    credentials_file=self.credentials_file_var.get(),
                    gmail_account=self.gmail_account_var.get()
                )
                self.gmail_downloader.set_root(self.root)  # Set root for dialogs
                
                # Authenticate
                self.update_progress("Autentiserar Gmail...", 5)
                self.gmail_downloader.authenticate(
                    progress_callback=self.update_progress,
                    gui_update_callback=self.gui_update
                )
                
                if cancel_requested:
                    self.cleanup_after_cancel()
                    return
                
                # Download attachments
                self.update_progress("Laddar ner bilagor...", 20)
                gmail_result = self.gmail_downloader.download_attachments(
                    sender_email=self.sender_var.get(),
                    start_date=self.start_date_var.get(),
                    end_date=self.end_date_var.get(),
                    output_dir=self.gmail_output_dir_var.get(),
                    progress_callback=self.update_progress,
                    gui_update_callback=self.gui_update
                )
                
                if gmail_result.get("cancelled"):
                    self.cleanup_after_cancel()
                    return
                
                self.gmail_running = False
                logger.info(f"Gmail download completed: {gmail_result}")

                if gmail_result.get('downloaded', 0) == 0:
                    messagebox.showinfo(
                        "Inga mejl hittades",
                        "Inga mejl med bilagor hittades i det angivna tidsspannet."
                    )
                    # Hide progress and re-enable controls, then return
                    self.progress_frame.pack_forget()
                    self.start_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
                    return

                if both_on:
                    # Auto-link: set KB input to Gmail output
                    self.kb_input_dir_var.set(gmail_result["output_path"])
                    logger.info(f"Auto-linking KB input to Gmail output: {gmail_result['output_path']}")
            
            # Phase 2: KB Processing
            if kb_on:
                self.kb_running = True
                self.update_status("Fas 2: KB filbearbetning...")
                logger.info("Starting KB processing phase")
                
                # Determine progress offset (50% if Gmail ran, 0% if KB only)
                progress_offset = 50 if gmail_on else 0
                
                def kb_progress_callback(message, progress):
                    adjusted_progress = progress_offset + (progress * (50 if gmail_on else 100) // 100)
                    self.update_progress(message, adjusted_progress)
                
                kb_result = self.kb_processor.process_files(
                    excel_path=self.excel_path_var.get(),
                    input_dir=self.kb_input_dir_var.get(),
                    output_dir=self.kb_output_dir_var.get(),
                    keep_renamed=self.keep_renamed_var.get(),
                    progress_callback=kb_progress_callback,
                    gui_update_callback=self.gui_update
                )
                
                if kb_result.get("cancelled"):
                    self.cleanup_after_cancel()
                    return
                
                self.kb_running = False
                logger.info(f"KB processing completed: {kb_result}")
            
            # Hide progress
            self.progress_frame.pack_forget()
            
            # Show results
            self.show_results(gmail_result, kb_result, both_on)
            
        except Exception as e:
            self.progress_frame.pack_forget()
            error_msg = f"Ett fel uppstod: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Fel", error_msg)
            self.status_var.set("Fel uppstod")
        
        finally:
            # Re-enable controls
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            self.gmail_running = False
            self.kb_running = False
    
    def cleanup_after_cancel(self):
        """Clean up after cancellation"""
        self.progress_frame.pack_forget()
        self.status_var.set("Avbruten")
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        logger.info("Processing cancelled by user")
    
    def show_results(self, gmail_result, kb_result, both_operations):
        """Show results dialog"""
        result_win = tb.Toplevel()
        result_win.title("Bearbetning slutförd")
        result_win.geometry("600x700")
        result_win.lift()
        result_win.focus_force()
        result_win.attributes('-topmost', True)
        result_win.after(100, lambda: result_win.attributes('-topmost', False))
        
        # Center window
        result_win.update_idletasks()
        x = (result_win.winfo_screenwidth() // 2) - (300)
        y = (result_win.winfo_screenheight() // 2) - (350)
        result_win.geometry(f"600x700+{x}+{y}")
        
        # Header
        header_frame = tb.Frame(result_win)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_text = "Bearbetning slutförd!"
        if both_operations:
            title_text = "Gmail nedladdning + KB bearbetning slutförd!"
        
        tb.Label(header_frame, text=title_text, 
                 font=("Arial", 16, "bold")).pack()
        
        # Content
        content_frame = tb.Frame(result_win)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Gmail results
        if gmail_result:
            tb.Label(content_frame, text="Gmail nedladdning:", 
                     font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
            
            gmail_text = [
                f"• Emails genomsökta: {gmail_result.get('total_emails', 0)}",
                f"• Filer nedladdade: {gmail_result.get('downloaded', 0)}",
                f"• Filer hoppade över: {gmail_result.get('skipped', 0)}",
                f"• Total storlek: {gmail_result.get('total_size', 0) / 1024 / 1024:.1f} MB" if gmail_result.get('total_size') else "• Total storlek: 0 MB",
                f"• Sparade i: {gmail_result.get('output_path', 'N/A')}"
            ]
            
            for line in gmail_text:
                tb.Label(content_frame, text=line, font=("Arial", 10)).pack(anchor="w", pady=1)
        
        # KB results
        if kb_result:
            tb.Label(content_frame, text="KB filbearbetning:", 
                     font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 5))
            
            kb_text = [
                f"• JPG-filer bearbetade: {kb_result.get('total_files', 0)}",
                f"• PDF-filer skapade: {kb_result.get('created_count', 0)}",
                f"• PDF-filer skrivna över: {kb_result.get('overwritten_count', 0)}",
                f"• Olika tidningar: {len(kb_result.get('pdfs_per_tidning', {}))}"
            ]
            
            if kb_result.get('output_path'):
                kb_text.append(f"• Sparade i: {kb_result['output_path']}")
            
            for line in kb_text:
                tb.Label(content_frame, text=line, font=("Arial", 10)).pack(anchor="w", pady=1)
            
            # Show sample newspapers
            if kb_result.get('pdfs_per_tidning'):
                pdfs_per_tidning = kb_result['pdfs_per_tidning']
                tb.Label(content_frame, text="Exempel på tidningar:", 
                         font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))
                
                sample_newspapers = list(sorted(pdfs_per_tidning.items()))[:5]
                for tidning, antal in sample_newspapers:
                    tb.Label(content_frame, 
                            text=f"  • {tidning}: {antal} PDF-fil{'er' if antal > 1 else ''}", 
                            font=("Arial", 9)).pack(anchor="w", pady=1)
                
                if len(pdfs_per_tidning) > 5:
                    tb.Label(content_frame, 
                            text=f"  ... och {len(pdfs_per_tidning) - 5} fler tidningar", 
                            font=("Arial", 9, "italic")).pack(anchor="w", pady=1)
        
        # Close button
        tb.Button(content_frame, text="Stäng", command=result_win.destroy, bootstyle=PRIMARY).pack(side="right", pady=10)

if __name__ == "__main__":
    # Test date validation if run directly
    def test_date_validation():
        """Test the date validation logic"""
        test_cases = [
            ("2024-01-15", True),   # Valid format and date
            ("20240115", True),      # Valid format (will be converted)
            ("2024-1-15", False),    # Invalid format
            ("2024-13-15", False),   # Invalid month
            ("2024-01-32", False),   # Invalid day
            ("", True),              # Empty (allowed)
            ("abc", False),          # Invalid
            ("2024", False),         # Incomplete
        ]
        
        print("Testing date validation...")
        for test_input, expected in test_cases:
            # Simulate validation logic
            if not test_input:
                result = True
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", test_input):
                # Check if it's a valid date
                try:
                    datetime.datetime.strptime(test_input, "%Y-%m-%d")
                    result = True
                except ValueError:
                    result = False
            elif re.match(r"^\d{8}$", test_input):
                # Convert and check if it's a valid date
                try:
                    normalized = f"{test_input[:4]}-{test_input[4:6]}-{test_input[6:]}"
                    datetime.datetime.strptime(normalized, "%Y-%m-%d")
                    result = True
                except ValueError:
                    result = False
            else:
                result = False
            
            status = "✓" if result == expected else "✗"
            print(f"{status} Input: '{test_input}' -> Expected: {expected}, Got: {result}")
    
    # Run test if this is the main file
    # test_date_validation()  # Temporarily commented out
    
    # Start the main application
    app = CombinedApp()
    app.root.mainloop()