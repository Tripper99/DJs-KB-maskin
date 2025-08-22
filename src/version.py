#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized version management for DJs KB-maskin application
"""

__version__ = "1.3.4"
__version_info__ = (1, 3, 4)
__release_date__ = "2025-08-22"

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
1.3.4 (2025-08-22): Updated documentation - DEVELOPMENT_HISTORY.md and CLAUDE.md reflect latest changes
1.3.3 (2025-08-22): GUI improvements - Increased window height by 40%, positioned higher on screen, reordered KB section elements
1.3.2 (2025-08-22): Added comprehensive codebase analysis documentation and architecture overview
1.3.1 (2025-08-22): Fixed filename sanitization bug - Restored parentheses in PDF names
1.3 (2025-08-22): Comprehensive security implementation - Path validation, secure file ops, and vulnerability fixes
1.2 (2025-08-22): Security improvements - Added comprehensive path validation
1.1 (2025-07-17): Documentation reorganization
1.0 (2025-07-16): Initial production release
"""