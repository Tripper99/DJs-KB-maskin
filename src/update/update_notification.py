#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Non-blocking update notification window
Displays small notification for available updates without blocking main window
"""

import logging
import sys
from pathlib import Path

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import X, BOTH, LEFT
    try:
        from ttkbootstrap.tooltip import ToolTip
        TOOLTIP_AVAILABLE = True
    except ImportError:
        TOOLTIP_AVAILABLE = False
        ToolTip = None
except ImportError:
    print("Error: ttkbootstrap not installed. Install with: pip install ttkbootstrap")
    exit(1)

from .models import UpdateInfo
from .update_dialog import UpdateDialog

logger = logging.getLogger(__name__)

# Swedish UI text constants
NOTIFICATION_TEXT = {
    'title': 'Uppdatering tillgänglig',
    'new_version_available': 'Ny version tillgänglig:',
    'published': 'Publicerad:',
    'view_update': 'Visa uppdatering',
    'close': 'Stäng',
    'tooltip_view': 'Öppnar fullständig uppdateringsinformation med nedladdningslänk',
    'tooltip_close': 'Stänger detta meddelande. Du kan söka efter uppdateringar från Hjälp-menyn.'
}


class UpdateNotification:
    """Non-blocking notification for available updates"""

    def __init__(self, parent_window, update_info: UpdateInfo):
        """
        Initialize update notification

        Args:
            parent_window: Parent tkinter window
            update_info: Information about available update
        """
        self.parent = parent_window
        self.update_info = update_info
        self.notification = None
        self.auto_dismiss_id = None

    def show(self):
        """Show notification window in bottom-right corner"""
        try:
            self._create_notification_window()
            self._position_notification()
            self._schedule_auto_dismiss()

            logger.info(f"Update notification displayed for version {self.update_info.latest_version}")

        except Exception as e:
            logger.error(f"Error showing update notification: {e}")

    def _create_notification_window(self):
        """Create the notification window"""
        # Create Toplevel window (NOT modal)
        self.notification = tb.Toplevel(self.parent)
        self.notification.title(NOTIFICATION_TEXT['title'])
        self.notification.geometry("350x150")
        self.notification.resizable(False, False)

        # Set as transient but DON'T use grab_set() (non-blocking)
        self.notification.transient(self.parent)

        # Stay on top temporarily
        self.notification.attributes('-topmost', True)

        # Set icon on notification
        self._set_window_icon(self.notification)

        # Handle window close button
        self.notification.protocol("WM_DELETE_WINDOW", self.dismiss)

        # Create main content frame
        main_frame = tb.Frame(self.notification, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        # Create content
        self._create_notification_content(main_frame)
        self._create_notification_buttons(main_frame)

        # Remove topmost after 2 seconds
        self.notification.after(2000, lambda: self.notification.attributes('-topmost', False))

    def _create_notification_content(self, parent):
        """Create notification content"""
        # Title with version
        title_frame = tb.Frame(parent)
        title_frame.pack(fill=X, pady=(0, 10))

        tb.Label(
            title_frame,
            text=f"{NOTIFICATION_TEXT['new_version_available']} {self.update_info.latest_version}",
            font=("TkDefaultFont", 10, "bold"),
            bootstyle="success"
        ).pack(side=LEFT)

        # Published date (if available)
        if self.update_info.formatted_date:
            date_frame = tb.Frame(parent)
            date_frame.pack(fill=X, pady=(0, 15))

            tb.Label(
                date_frame,
                text=f"{NOTIFICATION_TEXT['published']} {self.update_info.formatted_date}",
                font=("TkDefaultFont", 9)
            ).pack(side=LEFT)

    def _create_notification_buttons(self, parent):
        """Create action buttons"""
        button_frame = tb.Frame(parent)
        button_frame.pack(fill=X, pady=(10, 0))

        # View Update button (primary action)
        view_btn = tb.Button(
            button_frame,
            text=NOTIFICATION_TEXT['view_update'],
            command=self._show_full_dialog,
            bootstyle="success",
            width=18
        )
        view_btn.pack(side=LEFT, padx=(0, 10))

        # Close button
        close_btn = tb.Button(
            button_frame,
            text=NOTIFICATION_TEXT['close'],
            command=self.dismiss,
            bootstyle="outline",
            width=12
        )
        close_btn.pack(side=LEFT)

        # Add tooltips if available
        if TOOLTIP_AVAILABLE and ToolTip:
            try:
                ToolTip(view_btn, text=NOTIFICATION_TEXT['tooltip_view'], delay=400, wraplength=300)
                ToolTip(close_btn, text=NOTIFICATION_TEXT['tooltip_close'], delay=400, wraplength=300)
            except Exception as e:
                logger.warning(f"Failed to add tooltips to notification buttons: {e}")

        # Set keyboard shortcuts
        self.notification.bind('<Return>', lambda e: self._show_full_dialog())
        self.notification.bind('<Escape>', lambda e: self.dismiss())

        # Focus on view button
        view_btn.focus_set()

    def _position_notification(self):
        """Position notification in bottom-right corner of screen"""
        try:
            self.notification.update_idletasks()

            # Get screen dimensions
            screen_width = self.notification.winfo_screenwidth()
            screen_height = self.notification.winfo_screenheight()

            # Get notification dimensions
            notification_width = 350
            notification_height = 150

            # Calculate position (bottom-right with margins)
            x = screen_width - notification_width - 20
            y = screen_height - notification_height - 100  # 100px margin for taskbar

            # Ensure notification is visible on screen
            x = max(0, min(x, screen_width - notification_width))
            y = max(0, min(y, screen_height - notification_height))

            self.notification.geometry(f"+{x}+{y}")

            logger.debug(f"Notification positioned at ({x}, {y})")

        except Exception as e:
            logger.warning(f"Could not position notification: {e}")

    def _schedule_auto_dismiss(self):
        """Schedule auto-dismiss after 15 seconds"""
        try:
            self.auto_dismiss_id = self.notification.after(15000, self.dismiss)
            logger.debug("Auto-dismiss scheduled for 15 seconds")
        except Exception as e:
            logger.warning(f"Could not schedule auto-dismiss: {e}")

    def _show_full_dialog(self):
        """Open full modal UpdateDialog and dismiss notification"""
        try:
            logger.info("Opening full update dialog from notification")

            # Create and show full update dialog
            dialog = UpdateDialog(self.parent)
            result = dialog.show_update_available(self.update_info)

            logger.debug(f"Update dialog result: {result}")

            # Dismiss notification
            self.dismiss()

        except Exception as e:
            logger.error(f"Error opening full update dialog: {e}")
            # Still dismiss notification even if dialog fails
            self.dismiss()

    def dismiss(self):
        """Dismiss notification window"""
        try:
            # Cancel auto-dismiss timer if active
            if self.auto_dismiss_id and self.notification:
                try:
                    self.notification.after_cancel(self.auto_dismiss_id)
                    self.auto_dismiss_id = None
                    logger.debug("Auto-dismiss timer cancelled")
                except Exception as e:
                    logger.warning(f"Could not cancel auto-dismiss timer: {e}")

            # Destroy notification window
            if self.notification:
                self.notification.destroy()
                self.notification = None
                logger.info("Update notification dismissed")

        except Exception as e:
            logger.error(f"Error dismissing notification: {e}")

    def _set_window_icon(self, window):
        """Set application icon on notification window"""
        try:
            # Get icon path (same logic as main app)
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable
                if hasattr(sys, '_MEIPASS'):
                    icon_path = Path(sys._MEIPASS) / "Agg-med-smor-v4-transperent.ico"
                else:
                    app_dir = Path(sys.executable).parent
                    icon_path = app_dir / "Agg-med-smor-v4-transperent.ico"
            else:
                # Running as Python script - go up from src/update to project root
                app_dir = Path(__file__).parent.parent.parent
                icon_path = app_dir / "Agg-med-smor-v4-transperent.ico"

            if icon_path.exists():
                window.iconbitmap(str(icon_path))
                logger.debug(f"Icon set from: {icon_path}")
            else:
                logger.warning(f"Icon file not found: {icon_path}")

        except Exception as e:
            logger.warning(f"Could not set window icon on notification: {e}")


# Convenience function
def show_update_notification(parent_window, update_info: UpdateInfo) -> None:
    """
    Show update notification

    Args:
        parent_window: Parent tkinter window
        update_info: Update information to display
    """
    notification = UpdateNotification(parent_window, update_info)
    notification.show()
