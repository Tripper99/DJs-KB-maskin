#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swedish update dialog with security warnings
Provides user interface for update notifications and browser launching
"""

import logging
import webbrowser
import sys
from pathlib import Path
from tkinter import messagebox
from typing import Optional

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import (
        X, BOTH, LEFT, RIGHT
    )
    import tkinter as tk
    try:
        from ttkbootstrap.tooltip import ToolTip
        TOOLTIP_AVAILABLE = True
    except ImportError:
        TOOLTIP_AVAILABLE = False
        ToolTip = None
except ImportError:
    print("Error: ttkbootstrap not installed. Install with: pip install ttkbootstrap")
    exit(1)

from .models import UpdateInfo, UpdateCheckResult

logger = logging.getLogger(__name__)

# Swedish UI text constants
DIALOG_TEXT = {
    'title_update_available': 'Uppdatering tillgänglig',
    'title_no_updates': 'Inga uppdateringar',
    'title_error': 'Fel vid uppdateringskontroll',
    'current_version': 'Aktuell version:',
    'new_version': 'Ny version:',
    'published': 'Publicerad:',
    'available_files': 'Tillgängliga filer:',
    'release_notes': 'Versionsanteckningar:',
    'security_warning': '⚠️ Säkerhetsvarning',
    'security_message': 'Du kommer att omdirigeras till GitHub i din webbläsare för att ladda ner uppdateringen. Kontrollera alltid att URL:en är från den officiella källa innan du laddar ner.',
    'download_update': 'Ladda ner uppdatering',
    'skip_version': 'Hoppa över denna version',
    'close': 'Stäng',
    'cancel': 'Avbryt',
    'no_updates_message': 'Du använder redan den senaste versionen av applikationen.',
    'check_error_message': 'Ett fel uppstod vid kontroll av uppdateringar:',
    'opening_browser': 'Öppnar GitHub i webbläsaren...',
    'browser_error': 'Kunde inte öppna webbläsaren. Besök GitHub manuellt:',
    'version_skipped': 'Version {} hoppades över. Du kommer inte att få påminnelser om denna version igen.',
    'tooltip_download': 'Öppnar GitHub-sidan i webbläsaren för att ladda ner uppdateringen',
    'tooltip_skip': 'Hoppar över denna version och visar inte påminnelser igen',
    'tooltip_close': 'Stänger dialogen utan att göra något'
}


class UpdateDialog:
    """Swedish dialog for update notifications with security features"""
    
    def __init__(self, parent_window):
        """
        Initialize update dialog
        
        Args:
            parent_window: Parent tkinter window
        """
        self.parent = parent_window
        self.result = None
        self.dialog = None
        self.update_info = None
        
    def show_update_available(self, update_info: UpdateInfo) -> str:
        """
        Show dialog for available update
        
        Args:
            update_info: Information about available update
            
        Returns:
            User action: 'download', 'skip', or 'cancel'
        """
        self.update_info = update_info
        self.result = 'cancel'  # Default result
        
        try:
            self._create_update_dialog()
            self._show_modal_dialog()
            return self.result
            
        except Exception as e:
            logger.error(f"Error showing update dialog: {e}")
            messagebox.showerror(
                DIALOG_TEXT['title_error'],
                f"{DIALOG_TEXT['check_error_message']}\n{str(e)}"
            )
            return 'cancel'
            
    def show_no_updates_dialog(self) -> None:
        """Show dialog indicating no updates are available"""
        try:
            messagebox.showinfo(
                DIALOG_TEXT['title_no_updates'],
                DIALOG_TEXT['no_updates_message']
            )
        except Exception as e:
            logger.error(f"Error showing no updates dialog: {e}")
            
    def show_check_error_dialog(self, error_message: str) -> None:
        """Show dialog for update check error"""
        try:
            messagebox.showerror(
                DIALOG_TEXT['title_error'],
                f"{DIALOG_TEXT['check_error_message']}\n\n{error_message}"
            )
        except Exception as e:
            logger.error(f"Error showing error dialog: {e}")
            
    def _create_update_dialog(self):
        """Create the main update dialog window"""
        # Create dialog window
        self.dialog = tb.Toplevel(self.parent)
        self.dialog.title(DIALOG_TEXT['title_update_available'])
        self.dialog.geometry("600x900")
        self.dialog.resizable(True, True)
        self.dialog.minsize(550, 850)
        
        # Set icon on dialog
        self._set_window_icon(self.dialog)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog relative to parent
        self._center_dialog()
        
        # Create main content frame
        main_frame = tb.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create content sections
        self._create_version_info(main_frame)
        self._create_files_section(main_frame)
        self._create_release_notes(main_frame)
        self._create_security_warning(main_frame)
        self._create_buttons(main_frame)
        
        # Handle window close button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _create_version_info(self, parent):
        """Create version information section"""
        version_frame = tb.LabelFrame(parent, text="Versionsinformation", padding=10)
        version_frame.pack(fill=X, pady=(0, 10))
        
        # Current version
        current_frame = tb.Frame(version_frame)
        current_frame.pack(fill=X, pady=2)
        
        tb.Label(current_frame, text=DIALOG_TEXT['current_version'], 
                font=("TkDefaultFont", 9, "bold")).pack(side=LEFT)
        tb.Label(current_frame, text=self.update_info.current_version,
                font=("TkDefaultFont", 9)).pack(side=LEFT, padx=(10, 0))
        
        # New version
        new_frame = tb.Frame(version_frame)
        new_frame.pack(fill=X, pady=2)
        
        tb.Label(new_frame, text=DIALOG_TEXT['new_version'],
                font=("TkDefaultFont", 9, "bold")).pack(side=LEFT)
        tb.Label(new_frame, text=self.update_info.latest_version,
                font=("TkDefaultFont", 9), bootstyle="success").pack(side=LEFT, padx=(10, 0))
        
        # Published date
        if self.update_info.formatted_date:
            date_frame = tb.Frame(version_frame)
            date_frame.pack(fill=X, pady=2)
            
            tb.Label(date_frame, text=DIALOG_TEXT['published'],
                    font=("TkDefaultFont", 9, "bold")).pack(side=LEFT)
            tb.Label(date_frame, text=self.update_info.formatted_date,
                    font=("TkDefaultFont", 9)).pack(side=LEFT, padx=(10, 0))
        
    def _create_files_section(self, parent):
        """Create available files section"""
        if self.update_info.assets.total_files > 0:
            files_frame = tb.LabelFrame(parent, text=DIALOG_TEXT['available_files'], padding=10)
            files_frame.pack(fill=X, pady=(0, 10))
            
            # Create scrollable text widget for file list
            files_text = tk.Text(files_frame, height=4, wrap=tk.WORD, 
                               font=("Consolas", 9))
            files_text.pack(fill=BOTH, expand=True)
            
            # Insert file information
            file_summary = self.update_info.get_file_summary()
            files_text.insert('1.0', file_summary)
            files_text.config(state='disabled')  # Make read-only
            
    def _create_release_notes(self, parent):
        """Create release notes section"""
        if self.update_info.release_notes.strip():
            notes_frame = tb.LabelFrame(parent, text=DIALOG_TEXT['release_notes'], padding=10)
            notes_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
            
            # Create scrollable text widget
            notes_text = tk.Text(
                notes_frame, 
                height=6, 
                wrap=tk.WORD,
                font=("TkDefaultFont", 9)
            )
            notes_text.pack(fill=BOTH, expand=True)
            
            # Insert release notes
            notes_text.insert('1.0', self.update_info.short_release_notes)
            notes_text.config(state='disabled')  # Make read-only
            
    def _create_security_warning(self, parent):
        """Create security warning section"""
        warning_frame = tb.LabelFrame(parent, text=DIALOG_TEXT['security_warning'], 
                                     padding=10, bootstyle="warning")
        warning_frame.pack(fill=X, pady=(0, 15))
        
        warning_label = tb.Label(
            warning_frame,
            text=DIALOG_TEXT['security_message'],
            wraplength=550,
            justify=LEFT,
            font=("TkDefaultFont", 8)
        )
        warning_label.pack(fill=X)
        
    def _create_buttons(self, parent):
        """Create action buttons"""
        button_frame = tb.Frame(parent)
        button_frame.pack(fill=X, pady=(10, 0))
        
        # Download button (primary action)
        download_btn = tb.Button(
            button_frame,
            text=DIALOG_TEXT['download_update'],
            command=self._on_download,
            bootstyle="success",
            width=20
        )
        download_btn.pack(side=LEFT, padx=(0, 10))
        
        # Skip version button
        skip_btn = tb.Button(
            button_frame,
            text=DIALOG_TEXT['skip_version'],
            command=self._on_skip,
            bootstyle="secondary",
            width=20
        )
        skip_btn.pack(side=LEFT, padx=(0, 10))
        
        # Cancel/Close button
        cancel_btn = tb.Button(
            button_frame,
            text=DIALOG_TEXT['close'],
            command=self._on_close,
            bootstyle="outline",
            width=15
        )
        cancel_btn.pack(side=RIGHT)
        
        # Add tooltips if available
        if TOOLTIP_AVAILABLE and ToolTip:
            try:
                ToolTip(download_btn, text=DIALOG_TEXT['tooltip_download'], delay=400)
                ToolTip(skip_btn, text=DIALOG_TEXT['tooltip_skip'], delay=400)
                ToolTip(cancel_btn, text=DIALOG_TEXT['tooltip_close'], delay=400)
            except Exception as e:
                logger.warning(f"Failed to add button tooltips: {e}")
                
        # Set default button (Enter key)
        self.dialog.bind('<Return>', lambda e: self._on_download())
        self.dialog.bind('<Escape>', lambda e: self._on_close())
        
        # Focus on download button
        download_btn.focus_set()
        
    def _on_download(self):
        """Handle download button click"""
        self.result = 'download'
        self._open_release_page()
        self.dialog.destroy()
        
    def _on_skip(self):
        """Handle skip version button click"""
        self.result = 'skip'
        
        # Show confirmation message
        try:
            messagebox.showinfo(
                "Version hoppades över",
                DIALOG_TEXT['version_skipped'].format(self.update_info.latest_version)
            )
        except Exception as e:
            logger.warning(f"Error showing skip confirmation: {e}")
            
        self.dialog.destroy()
        
    def _on_close(self):
        """Handle dialog close"""
        self.result = 'cancel'
        self.dialog.destroy()
        
    def _open_release_page(self):
        """Open GitHub release page in browser"""
        try:
            # Show opening message
            logger.info(f"Opening release page: {self.update_info.release_url}")
            
            # Use webbrowser module for security
            success = webbrowser.open(self.update_info.release_url)
            
            if not success:
                # Fallback error message
                messagebox.showerror(
                    DIALOG_TEXT['title_error'],
                    f"{DIALOG_TEXT['browser_error']}\n\n{self.update_info.release_url}"
                )
                
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            messagebox.showerror(
                DIALOG_TEXT['title_error'],
                f"{DIALOG_TEXT['browser_error']}\n\n{self.update_info.release_url}"
            )
            
    def _set_window_icon(self, window):
        """Set application icon on window"""
        try:
            # Get icon path (same logic as main app)
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable
                app_dir = Path(sys.executable).parent
            else:
                # Running as Python script - go up from src/update to project root
                app_dir = Path(__file__).parent.parent.parent
                
            icon_path = app_dir / "Agg-med-smor-v4-transperent.ico"
            
            if icon_path.exists():
                window.iconbitmap(str(icon_path))
            else:
                logger.warning(f"Icon file not found: {icon_path}")
                
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")
            
    def _center_dialog(self):
        """Center dialog relative to parent window"""
        try:
            self.dialog.update_idletasks()
            
            # Get parent window position and size
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            # Get dialog size
            dialog_width = self.dialog.winfo_reqwidth()
            dialog_height = self.dialog.winfo_reqheight()
            
            # Calculate center position
            x = parent_x + (parent_width // 2) - (dialog_width // 2)
            y = parent_y + (parent_height // 2) - (dialog_height // 2)
            
            # Ensure dialog is visible on screen
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            
            x = max(0, min(x, screen_width - dialog_width))
            y = max(0, min(y, screen_height - dialog_height))
            
            self.dialog.geometry(f"+{x}+{y}")
            
        except Exception as e:
            logger.warning(f"Could not center dialog: {e}")
            
    def _show_modal_dialog(self):
        """Show dialog modally and wait for result"""
        try:
            # Wait for dialog to be ready
            self.dialog.update_idletasks()
            
            # Show dialog and wait for it to be destroyed
            self.dialog.wait_window()
            
        except Exception as e:
            logger.error(f"Error in modal dialog: {e}")
            self.result = 'cancel'


# Convenience functions
def show_update_dialog(parent_window, update_info: UpdateInfo) -> str:
    """
    Show update dialog and return user action
    
    Args:
        parent_window: Parent tkinter window
        update_info: Update information to display
        
    Returns:
        User action: 'download', 'skip', or 'cancel'
    """
    dialog = UpdateDialog(parent_window)
    return dialog.show_update_available(update_info)


def show_update_check_result(parent_window, result: UpdateCheckResult) -> Optional[str]:
    """
    Show appropriate dialog based on update check result
    
    Args:
        parent_window: Parent tkinter window
        result: Update check result
        
    Returns:
        User action if update available, None otherwise
    """
    dialog = UpdateDialog(parent_window)
    
    if result.success and result.has_update:
        return dialog.show_update_available(result.update_info)
    elif result.success and result.is_current:
        dialog.show_no_updates_dialog()
        return None
    else:
        dialog.show_check_error_dialog(result.error_message or "Okänt fel")
        return None