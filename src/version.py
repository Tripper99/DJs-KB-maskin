#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized version management for DJs KB-maskin application
"""

__version__ = "1.10.0"
__version_info__ = (1, 10, 0)
__release_date__ = "2026-01-10"

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
1.10.0 (2026-01-10): Cross-platform compatibility improvements - Fixed folder opening to work on Windows/Linux/macOS, implemented platform-specific config persistence (Windows: %APPDATA%, Linux/macOS: ~/.djs_kb_maskin), added automatic migration from old config location
1.9.0 (2025-12-10): Automatic update checking at startup - Added non-blocking notification system that checks GitHub for updates once per week, with user control via Help menu checkbox
1.8.0 (2025-09-17): Fixed outdated folder creation - Removed legacy "Nedladdningar" folder creation in program directory (downloads now correctly go to Downloads\Svenska tidningar)
1.7.9 (2025-09-17): Single instance restriction - Added Windows mutex to prevent multiple app instances, includes Swedish error message and focus existing window functionality
1.7.8 (2025-09-14): Critical folder management bug fix - Resolved dual path system causing all folder operations to fail, standardized default paths, fixed GUI display issues
1.7.7 (2025-09-14): Settings compatibility fix - Added version tracking to invalidate old settings files, ensuring fresh defaults with new versions
1.7.6 (2025-09-14): Major enhancement - Changed default download location to 'Svenska tidningar' in user's Downloads folder with enhanced folder validation
1.7.5 (2025-09-13): Critical fix - Resolved default download folder path resolution bug in installed executable
1.7.4 (2025-09-10): Bug fix - Fixed 'Overwrite All' option to persist across multiple file conflicts during PDF creation
1.7.3 (2025-09-10): GUI reorganization - Moved CSV status info to bottom of KB section
1.7.2 (2025-09-10): UI cleanup - Removed obsolete Excel references from user messages
1.7.1 (2025-09-10): Critical fix - Corrected bib-code extraction to strip 'bib' prefix before CSV lookup
1.7.0 (2025-09-10): Major update - Replaced Excel with CSV for bib-code lookup, simplified GUI, reduced dependencies
1.6.3 (2025-09-08): Code cleanup - removed redundant if-else statement in KB processor filename construction
1.6.2 (2025-09-08): Added requirements.txt file with all dependencies and version numbers
1.6.1 (2025-09-08): Code cleanup - removed unnecessary if statement in KB processor
1.6.0 (2025-09-07): Added Inno Setup installer with organized build tools and documentation
1.5.9 (2025-08-30): Fixed update dialog height - doubled to 900px to show all content properly
1.5.8 (2025-08-29): Added comprehensive update checking system with GitHub Releases API integration
1.5.7 (2025-08-28): Added application icon to file conflict dialogs (both Gmail JPG and KB PDF conflicts)
1.5.6 (2025-08-28): Fixed confirmation dialog size - made it larger and resizable so buttons are visible
1.5.5 (2025-08-28): Added application icon to all custom dialog windows including confirmation dialog
1.5.4 (2025-08-28): Fixed Unicode encoding issues - replaced emoji characters with ASCII for Windows compatibility
1.5.3 (2025-08-28): Added confirmation dialog before downloading email attachments
1.5.2 (2025-08-28): Date fields no longer persist between sessions - always start fresh
1.5.1 (2025-08-25): Changed button text from 'Bläddra...' to 'Välj mapp...' for better user clarity
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