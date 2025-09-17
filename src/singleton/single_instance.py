#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Instance Management for DJs KB-maskin
Prevents multiple instances of the application from running simultaneously.
"""

import ctypes
import sys
import tkinter as tk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)


class SingleInstance:
    """
    Windows-specific single instance implementation using named mutex.
    Prevents multiple instances of the application from running.
    """

    def __init__(self, app_name="DJs_KB_maskin"):
        """
        Initialize single instance checker.

        Args:
            app_name (str): Unique name for the application mutex
        """
        self.app_name = app_name
        self.mutex_name = f"{app_name}_SingleInstance"
        self.mutex_handle = None
        self._is_windows = sys.platform.startswith('win')

        if not self._is_windows:
            logger.warning("Single instance check only works on Windows")
            return

        # Windows API constants
        self.ERROR_ALREADY_EXISTS = 183
        self.WAIT_ABANDONED = 0x00000080

    def is_another_instance_running(self):
        """
        Check if another instance of the application is already running.

        Returns:
            bool: True if another instance is running, False otherwise
        """
        if not self._is_windows:
            return False

        try:
            # Try to create a named mutex
            kernel32 = ctypes.windll.kernel32
            self.mutex_handle = kernel32.CreateMutexW(
                None,  # Default security attributes
                True,  # Initially owned
                self.mutex_name  # Mutex name
            )

            if not self.mutex_handle:
                logger.error("Failed to create mutex")
                return False

            # Check if mutex already existed
            last_error = kernel32.GetLastError()

            if last_error == self.ERROR_ALREADY_EXISTS:
                logger.info("Another instance is already running")
                return True

            # Check for abandoned mutex (previous instance crashed)
            wait_result = kernel32.WaitForSingleObject(self.mutex_handle, 0)
            if wait_result == self.WAIT_ABANDONED:
                logger.warning("Found abandoned mutex from crashed instance, taking ownership")

            logger.info("Successfully acquired single instance mutex")
            return False

        except Exception as e:
            logger.error(f"Error checking for existing instance: {e}")
            return False

    def try_focus_existing_instance(self):
        """
        Try to bring the existing instance window to the foreground.
        Uses Windows API to find and focus the window.
        """
        if not self._is_windows:
            return

        try:
            user32 = ctypes.windll.user32

            # Find window by class name (tkinter windows use "Tk")
            # This is a best effort - may not always work perfectly
            def enum_window_callback(hwnd, lParam):
                # Get window title
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    window_title = buffer.value

                    # Look for our application window
                    if "DJs KB-maskin" in window_title or "Svenska Tidningar" in window_title:
                        # Try to bring window to foreground
                        # Use Alt key workaround for Windows focus restrictions
                        user32.keybd_event(0x12, 0, 0, 0)  # Alt down
                        user32.SetForegroundWindow(hwnd)
                        user32.keybd_event(0x12, 0, 2, 0)  # Alt up

                        # Also try to restore if minimized
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                        return False  # Stop enumeration
                return True  # Continue enumeration

            # Convert callback to C function pointer
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            callback = EnumWindowsProc(enum_window_callback)

            # Enumerate all windows
            user32.EnumWindows(callback, 0)

        except Exception as e:
            logger.error(f"Error trying to focus existing instance: {e}")

    def show_already_running_message(self):
        """
        Show a Swedish message that the application is already running.
        """
        try:
            # Create a temporary root window for the message box
            temp_root = tk.Tk()
            temp_root.withdraw()  # Hide the window

            # Set icon if available
            try:
                icon_path = "Agg-med-smor-v4-transperent.ico"
                temp_root.iconbitmap(icon_path)
            except Exception:
                pass  # Icon not critical

            messagebox.showwarning(
                "DJs KB-maskin körs redan",
                "DJs KB-maskin körs redan!\n\n"
                "Endast en instans av programmet kan köras åt gången.\n"
                "Det befintliga fönstret kommer nu att visas.",
                parent=temp_root
            )

            temp_root.destroy()

        except Exception as e:
            logger.error(f"Error showing already running message: {e}")

    def release_mutex(self):
        """
        Release the mutex when the application exits.
        """
        if self.mutex_handle and self._is_windows:
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
                logger.info("Released single instance mutex")
            except Exception as e:
                logger.error(f"Error releasing mutex: {e}")

    def __del__(self):
        """
        Ensure mutex is released when object is destroyed.
        """
        self.release_mutex()

    def check_and_handle_instance(self):
        """
        Complete check for existing instance with user notification.

        Returns:
            bool: True if this instance should continue, False if it should exit
        """
        if self.is_another_instance_running():
            self.show_already_running_message()
            self.try_focus_existing_instance()
            return False
        return True