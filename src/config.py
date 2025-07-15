# -*- coding: utf-8 -*-
"""
Configuration management for the DJs app
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = "combined_app_config.json"

def load_config():
    """Load application configuration"""
    default_config = {
        "gmail_enabled": False,
        "kb_enabled": False,
        "gmail_account": "",
        "credentials_file": "",
        "sender_email": "noreply@kb.se",
        "start_date": "",
        "end_date": "",
        "gmail_output_dir": str(Path.home() / "Downloads" / "Gmail-nedladdningar"),
        "excel_path": "",
        "kb_output_dir": "",
        "keep_renamed": False
    }
    
    if Path(CONFIG_FILE).exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (json.JSONDecodeError, IOError):
            return default_config
    return default_config

def save_config(config):
    """Save application configuration"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        logger.error(f"Could not save configuration: {e}")