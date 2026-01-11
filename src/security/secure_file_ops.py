#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure file operations wrapper
Provides safe wrappers for file I/O, pandas operations, and subprocess calls
"""

import os
import re
import subprocess
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Union

from .path_validator import PathValidator, get_default_validator

logger = logging.getLogger(__name__)


class SecureFileOps:
    """Secure wrappers for file operations"""
    
    def __init__(self, validator: Optional[PathValidator] = None):
        """
        Initialize secure file operations
        
        Args:
            validator: Path validator instance (uses default if None)
        """
        self.validator = validator or get_default_validator()
        
    def save_file(self, content: Union[bytes, str], 
                  filename: str, 
                  output_dir: str,
                  binary: bool = True) -> Path:
        """
        Securely save content to a file
        
        Args:
            content: File content to save
            filename: Desired filename (will be sanitized)
            output_dir: Output directory
            binary: Whether to write in binary mode
            
        Returns:
            Path to saved file
            
        Raises:
            ValueError: If validation fails
        """
        # Validate output directory
        is_valid, error_msg, safe_dir = self.validator.validate_directory(
            output_dir,
            must_exist=False,
            create_if_missing=True
        )
        
        if not is_valid:
            logger.error(f"Output directory validation failed: {error_msg}")
            raise ValueError(f"Ogiltig utdata-katalog: {error_msg}")
            
        # Sanitize filename
        safe_filename = self.validator.sanitize_filename(filename)
        
        # Construct full path
        output_path = safe_dir / safe_filename
        
        # Check if file already exists
        if output_path.exists():
            logger.warning(f"File already exists: {output_path}")
            # Could implement versioning or user prompt here
            
        # Save file
        try:
            mode = 'wb' if binary else 'w'
            encoding = None if binary else 'utf-8'
            
            with open(output_path, mode, encoding=encoding) as f:
                f.write(content)
                
            logger.info(f"Securely saved file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise Exception(f"Kunde inte spara fil: {str(e)}")
    
    def open_file(self, file_path: str, mode: str = 'r', **kwargs):
        """
        Securely open a file for reading/writing
        
        Args:
            file_path: Path to file
            mode: File open mode
            **kwargs: Additional arguments for open()
            
        Returns:
            File handle
            
        Raises:
            ValueError: If path validation fails
        """
        # Check if writing mode
        must_exist = 'r' in mode
        
        # Validate file path
        is_valid, error_msg, safe_path = self.validator.is_safe_path(
            file_path,
            must_exist=must_exist
        )
        
        if not is_valid:
            logger.error(f"File path validation failed: {error_msg}")
            raise ValueError(f"Ogiltig filsökväg: {error_msg}")
            
        # Open file with validated path
        return open(safe_path, mode, **kwargs)
    
    def safe_subprocess_run(self, command: List[str], 
                           file_arg: Optional[str] = None,
                           **kwargs) -> subprocess.CompletedProcess:
        """
        Securely run a subprocess command
        
        Args:
            command: Command as list of arguments
            file_arg: Optional file path argument to validate
            **kwargs: Additional arguments for subprocess.run
            
        Returns:
            CompletedProcess result
            
        Raises:
            ValueError: If validation fails
        """
        # Never use shell=True for security
        if kwargs.get('shell', False):
            logger.error("Attempted to run subprocess with shell=True")
            raise ValueError("Shell mode är inte tillåtet av säkerhetsskäl")
            
        # Validate file argument if provided
        if file_arg:
            is_valid, error_msg, safe_path = self.validator.is_safe_path(
                file_arg,
                must_exist=True
            )

            if not is_valid:
                logger.error(f"File argument validation failed: {error_msg}")
                raise ValueError(f"Ogiltig fil för subprocess: {error_msg}")

            # Append validated path to command
            command = command + [str(safe_path)]
            
        # Set secure defaults
        kwargs.setdefault('shell', False)
        kwargs.setdefault('check', True)
        kwargs.setdefault('capture_output', True)
        kwargs.setdefault('text', True)
        
        try:
            logger.info(f"Running secure subprocess: {command[0]}")
            result = subprocess.run(command, **kwargs)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Subprocess error: {e}")
            raise
    
    def glob_files(self, directory: str, pattern: str = "*") -> List[Path]:
        """
        Securely glob files in a directory
        
        Args:
            directory: Directory to search
            pattern: Glob pattern
            
        Returns:
            List of matching file paths
            
        Raises:
            ValueError: If validation fails
        """
        # Validate directory
        is_valid, error_msg, safe_dir = self.validator.validate_directory(
            directory,
            must_exist=True
        )
        
        if not is_valid:
            logger.error(f"Directory validation failed for glob: {error_msg}")
            raise ValueError(f"Ogiltig katalog för sökning: {error_msg}")
            
        # Sanitize pattern to prevent injection
        # Allow only safe glob patterns
        safe_pattern = pattern  # Keep original pattern for now, validate directory instead
        
        try:
            files = list(safe_dir.glob(safe_pattern))
            logger.info(f"Found {len(files)} files matching pattern {safe_pattern}")
            return files
        except Exception as e:
            logger.error(f"Glob operation failed: {e}")
            raise Exception(f"Kunde inte söka filer: {str(e)}")
    
    def create_temp_file(self, suffix: str = None, 
                        prefix: str = "tmp_",
                        content: Optional[Union[bytes, str]] = None,
                        binary: bool = True) -> Path:
        """
        Create a secure temporary file
        
        Args:
            suffix: File suffix
            prefix: File prefix
            content: Optional content to write
            binary: Whether to write in binary mode
            
        Returns:
            Path to temporary file
        """
        # Sanitize prefix and suffix
        if prefix:
            prefix = self.validator.sanitize_filename(prefix, preserve_extension=False)
        if suffix:
            suffix = '.' + re.sub(r'[^\w]', '', suffix)
            
        try:
            # Create temp file
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # Close file descriptor
            
            temp_path = Path(temp_path)
            
            # Write content if provided
            if content is not None:
                mode = 'wb' if binary else 'w'
                encoding = None if binary else 'utf-8'
                with open(temp_path, mode, encoding=encoding) as f:
                    f.write(content)
                    
            logger.info(f"Created secure temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to create temp file: {e}")
            raise Exception(f"Kunde inte skapa temporär fil: {str(e)}")
    
    def copy_file(self, source: str, destination: str) -> Path:
        """
        Securely copy a file
        
        Args:
            source: Source file path
            destination: Destination path
            
        Returns:
            Path to copied file
            
        Raises:
            ValueError: If validation fails
        """
        # Validate source
        is_valid, error_msg, safe_source = self.validator.is_safe_path(
            source,
            must_exist=True
        )
        
        if not is_valid:
            logger.error(f"Source path validation failed: {error_msg}")
            raise ValueError(f"Ogiltig källfil: {error_msg}")
            
        # Validate destination directory
        dest_path = Path(destination)
        if dest_path.is_dir():
            dest_dir = destination
            dest_file = safe_source.name
        else:
            dest_dir = str(dest_path.parent)
            dest_file = dest_path.name
            
        is_valid, error_msg, safe_dest_dir = self.validator.validate_directory(
            dest_dir,
            must_exist=False,
            create_if_missing=True
        )
        
        if not is_valid:
            logger.error(f"Destination directory validation failed: {error_msg}")
            raise ValueError(f"Ogiltig målkatalog: {error_msg}")
            
        # Sanitize destination filename
        safe_dest_file = self.validator.sanitize_filename(dest_file)
        safe_dest = safe_dest_dir / safe_dest_file
        
        try:
            shutil.copy2(safe_source, safe_dest)
            logger.info(f"Securely copied file: {safe_source} -> {safe_dest}")
            return safe_dest
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise Exception(f"Kunde inte kopiera fil: {str(e)}")


# Singleton instance for application-wide use
_default_ops = None

def get_secure_ops() -> SecureFileOps:
    """Get or create the default secure file operations instance"""
    global _default_ops
    if _default_ops is None:
        _default_ops = SecureFileOps()
    return _default_ops


