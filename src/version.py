#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized version management for DJs KB-maskin application
"""

__version__ = "1.2"
__version_info__ = (1, 2, 0)
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
1.2 (2025-08-22): Security improvements - Added comprehensive path validation
1.1 (2025-07-17): Documentation reorganization
1.0 (2025-07-16): Initial production release
"""