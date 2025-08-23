# -*- coding: utf-8 -*-
"""
Main GUI window for the DJs app
CRITICAL: This preserves the exact layout and behavior of the original GUI
"""

import datetime
import logging
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    import tkinter as tk
    from tkinter import scrolledtext
except ImportError:
    print("Error: ttkbootstrap not installed. Install with: pip install ttkbootstrap")
    exit(1)

from ..config import load_config, save_config
from ..gmail.downloader import GmailDownloader
from ..kb.processor import KBProcessor
from ..version import __version__ as VERSION
from ..security import get_secure_ops, get_default_validator

logger = logging.getLogger(__name__)

# Check for required dependencies
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

try:
    from PIL import Image, ImageTk
    import pandas as pd
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    print("Warning: PIL or pandas not installed. KB processing functionality will be disabled.")
    print("Install with: pip install Pillow pandas openpyxl")
    IMAGE_PROCESSING_AVAILABLE = False

class CombinedApp:
    def __init__(self):
        self.setup_gui()
        self.config = load_config()
        self.gmail_downloader = None
        self.kb_processor = KBProcessor()
        self.secure_ops = get_secure_ops()
        self.validator = get_default_validator()
        
        # Thread-safe cancellation event
        self.cancel_event = threading.Event()
        
        # Set cancel event for processors
        self.kb_processor.cancel_event = self.cancel_event
        
        self.load_config_to_gui()
    
    def get_app_directory(self):
        """Get the directory where the application is located (works for both .py and .exe)"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            return Path(sys.executable).parent
        else:
            # Running as Python script
            return Path(__file__).parent.parent.parent
    
    def setup_gui(self):
        """Setup the main GUI window"""
        self.root = tb.Window(themename="superhero")
        self.root.title("DJs app för hantering av filer från 'Svenska Tidningar'")
        
        # Set window icon
        try:
            icon_path = self.get_app_directory() / "Agg-med-smor-v4-transperent.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")
        
        # Set a more reasonable window size (reduce width and height significantly)
        window_width = 800
        window_height = 1400  # Increased by 40% from 1000 to 1400
        
        # Get screen dimensions for proper positioning
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position to center the window, but keep it towards top-left
        x = min(50, screen_width // 10)  # 50 pixels from left, but not more than 1/10 of screen width
        y = 5  # 5 pixels from top, positioned very high on screen
        
        # Set initial size without position
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.update_idletasks()
        
        # Now set final position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Force window to the front and ensure it's visible
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
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
        self.use_same_output_dir_var = tk.BooleanVar(value=True)  # Default to True
        self.delete_original_files_var = tk.BooleanVar(value=True)  # Default to True (delete)
        
        # Status
        self.status_var = tk.StringVar(value="Fyll i fälten nedan")
        
        # Progress
        self.progress_message_var = tk.StringVar(value="")
        
        # Track which operations are running
        self.gmail_running = False
        self.kb_running = False
        
        # Placeholder state tracking
        self.placeholder_text = "ÅÅÅÅ-MM-DD"
        self.start_date_has_placeholder = False
        self.end_date_has_placeholder = False
        
        # Bind checkbox events
        self.gmail_enabled.trace('w', self.on_gmail_toggle)
        self.kb_enabled.trace('w', self.on_kb_toggle)
        self.use_same_output_dir_var.trace('w', self.on_same_output_dir_toggle)
        
        # Bind field change events to update status
        self.gmail_account_var.trace('w', self.update_status_message)
        self.credentials_file_var.trace('w', self.update_status_message)
        self.start_date_var.trace('w', self.update_status_message)
        self.excel_path_var.trace('w', self.update_status_message)
        self.kb_input_dir_var.trace('w', self.update_status_message)
        self.kb_output_dir_var.trace('w', self.update_status_message)
        self.gmail_output_dir_var.trace('w', self.update_status_message)
        self.gmail_output_dir_var.trace('w', self.on_gmail_output_dir_change)
        
        # Bind input directory changes to auto-update output if same dir is selected
        self.kb_input_dir_var.trace('w', self.on_kb_input_dir_change)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with reduced padding
        main_frame = tb.Frame(self.main_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = tb.Label(main_frame, text="DJs app för hantering av filer från 'Svenska Tidningar'", 
                              font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Tool selection frame with reduced padding
        selection_frame = tb.LabelFrame(main_frame, text="Välj verktyg", padding=10)
        selection_frame.pack(fill="x", pady=(0, 10))
        
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
        # Skip validation if it's placeholder text
        if value == self.placeholder_text:
            self.update_date_validation_label("", field, True)
            return
        # Only validate if length is 10 (full date)
        if len(value) == 10:
            self.validate_date(value, field)
        else:
            self.update_date_validation_label(value, field, False)

    def create_gmail_section(self, parent):
        """Create Gmail downloader section"""
        self.gmail_frame = tb.LabelFrame(parent, text="Gmail jpg-nedladdare", padding=10)
        
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
                        self.secure_ops.safe_subprocess_run(['open'], file_arg=str(manual_path))
                    else:
                        self.secure_ops.safe_subprocess_run(['xdg-open'], file_arg=str(manual_path))
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte öppna Manual.docx: {e}")
            else:
                messagebox.showerror("Fel", f"Manual.docx hittades inte i programmets mapp.\nSökte i: {manual_path}")
        help_label.bind("<Button-1>", open_manual_event)
        
        creds_path_frame = tb.Frame(creds_frame)
        creds_path_frame.pack(fill="x")
        
        creds_entry = tb.Entry(creds_path_frame, textvariable=self.credentials_file_var, 
                              font=('Arial', 10))
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
        self.start_date_entry = start_date_entry  # Store reference for placeholder functionality
        self.start_date_validation_label = tb.Label(start_date_frame, text="", font=('Arial', 10))
        self.start_date_validation_label.pack(side="left", padx=(5, 0))
        start_date_entry.bind('<KeyRelease>', lambda e: self.full_date_validation('start'))
        start_date_entry.bind('<FocusOut>', lambda e: self.on_start_date_focus_out(e))
        start_date_entry.bind('<FocusIn>', lambda e: self.on_start_date_focus_in(e))
        
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
        self.end_date_entry = end_date_entry  # Store reference for placeholder functionality
        self.end_date_validation_label = tb.Label(end_date_frame, text="", font=('Arial', 10))
        self.end_date_validation_label.pack(side="left", padx=(5, 0))
        end_date_entry.bind('<KeyRelease>', lambda e: self.full_date_validation('end'))
        end_date_entry.bind('<FocusOut>', lambda e: self.on_end_date_focus_out(e))
        end_date_entry.bind('<FocusIn>', lambda e: self.on_end_date_focus_in(e))
        
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
        # Allow empty input or placeholder text
        if not input_str or input_str == self.placeholder_text:
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

        # Clear if empty or placeholder
        if not input_str or input_str == self.placeholder_text:
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

        # If either field is empty or contains placeholder text, just show format validation
        if (not start_date or start_date == self.placeholder_text or 
            not end_date or end_date == self.placeholder_text):
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
    
    def on_start_date_focus_in(self, event):
        """Handle start date field focus in - remove placeholder if present"""
        if self.start_date_has_placeholder:
            self.start_date_var.set("")
            self.start_date_entry.config(foreground="white")
            self.start_date_has_placeholder = False
    
    def on_start_date_focus_out(self, event):
        """Handle start date field focus out - add placeholder if empty, run validation"""
        current_value = self.start_date_var.get().strip()
        if not current_value:
            self.start_date_var.set(self.placeholder_text)
            self.start_date_entry.config(foreground="gray")
            self.start_date_has_placeholder = True
        else:
            self.start_date_has_placeholder = False
        
        # Run the original validation logic
        self.full_date_validation('start')
    
    def on_end_date_focus_in(self, event):
        """Handle end date field focus in - remove placeholder if present"""
        if self.end_date_has_placeholder:
            self.end_date_var.set("")
            self.end_date_entry.config(foreground="white")
            self.end_date_has_placeholder = False
    
    def on_end_date_focus_out(self, event):
        """Handle end date field focus out - add placeholder if empty, run validation"""
        current_value = self.end_date_var.get().strip()
        if not current_value:
            self.end_date_var.set(self.placeholder_text)
            self.end_date_entry.config(foreground="gray")
            self.end_date_has_placeholder = True
        else:
            self.end_date_has_placeholder = False
        
        # Run the original validation logic
        self.full_date_validation('end')
    
    def create_kb_section(self, parent):
        """Create KB processor section"""
        self.kb_frame = tb.LabelFrame(parent, text="Bearbetning av jpg-filer från KB", padding=10)
        
        # Excel file (moved to top for logical workflow)
        excel_frame = tb.Frame(self.kb_frame)
        excel_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(excel_frame, text="Excel-fil med bib-koder översatta till tidningsnamn:", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        excel_path_frame = tb.Frame(excel_frame)
        excel_path_frame.pack(fill="x")
        
        excel_entry = tb.Entry(excel_path_frame, textvariable=self.excel_path_var, 
                              font=('Arial', 10))
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
                                    text="📁 Om båda verktygen körs så används automatiskt nedladdningsmappen.",
                                    font=('Arial', 9), foreground="lightgreen")
        
        # Delete original files option
        delete_files_frame = tb.Frame(self.kb_frame)
        delete_files_frame.pack(fill="x", pady=(10, 15))
        
        # Create a frame for the checkbox, text and help button
        delete_checkbox_frame = tb.Frame(delete_files_frame)
        delete_checkbox_frame.pack(anchor="w")
        
        # Create the checkbox with text
        tb.Checkbutton(delete_checkbox_frame, text="Radera bib-filerna efter omdöpning?", 
                      variable=self.delete_original_files_var, 
                      bootstyle="info-round-toggle").pack(side="left")
        
        # Create help button with question mark
        delete_help_btn = tb.Button(delete_checkbox_frame, text="?", width=3, 
                                   command=self.show_delete_files_help,
                                   bootstyle="info-outline")
        delete_help_btn.pack(side="left", padx=(10, 0))
        
        # Output directory
        kb_output_frame = tb.Frame(self.kb_frame)
        kb_output_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(kb_output_frame, text="Var ska pdf:erna sparas?", font=('Arial', 10)).pack(anchor="w", pady=(0, 5))
        
        # Same directory switch
        same_dir_frame = tb.Frame(kb_output_frame)
        same_dir_frame.pack(fill="x", pady=(0, 10))
        
        self.same_dir_check = tb.Checkbutton(same_dir_frame, text="Använd mappen där jpg-filerna finns", 
                                           variable=self.use_same_output_dir_var, 
                                           bootstyle="info-round-toggle")
        self.same_dir_check.pack(anchor="w")
        
        kb_output_path_frame = tb.Frame(kb_output_frame)
        kb_output_path_frame.pack(fill="x")
        
        self.kb_output_entry = tb.Entry(kb_output_path_frame, textvariable=self.kb_output_dir_var, 
                                       font=('Arial', 10))
        self.kb_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.browse_kb_output_btn = tb.Button(kb_output_path_frame, text="Bläddra...", 
                                             command=self.browse_kb_output_dir, 
                                             bootstyle=INFO, width=12)
        self.browse_kb_output_btn.pack(side="right")
        
        # Keep renamed files checkbox (moved under output directory)
        keep_frame = tb.Frame(self.kb_frame)
        keep_frame.pack(fill="x", pady=(0, 10))
        
        # Create a frame for the checkbox, text and help button
        checkbox_frame = tb.Frame(keep_frame)
        checkbox_frame.pack(anchor="w")
        
        # Create the checkbox with text
        tb.Checkbutton(checkbox_frame, text="Spara omdöpta jpg-filer i en underkatalog?", 
                      variable=self.keep_renamed_var, 
                      bootstyle="info-round-toggle").pack(side="left")
        
        # Create help button with question mark
        help_btn = tb.Button(checkbox_frame, text="?", width=3, 
                            command=self.show_keep_renamed_help,
                            bootstyle="info-outline")
        help_btn.pack(side="left", padx=(10, 0))
    
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
        self.progress_label = tb.Label(self.progress_frame, textvariable=self.progress_message_var, 
                                      font=("Arial", 10), wraplength=550, justify="left")
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
                      "Python-kodningen är gjord med hjälp av ai-motorerna Cursor och framför allt Claude Code.",
                 font=("Arial", 10), wraplength=550).pack(anchor="w", pady=10)
        
        tb.Button(content_frame, text="Stäng", command=about_win.destroy, bootstyle=PRIMARY).pack(side="right", pady=10)
    
    def show_keep_renamed_help(self):
        """Show help dialog for keep renamed files option"""
        help_win = tb.Toplevel()
        help_win.title("Hjälp - Spara omdöpta jpg-filer")
        help_win.geometry("500x485")  # Increased height by 62% total (300 -> 485)
        
        # Center window
        help_win.update_idletasks()
        x = (help_win.winfo_screenwidth() // 2) - (250)
        y = (help_win.winfo_screenheight() // 2) - (242)  # Adjusted for new height
        help_win.geometry(f"500x485+{x}+{y}")
        
        # Create main frame for content
        main_frame = tb.Frame(help_win)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        try:
            import tkinter.ttk as ttk
            # Create canvas and scrollbar for scrolling
            canvas = tk.Canvas(main_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tb.Frame(canvas)
            
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
        
        tb.Label(content_frame, 
                 text="Under behandlingen av jpg-filerna skapar programmet tillfälligt omdöpta filer med begripliga namn.\n\n"
                      "Om denna ruta är ikryssad sparas de omdöpta jpg-filerna i en underkatalog som heter 'Jpg-filer med fina namn'.\n\n"
                      "Detta är användbart för redigerare som vill ha tillgång till jpg-filerna med begripliga namn utan att behöva "
                      "konvertera tillbaka från PDF-format.\n\n"
                      "Om rutan inte är ikryssad raderas de omdöpta jpg-filerna efter att PDF-filerna har skapats.",
                 font=("Arial", 10), wraplength=430, justify="left").pack(anchor="w", pady=10)
        
        tb.Button(content_frame, text="Stäng", command=help_win.destroy, bootstyle=PRIMARY).pack(side="right", pady=10)
    
    def show_delete_files_help(self):
        """Show help dialog for delete original files option"""
        help_win = tb.Toplevel()
        help_win.title("Hjälp - Radera bib-filerna")
        help_win.geometry("500x405")  # Increased height by 62% total (250 -> 405)
        
        # Center window
        help_win.update_idletasks()
        x = (help_win.winfo_screenwidth() // 2) - (250)
        y = (help_win.winfo_screenheight() // 2) - (202)  # Adjusted for new height
        help_win.geometry(f"500x405+{x}+{y}")
        
        # Create main frame for content
        main_frame = tb.Frame(help_win)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        try:
            import tkinter.ttk as ttk
            # Create canvas and scrollbar for scrolling
            canvas = tk.Canvas(main_frame, highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tb.Frame(canvas)
            
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
        
        tb.Label(content_frame, 
                 text="Appen kopierar och döper om jpg-filerna från KB, som har obegripliga namn.\n\n"
                      "Originalfilerna raderas som standard för att spara diskutrymme och undvika förvirring.\n\n"
                      "Om du av någon anledning vill ha kvar originalfilerna med deras obegripliga namn "
                      "så kan du slå av den här brytaren.\n\n"
                      "Observera att detta kan leda till dubbelt så många filer i mappen.",
                 font=("Arial", 10), wraplength=430, justify="left").pack(anchor="w", pady=10)
        
        tb.Button(content_frame, text="Stäng", command=help_win.destroy, bootstyle=PRIMARY).pack(side="right", pady=10)
    
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
                self.secure_ops.safe_subprocess_run(['open'], file_arg=str(manual_path))
            else:
                self.secure_ops.safe_subprocess_run(['xdg-open'], file_arg=str(manual_path))
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
    
    def on_same_output_dir_toggle(self, *args):
        """Handle same output directory checkbox toggle"""
        self.update_kb_output_ui_state()
        if self.use_same_output_dir_var.get():
            # Auto-set output dir to input dir
            self.kb_output_dir_var.set(self.kb_input_dir_var.get())
    
    def on_gmail_output_dir_change(self, *args):
        """Handle Gmail output directory change - update KB input if auto-linked"""
        gmail_on = self.gmail_enabled.get()
        kb_on = self.kb_enabled.get()
        both_on = gmail_on and kb_on
        
        if both_on:
            # Update KB input field with Gmail output path
            gmail_output = self.gmail_output_dir_var.get()
            if gmail_output:
                self.kb_input_dir_var.set(gmail_output)
    
    def on_kb_input_dir_change(self, *args):
        """Handle KB input directory change"""
        if self.use_same_output_dir_var.get():
            # Auto-update output dir when input dir changes
            self.update_kb_output_ui_state()
    
    def update_kb_output_ui_state(self):
        """Update KB output directory UI state based on same directory setting"""
        if self.use_same_output_dir_var.get():
            # Disable manual output directory selection and show input path
            self.kb_output_entry.config(state="readonly", foreground="gray")
            self.browse_kb_output_btn.config(state="disabled")
            # Show input directory path in output field
            input_path = self.kb_input_dir_var.get()
            if input_path and input_path != "(Använder nedladdningsmapp från Gmail)":
                self.kb_output_dir_var.set(input_path)
            else:
                self.kb_output_dir_var.set("(Samma som jpg-filernas mapp)")
        else:
            # Enable manual output directory selection
            self.kb_output_entry.config(state="normal", foreground="white")
            self.browse_kb_output_btn.config(state="normal")
    
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
            self.gmail_frame.pack(fill="x", pady=(0, 10))
        
        # Show KB section after Gmail if enabled
        if kb_on:
            self.kb_frame.pack(fill="x", pady=(0, 10))
        
        # Show auto-link info when both are enabled
        if both_on:
            self.kb_auto_info.pack(anchor="w", pady=(5, 0))
            # Disable KB input browsing when auto-linked
            self.kb_input_entry.config(state="readonly", foreground="gray")
            self.browse_kb_input_btn.config(state="disabled")
            # Show Gmail output dir in KB input field (auto-linked)
            gmail_output = self.gmail_output_dir_var.get()
            if gmail_output:
                self.kb_input_dir_var.set(gmail_output)
            else:
                self.kb_input_dir_var.set("(Använder nedladdningsmapp från Gmail)")
        else:
            self.kb_auto_info.pack_forget()
            # Enable KB input browsing when not auto-linked
            if kb_on:
                self.kb_input_entry.config(state="normal", foreground="white")
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
        
        # Update status message
        self.update_status_message()
        
        # Update KB output directory UI state
        self.update_kb_output_ui_state()
    
    def load_config_to_gui(self):
        """Load saved configuration to GUI"""
        # Always start with both tools enabled, regardless of saved config
        self.gmail_enabled.set(True)
        self.kb_enabled.set(True)
        self.gmail_account_var.set(self.config.get("gmail_account", ""))
        self.credentials_file_var.set(self.config.get("credentials_file", "Ingen fil vald"))
        self.sender_var.set(self.config.get("sender_email", "noreply@kb.se"))
        # Set initial placeholders for date fields
        self.start_date_var.set(self.placeholder_text)
        self.end_date_var.set(self.placeholder_text)
        self.start_date_has_placeholder = True
        self.end_date_has_placeholder = True
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
        
        # Load use_same_output_dir setting (default True)
        self.use_same_output_dir_var.set(self.config.get("use_same_output_dir", True))
        
        # Always start with delete_original_files enabled (don't save this setting)
        self.delete_original_files_var.set(True)
        
        self.update_ui_state()
        
        # Set initial placeholder appearance after UI is created
        self.root.after(10, self._apply_initial_placeholder_styling)
    
    def _apply_initial_placeholder_styling(self):
        """Apply initial gray styling to placeholder text"""
        if self.start_date_has_placeholder:
            self.start_date_entry.config(foreground="gray")
        if self.end_date_has_placeholder:
            self.end_date_entry.config(foreground="gray")
    
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
            "keep_renamed": self.keep_renamed_var.get(),
            "use_same_output_dir": self.use_same_output_dir_var.get()
            # Note: delete_original_files is not saved - always defaults to True at startup
        })
        save_config(self.config)
    
    def browse_credentials_file(self):
        """Browse for credentials file"""
        file_path = filedialog.askopenfilename(
            title="Välj Gmail API Credentials-fil",
            filetypes=[("JSON-filer", "*.json"), ("Alla filer", "*.*")],
            initialdir=self.get_app_directory()
        )
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'installed' in data or 'web' in data:
                        self.credentials_file_var.set(file_path)
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
            filetypes=[("Excel-filer", "*.xlsx"), ("Alla filer", "*.*")],
            initialdir=self.get_app_directory()
        )
        if file_path:
            is_valid, message = self.kb_processor.validate_excel_file(file_path)
            if is_valid:
                self.excel_path_var.set(file_path)
                self.excel_validation_label.config(text=f"✓ {message}", foreground="green")
            else:
                self.excel_validation_label.config(text="", foreground="green")
                messagebox.showerror("Ogiltig Excel-fil", message)
    
    def browse_kb_input_dir(self):
        """Browse for KB input directory"""
        directory = filedialog.askdirectory(
            title="Välj mapp med KB JPG-filer",
            initialdir=self.get_app_directory()
        )
        if directory:
            self.kb_input_dir_var.set(directory)
    
    def browse_kb_output_dir(self):
        """Browse for KB output directory"""
        directory = filedialog.askdirectory(
            title="Välj mapp för PDF-utdata",
            initialdir=self.get_app_directory()
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
            start_date_value = self.start_date_var.get().strip()
            if not start_date_value or start_date_value == self.placeholder_text:
                errors.append("Startdatum måste anges")
            if (start_date_value and start_date_value != self.placeholder_text and 
                self.start_date_validation_label.cget("text") != "✓"):
                errors.append("Startdatum är ogiltigt eller inkonsekvent med slutdatum")
            end_date_value = self.end_date_var.get().strip()
            if (end_date_value and end_date_value != self.placeholder_text and 
                self.end_date_validation_label.cget("text") != "✓"):
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
            
            # Check KB output directory (unless using same directory)
            if not self.use_same_output_dir_var.get():
                if not self.kb_output_dir_var.get().strip():
                    errors.append("KB output-mapp måste anges")
        
        return len(errors) == 0, errors
    
    def update_progress(self, message: str, progress: int):
        """Update progress bar and message - thread-safe"""
        try:
            # Schedule GUI update on main thread
            self.root.after(0, self._update_progress_safe, message, progress)
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def _update_progress_safe(self, message: str, progress: int):
        """Internal method to safely update progress from main thread"""
        try:
            self.progress_message_var.set(message)
            self.progress_bar['value'] = progress
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def update_status(self, message: str):
        """Update status message - thread-safe"""
        try:
            # Schedule GUI update on main thread
            self.root.after(0, self._update_status_safe, message)
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def _update_status_safe(self, message: str):
        """Internal method to safely update status from main thread"""
        try:
            self.status_var.set(message)
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def update_status_message(self, *args):
        """Update status message based on form completion"""
        if self.gmail_running or self.kb_running:
            return  # Don't update during processing
        
        gmail_on = self.gmail_enabled.get()
        kb_on = self.kb_enabled.get()
        
        if not gmail_on and not kb_on:
            self.status_var.set("Välj minst ett verktyg")
            return
        
        # Check if required fields are filled
        fields_complete = True
        
        if gmail_on:
            start_date_value = self.start_date_var.get().strip()
            if (not self.gmail_account_var.get().strip() or 
                self.credentials_file_var.get() in ["Ingen fil vald", ""] or
                not start_date_value or start_date_value == self.placeholder_text or
                not self.gmail_output_dir_var.get().strip()):
                fields_complete = False
        
        if kb_on:
            if self.excel_path_var.get() in ["Ingen fil vald", ""]:
                fields_complete = False
            
            # Check KB input directory (unless auto-linked)
            if not (gmail_on and kb_on):  # Not auto-linked
                if not self.kb_input_dir_var.get().strip():
                    fields_complete = False
            
            # Check KB output directory (unless using same directory)
            if not self.use_same_output_dir_var.get():
                if not self.kb_output_dir_var.get().strip():
                    fields_complete = False
        
        if fields_complete:
            self.status_var.set("Redo att börja")
        else:
            self.status_var.set("Fyll i fälten nedan")
    
    def gui_update(self):
        """Update GUI - thread-safe version"""
        try:
            # Schedule GUI update on main thread
            self.root.after(0, self._gui_update_safe)
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def _gui_update_safe(self):
        """Internal method to safely update GUI from main thread"""
        try:
            self.root.update_idletasks()
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def clear_progress_text(self):
        """Clear progress text completely using a more robust method"""
        try:
            # Method 1: Set to a unique placeholder then clear
            placeholder = "█" * 50  # Use a unique string that's unlikely to match existing text
            self.progress_message_var.set(placeholder)
            self.progress_label.update()
            self.progress_message_var.set("")
            self.progress_label.update()
            
            # Method 2: Force widget reconfiguration
            self.progress_label.config(text="")
            self.progress_label.update()
            
            # Method 3: Temporarily hide and show the label to force refresh
            self.progress_label.pack_forget()
            self.progress_label.pack(pady=(8, 0))
            self.progress_label.update()
        except tk.TclError:
            # GUI might have been destroyed
            pass
    
    def cancel_processing(self):
        """Cancel current processing"""
        self.cancel_event.set()
        
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
        
        # Clear any previous cancel request
        self.cancel_event.clear()
        
        # Disable controls
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        
        # Show progress
        self.progress_frame.pack(pady=(10, 0), fill="x")
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
        
        # Clear any previous progress text completely
        self.clear_progress_text()
        
        # Start processing in background thread
        self.processing_thread = threading.Thread(target=self.run_processing_workflow, daemon=True)
        self.processing_thread.start()
    
    def run_processing_workflow(self):
        """Run the actual processing workflow in background thread"""
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
                
                # Set cancel event for Gmail downloader
                self.gmail_downloader.cancel_event = self.cancel_event
                
                # Authenticate
                self.update_progress("Autentiserar Gmail...", 5)
                self.gmail_downloader.authenticate(
                    progress_callback=self.update_progress,
                    gui_update_callback=self.gui_update
                )
                
                if self.cancel_event.is_set():
                    self.cleanup_after_cancel()
                    return
                
                # Download attachments
                self.update_progress("Laddar ner bilagor...", 20)
                # Convert placeholder text to empty string for processing
                start_date = self.start_date_var.get()
                end_date = self.end_date_var.get()
                if start_date == self.placeholder_text:
                    start_date = ""
                if end_date == self.placeholder_text:
                    end_date = ""
                    
                gmail_result = self.gmail_downloader.download_attachments(
                    sender_email=self.sender_var.get(),
                    start_date=start_date,
                    end_date=end_date,
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
                    # Schedule no emails found handling on main thread
                    self.root.after(0, self._handle_no_emails_found)
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
                
                # Set root for KB processor dialogs
                self.kb_processor.set_root(self.root)
                
                # Determine progress offset (50% if Gmail ran, 0% if KB only)
                progress_offset = 50 if gmail_on else 0
                
                def kb_progress_callback(message, progress):
                    adjusted_progress = progress_offset + (progress * (50 if gmail_on else 100) // 100)
                    self.update_progress(message, adjusted_progress)
                
                # Determine output directory
                output_dir = self.kb_output_dir_var.get()
                if self.use_same_output_dir_var.get():
                    output_dir = self.kb_input_dir_var.get()

                kb_result = self.kb_processor.process_files(
                    excel_path=self.excel_path_var.get(),
                    input_dir=self.kb_input_dir_var.get(),
                    output_dir=output_dir,
                    keep_renamed=self.keep_renamed_var.get(),
                    delete_originals=self.delete_original_files_var.get(),
                    progress_callback=kb_progress_callback,
                    gui_update_callback=self.gui_update
                )
                
                if kb_result.get("cancelled"):
                    self.cleanup_after_cancel()
                    return
                
                self.kb_running = False
                logger.info(f"KB processing completed: {kb_result}")
            
            # Schedule final GUI updates on main thread
            self.root.after(0, self._finalize_processing_success, gmail_result, kb_result, both_on)
            
        except Exception as e:
            error_msg = f"Ett fel uppstod: {str(e)}"
            logger.error(error_msg)
            # Schedule error handling on main thread
            self.root.after(0, self._finalize_processing_error, error_msg)
    
    def _finalize_processing_success(self, gmail_result, kb_result, both_on):
        """Finalize successful processing on main thread"""
        try:
            # Hide progress
            self.clear_progress_text()
            self.progress_frame.pack_forget()
            
            # Update status to show completion
            self.update_status("Färdig")
            
            # Re-enable controls
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            self.gmail_running = False
            self.kb_running = False
            
            # Show results
            self.show_results(gmail_result, kb_result, both_on)
        except Exception as e:
            logger.error(f"Error in finalize_processing_success: {e}")
    
    def _finalize_processing_error(self, error_msg):
        """Finalize error processing on main thread"""
        try:
            # Clear progress text before hiding
            self.clear_progress_text()
            self.progress_frame.pack_forget()
            
            # Show error message
            messagebox.showerror("Fel", error_msg)
            
            # Update status and re-enable controls
            self.gmail_running = False
            self.kb_running = False
            self.update_status("Fel uppstod")
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
        except Exception as e:
            logger.error(f"Error in finalize_processing_error: {e}")
    
    def cleanup_after_cancel(self):
        """Clean up after cancellation - thread-safe"""
        logger.info("Processing cancelled by user")
        # Schedule cleanup on main thread
        self.root.after(0, self._cleanup_after_cancel_safe)
    
    def _cleanup_after_cancel_safe(self):
        """Internal method to safely cleanup after cancellation from main thread"""
        try:
            # Clear progress text before hiding
            self.clear_progress_text()
            self.progress_frame.pack_forget()
            self.gmail_running = False
            self.kb_running = False
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            self.update_status("Avbruten")
        except Exception as e:
            logger.error(f"Error in cleanup_after_cancel_safe: {e}")
    
    def _handle_no_emails_found(self):
        """Handle no emails found scenario on main thread"""
        try:
            messagebox.showinfo(
                "Inga mejl hittades",
                "Inga mejl med bilagor hittades i det angivna tidsspannet."
            )
            # Hide progress and re-enable controls
            self.progress_frame.pack_forget()
            self.start_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            self.gmail_running = False
            self.kb_running = False
            self.update_status("Inga mejl hittades")
        except Exception as e:
            logger.error(f"Error in handle_no_emails_found: {e}")
    
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
                f"• Dublettfiler som hoppats över: {gmail_result.get('skipped', 0)}",
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
            
            # Show unknown bib codes information
            if kb_result.get('unknown_bib_count', 0) > 0:
                tb.Label(content_frame, text="Okända bib-koder:", 
                         font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 5))
                
                unknown_count = kb_result['unknown_bib_count']
                tb.Label(content_frame, 
                        text=f"• {unknown_count} filer innehöll bib-koder som saknades i Excel-dokumentet", 
                        font=("Arial", 9)).pack(anchor="w", pady=1)
                
                tb.Label(content_frame, 
                        text="• Dessa PDF-filer är märkta med tidningsnamnet 'OKÄND'", 
                        font=("Arial", 9)).pack(anchor="w", pady=1)
                
                tb.Label(content_frame, 
                        text="• Den okända bib-koden bevaras i filnamnet", 
                        font=("Arial", 9)).pack(anchor="w", pady=1)
                
                tb.Label(content_frame, 
                        text="Tips: Öppna filerna, kolla tidningsnamnen och uppdatera Excel-dokumentet med de nya bib-koderna", 
                        font=("Arial", 9), foreground="yellow", wraplength=550).pack(anchor="w", pady=(5, 0))
        
        # Close button
        tb.Button(content_frame, text="Stäng", command=result_win.destroy, bootstyle=PRIMARY).pack(side="right", pady=10)