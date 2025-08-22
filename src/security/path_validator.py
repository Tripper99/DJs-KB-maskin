#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive path validation module for security
Prevents path traversal, injection attacks, and unauthorized file access
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Tuple
import unicodedata

logger = logging.getLogger(__name__)

# Windows-specific reserved names
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
    'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5',
    'LPT6', 'LPT7', 'LPT8', 'LPT9', 'CLOCK$'
}

# Dangerous path patterns
DANGEROUS_PATTERNS = [
    r'\.\.[\\/]',           # Parent directory traversal
    r'^\\\\\?\\',           # Windows extended path
    r'^\\\\\.\\',           # Windows device path
    r'^\\\\[^\\]+\\',       # UNC path (\\server\share)
    r'[\x00-\x1f\x7f]',     # Control characters
    r'[<>"|?*]',            # Windows invalid characters (allow : for drive letters)
]

# Maximum path lengths
MAX_PATH_LENGTH = 260  # Windows MAX_PATH
MAX_FILENAME_LENGTH = 255


class PathValidator:
    """Secure path validation with whitelist-based approach"""
    
    def __init__(self, allowed_base_dirs: Optional[List[str]] = None):
        """
        Initialize path validator with optional base directory restrictions
        
        Args:
            allowed_base_dirs: List of allowed base directories for operations
        """
        self.allowed_base_dirs = []
        if allowed_base_dirs:
            for base_dir in allowed_base_dirs:
                try:
                    resolved = Path(base_dir).resolve()
                    if resolved.exists() and resolved.is_dir():
                        self.allowed_base_dirs.append(resolved)
                    else:
                        logger.warning(f"Allowed base dir does not exist or is not a directory: {base_dir}")
                except Exception as e:
                    logger.error(f"Error resolving base directory {base_dir}: {e}")
    
    def is_safe_path(self, path_str: str, 
                     must_exist: bool = False,
                     allow_relative: bool = False,
                     base_dir: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Comprehensive path validation
        
        Args:
            path_str: Path string to validate
            must_exist: Whether the path must already exist
            allow_relative: Whether to allow relative paths
            base_dir: Specific base directory to restrict to
            
        Returns:
            Tuple of (is_valid, error_message, safe_path)
        """
        
        if not path_str:
            return False, "Tom sökväg angiven", None
            
        # Remove any null bytes
        if '\x00' in path_str:
            return False, "Ogiltig sökväg: innehåller null-tecken", None
            
        # Normalize unicode to prevent homograph attacks
        try:
            path_str = unicodedata.normalize('NFKC', path_str)
        except Exception:
            return False, "Ogiltig Unicode i sökväg", None
            
        # Check length limits
        if len(path_str) > MAX_PATH_LENGTH:
            return False, f"Sökväg för lång (max {MAX_PATH_LENGTH} tecken)", None
            
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                return False, "Ogiltig sökväg: innehåller otillåtet mönster", None
        
        # Check for path traversal attempts
        if '..' in path_str:
            return False, "Ogiltig sökväg: innehåller '..'", None
            
        # Parse the path
        try:
            path = Path(path_str)
        except Exception as e:
            return False, f"Ogiltig sökväg: {str(e)}", None
            
        # Check if it's absolute when it shouldn't be
        if not allow_relative and not path.is_absolute():
            # Make it absolute relative to current working directory
            try:
                path = Path.cwd() / path
            except Exception as e:
                return False, f"Kunde inte lösa relativ sökväg: {str(e)}", None
                
        # Resolve the path (follow symlinks, normalize)
        try:
            resolved_path = path.resolve()
        except Exception as e:
            return False, f"Kunde inte lösa sökväg: {str(e)}", None
            
        # Check against allowed base directories
        if base_dir:
            try:
                base_resolved = Path(base_dir).resolve()
                if not self._is_subpath(resolved_path, base_resolved):
                    return False, "Sökväg utanför tillåten katalog", None
            except Exception as e:
                return False, f"Ogiltig baskatalog: {str(e)}", None
                
        elif self.allowed_base_dirs:
            # Check if path is within any allowed base directory
            in_allowed = False
            for allowed_dir in self.allowed_base_dirs:
                if self._is_subpath(resolved_path, allowed_dir):
                    in_allowed = True
                    break
            if not in_allowed:
                return False, "Sökväg utanför tillåtna kataloger", None
                
        # Check if path exists when required
        if must_exist and not resolved_path.exists():
            return False, "Sökväg existerar inte", None
            
        # Additional checks for files
        if resolved_path.exists() and resolved_path.is_file():
            # Check filename
            filename = resolved_path.name
            if len(filename) > MAX_FILENAME_LENGTH:
                return False, f"Filnamn för långt (max {MAX_FILENAME_LENGTH} tecken)", None
                
        return True, None, resolved_path
    
    def sanitize_filename(self, filename: str, 
                         preserve_extension: bool = True) -> str:
        """
        Sanitize a filename for safe use
        
        Args:
            filename: Original filename
            preserve_extension: Whether to preserve file extension
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"
            
        # Normalize unicode
        filename = unicodedata.normalize('NFKC', filename)
        
        # Split extension if preserving
        name = filename
        ext = ""
        if preserve_extension and '.' in filename:
            parts = filename.rsplit('.', 1)
            if len(parts) == 2:
                name, ext = parts
                ext = '.' + ext
        
        # Remove/replace invalid characters
        # Keep alphanumeric, spaces, hyphens, underscores, and Swedish characters
        name = re.sub(r'[^\w\s\-åäöÅÄÖ]', '_', name, flags=re.UNICODE)
        
        # Remove multiple underscores
        name = re.sub(r'_+', '_', name)
        
        # Trim whitespace and underscores
        name = name.strip('_ \t\n\r')
        
        # Ensure not empty
        if not name:
            name = "unnamed"
            
        # Check against Windows reserved names
        name_upper = name.upper()
        if name_upper in WINDOWS_RESERVED_NAMES:
            name = f"{name}_safe"
            
        # Limit length
        max_name_len = MAX_FILENAME_LENGTH - len(ext)
        if len(name) > max_name_len:
            name = name[:max_name_len]
            
        return name + ext
    
    def validate_excel_path(self, excel_path: str) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Special validation for Excel file paths
        
        Args:
            excel_path: Path to Excel file
            
        Returns:
            Tuple of (is_valid, error_message, safe_path)
        """
        # Basic path validation
        is_valid, error_msg, safe_path = self.is_safe_path(
            excel_path, 
            must_exist=True,
            allow_relative=False
        )
        
        if not is_valid:
            return False, error_msg, None
            
        # Check file extension
        if safe_path.suffix.lower() not in ['.xlsx', '.xls', '.xlsm']:
            return False, "Filen måste vara en Excel-fil (.xlsx, .xls, .xlsm)", None
            
        # Check file size (prevent huge files)
        try:
            file_size = safe_path.stat().st_size
            max_size = 100 * 1024 * 1024  # 100 MB
            if file_size > max_size:
                return False, f"Excel-fil för stor (max {max_size // (1024*1024)} MB)", None
        except Exception as e:
            return False, f"Kunde inte kontrollera filstorlek: {str(e)}", None
            
        return True, None, safe_path
    
    def validate_directory(self, dir_path: str, 
                          must_exist: bool = True,
                          create_if_missing: bool = False) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Validate a directory path
        
        Args:
            dir_path: Directory path to validate
            must_exist: Whether directory must exist
            create_if_missing: Create directory if it doesn't exist
            
        Returns:
            Tuple of (is_valid, error_message, safe_path)
        """
        # Basic path validation
        is_valid, error_msg, safe_path = self.is_safe_path(
            dir_path,
            must_exist=False,
            allow_relative=False
        )
        
        if not is_valid:
            return False, error_msg, None
            
        # Check if it's a directory
        if safe_path.exists() and not safe_path.is_dir():
            return False, "Sökvägen är inte en katalog", None
            
        # Handle existence requirements
        if must_exist and not safe_path.exists():
            if create_if_missing:
                try:
                    safe_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {safe_path}")
                except Exception as e:
                    return False, f"Kunde inte skapa katalog: {str(e)}", None
            else:
                return False, "Katalogen existerar inte", None
                
        return True, None, safe_path
    
    def _is_subpath(self, path: Path, base: Path) -> bool:
        """
        Check if path is a subpath of base
        
        Args:
            path: Path to check
            base: Base path
            
        Returns:
            True if path is under base
        """
        try:
            path.relative_to(base)
            return True
        except ValueError:
            return False


# Singleton instance for application-wide use
_default_validator = None

def get_default_validator() -> PathValidator:
    """Get or create the default path validator instance"""
    global _default_validator
    if _default_validator is None:
        _default_validator = PathValidator()
    return _default_validator

def set_allowed_directories(directories: List[str]):
    """Configure allowed base directories for the default validator"""
    global _default_validator
    _default_validator = PathValidator(allowed_base_dirs=directories)