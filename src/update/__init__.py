#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update system module for DJs KB-maskin application
Provides version checking and update functionality via GitHub Releases
"""

from .models import (
    AssetInfo,
    ReleaseAssets,
    UpdateInfo,
    UpdateCheckResult
)

from .version_checker import (
    VersionChecker,
    create_version_checker,
    quick_update_check
)

from .update_dialog import (
    UpdateDialog,
    show_update_dialog,
    show_update_check_result
)

__all__ = [
    'AssetInfo',
    'ReleaseAssets', 
    'UpdateInfo',
    'UpdateCheckResult',
    'VersionChecker',
    'create_version_checker',
    'quick_update_check',
    'UpdateDialog',
    'show_update_dialog',
    'show_update_check_result'
]