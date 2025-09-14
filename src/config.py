# -*- coding: utf-8 -*-
"""
Configuration management for the DJs app
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

def get_app_directory():
    """
    Get the directory where the application is located (works for both .py and .exe)
    
    Returns:
        Path: Absolute path to the application directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        app_dir = Path(sys.executable).parent
        logger.debug(f"Running as executable - app directory: {app_dir}")
    else:
        # Running as Python script - go up 2 levels from src/config.py
        app_dir = Path(__file__).parent.parent
        logger.debug(f"Running as script - app directory: {app_dir}")
    
    # Ensure it's absolute
    app_dir = app_dir.resolve()
    logger.debug(f"Resolved app directory: {app_dir}")
    logger.debug(f"Current working directory: {Path.cwd()}")
    
    return app_dir

def get_user_downloads_folder():
    """
    Get the user's Downloads folder with cross-platform support and fallbacks
    
    Returns:
        Path: Absolute path to the user's Downloads folder, or fallback location
    """
    logger.debug("Detecting user's Downloads folder...")
    
    # Try platform-specific detection first
    try:
        if sys.platform.startswith('win'):
            # Windows: Try to get Downloads folder from registry
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
                    downloads_folder = Path(downloads_path)
                    if downloads_folder.exists():
                        logger.info(f"Windows Downloads folder found via registry: {downloads_folder}")
                        return downloads_folder
            except (ImportError, OSError, FileNotFoundError):
                logger.debug("Registry method failed, trying fallback")
            
            # Windows fallback: Standard Downloads folder
            downloads_folder = Path.home() / "Downloads"
            if downloads_folder.exists():
                logger.info(f"Windows Downloads folder found via fallback: {downloads_folder}")
                return downloads_folder
                
        elif sys.platform == 'darwin':
            # macOS: Standard Downloads folder
            downloads_folder = Path.home() / "Downloads"
            if downloads_folder.exists():
                logger.info(f"macOS Downloads folder found: {downloads_folder}")
                return downloads_folder
                
        else:
            # Linux/Unix: Try XDG user-dirs first
            try:
                result = subprocess.run(['xdg-user-dir', 'DOWNLOAD'], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    downloads_path = result.stdout.strip()
                    downloads_folder = Path(downloads_path)
                    if downloads_folder.exists():
                        logger.info(f"Linux Downloads folder found via XDG: {downloads_folder}")
                        return downloads_folder
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                logger.debug("XDG user-dirs method failed, trying fallback")
            
            # Linux fallback: Standard Downloads folder
            downloads_folder = Path.home() / "Downloads"
            if downloads_folder.exists():
                logger.info(f"Linux Downloads folder found via fallback: {downloads_folder}")
                return downloads_folder
                
    except Exception as e:
        logger.warning(f"Error detecting Downloads folder: {e}")
    
    # Ultimate fallback: Create "Svenska tidningar" in app directory
    app_dir = get_app_directory()
    fallback_folder = app_dir / "Svenska tidningar"
    logger.warning(f"Could not find user Downloads folder, using app directory fallback: {fallback_folder}")
    return fallback_folder

# Use absolute path for config file in app directory
def get_config_file_path():
    """Get the absolute path to the configuration file"""
    config_path = get_app_directory() / "djs_kb-maskin_settings.json"
    logger.debug(f"Config file path: {config_path}")
    return config_path

def load_config():
    """Load application configuration"""
    try:
        from .version import get_version
    except ImportError:
        from version import get_version
    
    # Get current version for settings validation
    current_version = get_version()
    
    # Get default download directory in user's Downloads folder - use absolute path
    user_downloads = get_user_downloads_folder()
    default_download_dir = user_downloads / "Svenska tidningar"
    
    logger.info(f"Loading configuration from user Downloads: {user_downloads}")
    logger.info(f"Default download directory: {default_download_dir}")
    logger.info(f"Current application version: {current_version}")
    
    default_config = {
        "_config_version": current_version,  # Track which version created this config
        "gmail_enabled": False,
        "kb_enabled": False,
        "gmail_account": "",
        "credentials_file": "",
        "sender_email": "noreply@kb.se",
        "start_date": "",
        "end_date": "",
        "gmail_output_dir": str(default_download_dir.resolve()),  # Always use absolute path
        "kb_output_dir": "",
        "keep_renamed": False,
        "update_settings": {
            "github_repo_owner": "Tripper99",  # TODO: Replace with actual GitHub username
            "github_repo_name": "DJs-KB-maskin",
            "check_on_startup": False,
            "last_check_date": None,
            "check_interval_days": 7,
            "skip_version": None,
            "auto_check_enabled": False
        }
    }
    
    config_file = get_config_file_path()
    logger.debug(f"Looking for config file at: {config_file}")
    
    if config_file.exists():
        try:
            logger.info(f"Loading existing configuration from: {config_file}")
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                
                # Check if configuration is from an older version
                config_version = config.get("_config_version", "unknown")
                if config_version != current_version:
                    logger.info(f"Configuration file is from version {config_version}, current version is {current_version}")
                    logger.info("Using default configuration to ensure compatibility with new version")
                    return default_config
                
                # Version matches, merge with defaults
                config = _deep_merge_config(default_config, config)
                logger.debug("Configuration loaded successfully")
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading config file: {e}, using defaults")
            return default_config
    else:
        logger.info("No existing configuration found, using defaults")
    
    return default_config


def _deep_merge_config(default_config, user_config):
    """
    Deep merge user configuration with defaults, ensuring all nested keys exist
    
    Args:
        default_config: Default configuration dictionary
        user_config: User's existing configuration dictionary
        
    Returns:
        Merged configuration with all default values preserved
    """
    result = user_config.copy()
    
    for key, default_value in default_config.items():
        if key not in result:
            # Key missing entirely, add default value
            result[key] = default_value
        elif isinstance(default_value, dict) and isinstance(result[key], dict):
            # Both are dictionaries, recursively merge
            result[key] = _deep_merge_config(default_value, result[key])
        # If key exists and is not a dict, keep user's value
    
    return result

def save_config(config):
    """Save application configuration"""
    try:
        from .version import get_version
    except ImportError:
        from version import get_version
    
    config_file = get_config_file_path()
    logger.debug(f"Saving configuration to: {config_file}")
    
    try:
        # Ensure the app directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Always update config version when saving
        config["_config_version"] = get_version()
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.debug("Configuration saved successfully")
    except IOError as e:
        logger.error(f"Could not save configuration to {config_file}: {e}")


def get_update_settings(config):
    """Get update settings from configuration"""
    return config.get("update_settings", {})


def set_update_setting(config, key, value):
    """Set a specific update setting"""
    if "update_settings" not in config:
        config["update_settings"] = {}
    config["update_settings"][key] = value


def set_github_repository(config, repo_owner, repo_name):
    """Set GitHub repository information"""
    set_update_setting(config, "github_repo_owner", repo_owner)
    set_update_setting(config, "github_repo_name", repo_name)


def set_skip_version(config, version):
    """Set version to skip"""
    set_update_setting(config, "skip_version", version)


def clear_skip_version(config):
    """Clear skipped version"""
    set_update_setting(config, "skip_version", None)


def should_check_for_updates(config):
    """Check if automatic update checking is enabled and due"""
    update_settings = get_update_settings(config)
    
    # Check if auto-check is enabled
    if not update_settings.get("auto_check_enabled", False):
        return False
        
    # Check if startup checking is enabled
    if not update_settings.get("check_on_startup", False):
        return False
        
    # Check interval
    last_check = update_settings.get("last_check_date")
    if not last_check:
        return True
        
    from datetime import datetime, timedelta
    try:
        last_check_date = datetime.fromisoformat(last_check)
        check_interval = update_settings.get("check_interval_days", 7)
        next_check_date = last_check_date + timedelta(days=check_interval)
        
        return datetime.now() >= next_check_date
    except (ValueError, TypeError):
        # Invalid date format, check anyway
        return True


def update_last_check_date(config):
    """Update the last check date to current time"""
    from datetime import datetime
    set_update_setting(config, "last_check_date", datetime.now().isoformat())