# -*- coding: utf-8 -*-
"""
Gmail download manager and orchestrator
"""

import logging
import tkinter as tk
from pathlib import Path
from typing import Dict, Optional, Tuple

from .authenticator import GmailAuthenticator, AuthenticationError
from .searcher import GmailSearcher
from .processor import AttachmentProcessor
from ..security import get_secure_ops, get_default_validator

logger = logging.getLogger(__name__)

class DownloadManager:
    def __init__(self, output_dir: str):
        self.secure_ops = get_secure_ops()
        self.validator = get_default_validator()
        
        # Validate and set up output directory
        is_valid, error_msg, safe_path = self.validator.validate_directory(
            output_dir, must_exist=False, create_if_missing=True
        )
        if not is_valid:
            raise ValueError(f"Ogiltig utdata-katalog: {error_msg}")
            
        self.output_path = safe_path
        self.overwrite_all = False
        self.skip_all = False
        self.cancel_event = None
        # Track files downloaded in current session to avoid duplicates
        self.downloaded_in_session = set()
    
    def check_duplicate_in_session(self, filename: str) -> bool:
        """Check if file was already downloaded in current session"""
        return filename in self.downloaded_in_session
    
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
        dialog.geometry("600x500")
        dialog.transient(root)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        # Add periodic check for cancellation while dialog is open
        def check_cancel_during_dialog():
            if self.cancel_event and self.cancel_event.is_set():
                result.set("cancel")
                dialog.destroy()
            else:
                dialog.after(100, check_cancel_during_dialog)
        
        # Start the cancellation check
        dialog.after(100, check_cancel_during_dialog)
        
        # Center the dialog over the parent window (app window)
        dialog.update_idletasks()
        root.update_idletasks()
        
        # Get parent window position and size
        parent_x = root.winfo_x()
        parent_y = root.winfo_y()
        parent_width = root.winfo_width()
        parent_height = root.winfo_height()
        
        # Calculate position to center dialog over parent window
        dialog_width = 600
        dialog_height = 500
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Create main frame for content
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        try:
            import tkinter.ttk as ttk
            # Create canvas and scrollbar for scrolling
            canvas = tk.Canvas(main_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack scrollbar and canvas
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            
            content_frame = scrollable_frame
        except ImportError:
            # Fallback if ttk not available
            content_frame = main_frame
        
        # Message label
        tk.Label(content_frame, text=f"Filen {original_filename} finns redan.\n\nVad vill du göra?", 
                font=("Arial", 11), wraplength=550, justify="center").pack(pady=20)
        
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
        button_frame = tk.Frame(content_frame)
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
        try:
            # Use secure file operations
            output_path = self.secure_ops.save_file(
                content=file_data,
                filename=filename,
                output_dir=str(self.output_path),
                binary=True
            )
            file_size = len(file_data)
            # Add to session tracking set (use sanitized filename)
            self.downloaded_in_session.add(output_path.name)
            logger.info(f"✅ Downloaded: {output_path.name} ({self.format_file_size(file_size)})")
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
        self.cancel_requested = False  # Keep for backward compatibility
        self.cancel_event = None  # Will be set by GUI
        self.searcher = None
        self.attachment_processor = None
        self.download_manager = None
        self.root = None  # Reference to root window for dialogs
        self.secure_ops = get_secure_ops()
        self.validator = get_default_validator()
    
    def set_root(self, root: tk.Tk):
        """Set the root window for dialog purposes"""
        self.root = root
    
    def cancel_operation(self):
        self.cancel_requested = True
        if self.cancel_event:
            self.cancel_event.set()
        logger.info("Download cancellation requested")
    
    def reset_cancel_state(self):
        self.cancel_requested = False
        if self.cancel_event:
            self.cancel_event.clear()
    
    def _check_cancellation(self) -> bool:
        """Check if operation has been cancelled"""
        if self.cancel_event and self.cancel_event.is_set():
            return True
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
        
        email_details = self.attachment_processor.get_email_details(message_id, cancel_check=lambda: self._check_cancellation())
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
                logger.info(f"Download cancelled during attachment {att_num} processing")
                return downloaded, skipped, total_size
            
            if len(jpg_attachments) > 1:
                if progress_callback:
                    progress_callback(f"Email {email_num}/{total_emails} - Bilaga {att_num}/{len(jpg_attachments)}", progress)
                if gui_update_callback:
                    gui_update_callback()
            
            # Check cancellation before download
            if self._check_cancellation():
                logger.info(f"Download cancelled before attachment {att_num} download")
                return downloaded, skipped, total_size
            
            file_data = self.attachment_processor.download_attachment(message_id, attachment['attachment_id'], cancel_check=lambda: self._check_cancellation())
            if not file_data:
                # Check if it's due to cancellation
                if self._check_cancellation():
                    logger.info(f"Download cancelled during attachment {att_num} download")
                    return downloaded, skipped, total_size
                continue
            
            # Check cancellation after download but before file conflict dialog
            if self._check_cancellation():
                logger.info(f"Download cancelled after attachment {att_num} download")
                return downloaded, skipped, total_size
            
            original_filename = attachment['filename']
            
            # Check if file was already downloaded in current session - skip silently
            if self.download_manager.check_duplicate_in_session(original_filename):
                skipped += 1
                logger.info(f"🔄 Skipping duplicate from session: {original_filename}")
                continue  # Continue with next attachment
            
            final_filename = self.download_manager.handle_filename_conflict(original_filename, self.root)
            
            if final_filename is None:
                self.cancel_operation()  # Cancel the entire process if user chooses to cancel
                return downloaded, skipped, total_size
            elif final_filename == "SKIP":
                skipped += 1
                logger.info(f"Skipped file: {original_filename}")
                continue  # Continue with next attachment
            
            # Check cancellation before file save
            if self._check_cancellation():
                logger.info(f"Download cancelled before saving attachment {att_num}")
                return downloaded, skipped, total_size
            
            if self.download_manager.save_file(final_filename, file_data):
                downloaded += 1
                total_size += len(file_data)
        
        return downloaded, skipped, total_size
    
    def download_attachments(self, sender_email: str, start_date: str, end_date: str, 
                           output_dir: str, progress_callback=None, gui_update_callback=None, 
                           confirmation_callback=None) -> Dict:
        """Download JPG attachments from Gmail"""
        self.reset_cancel_state()
        
        # Use default sender if empty
        sender_email = sender_email or "noreply@kb.se"
        
        try:
            logger.info(f"🚀 Starting download process")
            logger.info(f"📧 Sender: {sender_email}")
            logger.info(f"📅 Date range: {start_date} to {end_date if end_date else 'same day'}")
            
            self.download_manager = DownloadManager(output_dir)
            self.download_manager.cancel_event = self.cancel_event
            
            if progress_callback:
                progress_callback("Bygger sökfråga...", 5)
            if gui_update_callback:
                gui_update_callback()
            
            query = self.searcher.build_search_query(sender_email, start_date, end_date)
            message_ids = self.searcher.search_emails(query, progress_callback, gui_update_callback, lambda: self._check_cancellation())
            
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
            
            # Show confirmation dialog if callback provided
            if confirmation_callback:
                logger.info(f"📋 Found {len(message_ids)} emails, asking for user confirmation")
                if progress_callback:
                    progress_callback(f"Hittade {len(message_ids)} meddelanden med bilagor", 50)
                
                # Ask for confirmation - this will be handled by the main thread
                user_confirmed = confirmation_callback(len(message_ids), sender_email)
                if not user_confirmed:
                    logger.info("User cancelled download")
                    return {
                        "total_emails": len(message_ids),
                        "downloaded": 0,
                        "skipped": 0,
                        "total_size": 0,
                        "search_query": query,
                        "output_path": output_dir,
                        "user_cancelled": True
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
                
                # Check cancellation after processing each email
                if self._check_cancellation():
                    logger.info(f"Download cancelled after processing email {i}")
                    return {"cancelled": True}
                
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