# -*- coding: utf-8 -*-
"""
Configuration management for the DJs app
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = "djs_kb-maskin_settings.json"

def get_app_directory():
    """Get the directory where the application is located (works for both .py and .exe)"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return Path(sys.executable).parent
    else:
        # Running as Python script
        return Path(__file__).parent.parent

def load_config():
    """Load application configuration"""
    # Get default download directory in app folder
    app_dir = get_app_directory()
    default_download_dir = app_dir / "Nedladdningar"
    
    default_config = {
        "gmail_enabled": False,
        "kb_enabled": False,
        "gmail_account": "",
        "credentials_file": "",
        "sender_email": "noreply@kb.se",
        "start_date": "",
        "end_date": "",
        "gmail_output_dir": str(default_download_dir),
        "excel_path": "",
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
    
    if Path(CONFIG_FILE).exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Deep merge configuration with defaults
                config = _deep_merge_config(default_config, config)
                return config
        except (json.JSONDecodeError, IOError):
            return default_config
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
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        logger.error(f"Could not save configuration: {e}")


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