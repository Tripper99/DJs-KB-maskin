#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized version management for DJs KB-maskin application
"""

__version__ = "1.5.0"
__version_info__ = (1, 5, 0)
__release_date__ = "2025-08-25"

def get_version():
    """Return the current version string"""
    return __version__

def get_version_info():
    """Return version as tuple (major, minor, patch)"""
    return __version_info__

def get_full_version():
    """Return full version string with date"""
    return f"v{__version__} ({__release_date__})"

# Version history
VERSION_HISTORY = """
1.5.0 (2025-08-25): Added clickable 'Öppna mapp' link to open download folder in Windows Explorer
1.4.9 (2025-08-25): Fixed placeholder text being saved to config file - prevents date validation errors
1.4.8 (2025-08-25): Fixed window icon display in PyInstaller executable
1.4.7 (2025-08-25): Changed default download folder to 'Nedladdningar' subfolder in application directory
1.4.6 (2025-08-23): Updated documentation for recent changes
1.4.5 (2025-08-23): Added tooltip to Start button with humorous 'whoopee machine' reference
1.4.4 (2025-08-23): Added tooltips to main tool selection switches for better user guidance
1.4.3 (2025-08-23): Changed default setting - 'Spara omdöpta jpg-filer i en underkatalog?' now defaults to OFF
1.4.1 (2025-08-23): Improved tooltips and user guidance in the GUI
1.4.0 (2025-08-23): Improved tooltips and user guidance in the GUI
1.3.8 (2025-08-23): Added comprehensive tooltips to all major GUI fields for improved user experience
1.3.7 (2025-08-23): Reversed delete logic - Original files now deleted by default (switch OFF), can be preserved by turning switch ON
1.3.6 (2025-08-22): GUI improvements - File dialogs start in app directory, window positioned higher, date placeholders added
1.3.5 (2025-08-22): Renamed settings file from combined_app_config.json to djs_kb-maskin_settings.json
1.3.4 (2025-08-22): Updated documentation - DEVELOPMENT_HISTORY.md and CLAUDE.md reflect latest changes
1.3.3 (2025-08-22): GUI improvements - Increased window height by 40%, positioned higher on screen, reordered KB section elements
1.3.2 (2025-08-22): Added comprehensive codebase analysis documentation and architecture overview
1.3.1 (2025-08-22): Fixed filename sanitization bug - Restored parentheses in PDF names
1.3 (2025-08-22): Comprehensive security implementation - Path validation, secure file ops, and vulnerability fixes
1.2 (2025-08-22): Security improvements - Added comprehensive path validation
1.1 (2025-07-17): Documentation reorganization
1.0 (2025-07-16): Initial production release
"""