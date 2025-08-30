#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data models for the update system
Provides validated data structures for version checking and release information
"""

from dataclasses import dataclass
from typing import Optional, List
import re
from datetime import datetime

# Version validation pattern
VERSION_PATTERN = re.compile(r'^v?\d+\.\d+\.\d+$')


@dataclass
class AssetInfo:
    """Information about a single release asset (file)"""
    
    name: str
    download_url: str
    size: int
    
    def __post_init__(self):
        """Validate asset information after initialization"""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Asset name must be a non-empty string")
            
        if len(self.name) > 100:
            raise ValueError("Asset name too long (max 100 characters)")
            
        if not isinstance(self.download_url, str) or not self.download_url.startswith('https://'):
            raise ValueError("Asset download URL must be a valid HTTPS URL")
            
        if not isinstance(self.size, int) or self.size < 0:
            raise ValueError("Asset size must be a non-negative integer")
            
    @property
    def is_exe_file(self) -> bool:
        """Check if this asset is an executable file"""
        return self.name.lower().endswith('.exe')
        
    @property
    def is_manual_file(self) -> bool:
        """Check if this asset is a manual document"""
        return (self.name.lower().endswith('.docx') or 
                self.name.lower().endswith('.pdf') or
                'manual' in self.name.lower())
                
    @property
    def size_mb(self) -> float:
        """Get asset size in megabytes"""
        return self.size / (1024 * 1024)
        
    def get_display_size(self) -> str:
        """Get human-readable size string"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size_mb:.1f} MB"


@dataclass
class ReleaseAssets:
    """Collection of assets in a release"""
    
    exe_file: Optional[AssetInfo] = None
    manual_file: Optional[AssetInfo] = None
    other_files: Optional[List[AssetInfo]] = None
    
    def __post_init__(self):
        """Initialize other_files if not provided"""
        if self.other_files is None:
            self.other_files = []
            
    @property
    def total_files(self) -> int:
        """Get total number of files"""
        count = 0
        if self.exe_file:
            count += 1
        if self.manual_file:
            count += 1
        count += len(self.other_files)
        return count
        
    @property
    def has_required_files(self) -> bool:
        """Check if release has the expected exe file"""
        return self.exe_file is not None
        
    @property
    def total_size(self) -> int:
        """Get total size of all assets in bytes"""
        total = 0
        if self.exe_file:
            total += self.exe_file.size
        if self.manual_file:
            total += self.manual_file.size
        for asset in self.other_files:
            total += asset.size
        return total
        
    def get_all_assets(self) -> List[AssetInfo]:
        """Get list of all assets"""
        assets = []
        if self.exe_file:
            assets.append(self.exe_file)
        if self.manual_file:
            assets.append(self.manual_file)
        assets.extend(self.other_files)
        return assets


@dataclass
class UpdateInfo:
    """Complete information about an available update"""
    
    current_version: str
    latest_version: str
    release_url: str
    release_notes: str
    assets: ReleaseAssets
    published_date: str
    is_newer: bool = False
    
    def __post_init__(self):
        """Validate update information after initialization"""
        # Validate version strings
        if not self._is_valid_version(self.current_version):
            raise ValueError(f"Invalid current version format: {self.current_version}")
            
        if not self._is_valid_version(self.latest_version):
            raise ValueError(f"Invalid latest version format: {self.latest_version}")
            
        # Validate URLs
        if not isinstance(self.release_url, str) or not self.release_url.startswith('https://'):
            raise ValueError("Release URL must be a valid HTTPS URL")
            
        # Validate release notes
        if not isinstance(self.release_notes, str):
            self.release_notes = ""
        elif len(self.release_notes) > 5000:
            self.release_notes = self.release_notes[:5000] + "..."
            
        # Validate assets
        if not isinstance(self.assets, ReleaseAssets):
            raise ValueError("Assets must be a ReleaseAssets instance")
            
        # Validate date
        if not isinstance(self.published_date, str):
            self.published_date = ""
            
        # Calculate if newer version if not explicitly set
        if not hasattr(self, '_is_newer_calculated'):
            self.is_newer = self._calculate_is_newer()
            self._is_newer_calculated = True
            
    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid"""
        return isinstance(version, str) and bool(VERSION_PATTERN.match(version))
        
    def _calculate_is_newer(self) -> bool:
        """Calculate if latest version is newer than current"""
        try:
            current_tuple = self._version_to_tuple(self.current_version)
            latest_tuple = self._version_to_tuple(self.latest_version)
            return latest_tuple > current_tuple
        except ValueError:
            return False
            
    def _version_to_tuple(self, version: str) -> tuple:
        """Convert version string to comparable tuple"""
        # Remove 'v' prefix if present
        clean_version = version.lstrip('v')
        return tuple(map(int, clean_version.split('.')))
        
    @property
    def version_comparison(self) -> str:
        """Get formatted version comparison string"""
        return f"{self.current_version} → {self.latest_version}"
        
    @property
    def short_release_notes(self) -> str:
        """Get shortened release notes for display"""
        if not self.release_notes:
            return "Inga versionsanteckningar tillgängliga"
            
        # Take first few lines or characters
        lines = self.release_notes.split('\n')
        if len(lines) > 3:
            return '\n'.join(lines[:3]) + '\n...'
        elif len(self.release_notes) > 200:
            return self.release_notes[:200] + "..."
        else:
            return self.release_notes
            
    @property
    def formatted_date(self) -> str:
        """Get formatted publication date"""
        if not self.published_date:
            return "Okänt datum"
            
        try:
            # Try to parse ISO format date
            if 'T' in self.published_date:
                dt = datetime.fromisoformat(self.published_date.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            else:
                return self.published_date
        except (ValueError, AttributeError):
            return self.published_date
            
    def get_file_summary(self) -> str:
        """Get summary of available files in Swedish"""
        files = []
        
        if self.assets.exe_file:
            files.append(f"• {self.assets.exe_file.name} ({self.assets.exe_file.get_display_size()})")
            
        if self.assets.manual_file:
            files.append(f"• {self.assets.manual_file.name} ({self.assets.manual_file.get_display_size()})")
            
        for asset in self.assets.other_files:
            files.append(f"• {asset.name} ({asset.get_display_size()})")
            
        if not files:
            return "Inga filer tillgängliga"
            
        return '\n'.join(files)


@dataclass
class UpdateCheckResult:
    """Result of an update check operation"""
    
    success: bool
    update_info: Optional[UpdateInfo] = None
    error_message: Optional[str] = None
    cached_result: bool = False
    check_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.check_timestamp is None:
            self.check_timestamp = datetime.now()
            
    @property
    def has_update(self) -> bool:
        """Check if an update is available"""
        return (self.success and 
                self.update_info is not None and 
                self.update_info.is_newer)
                
    @property
    def is_current(self) -> bool:
        """Check if current version is up to date"""
        return (self.success and 
                self.update_info is not None and 
                not self.update_info.is_newer)