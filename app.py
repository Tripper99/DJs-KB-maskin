#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJs app för hantering av filer från "Svenska Tidningar" - Main Entry Point
dan@josefsson.net
Kod skriven med hjälp av Claude ai, Grok och Cursor.
"""

import datetime
import logging
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gui.main_window import CombinedApp

def setup_logging():
    """Setup logging to file in date-based subdirectories"""
    script_dir = Path(__file__).parent
    now = datetime.datetime.now()
    
    # Create logs directory with year-month subdirectory
    log_dir = script_dir / "logs" / now.strftime('%Y-%m')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_filename = log_dir / f"djs_kb_maskin_{now.strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return str(log_filename)

def main():
    """Main entry point"""
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== Starting DJs Svenska Tidningar app ===")
    logger.info(f"Log file: {log_file}")
    
    try:
        # Create and run the application
        app = CombinedApp()
        app.root.mainloop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()