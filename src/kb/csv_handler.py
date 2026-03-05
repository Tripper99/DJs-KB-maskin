#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV handler for bib-code to newspaper name mapping
Replaces the Excel-based system with a simpler CSV approach
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class CSVHandler:
    """Handles reading and validation of CSV files containing bib-code mappings"""

    ALIAS_FILENAME = "titles_bibids_aliases.csv"

    def __init__(self):
        self.csv_pattern = "titles_bibids_*.csv"
        self.bib_dict: Dict[str, str] = {}
        self.alias_dict: Dict[str, str] = {}  # bib_code -> alias
        self.loaded_file: Optional[Path] = None
        self.alias_file: Optional[Path] = None
    
    def find_csv_file(self, app_directory: Path) -> Optional[Path]:
        """
        Find the most recent CSV file matching the pattern in the app directory
        
        Args:
            app_directory: The application directory to search in
            
        Returns:
            Path to the most recent CSV file, or None if not found
        """
        try:
            # Find all matching CSV files, excluding alias file
            csv_files = [f for f in app_directory.glob(self.csv_pattern)
                         if f.name != self.ALIAS_FILENAME]
            
            if not csv_files:
                logger.warning(f"No CSV files matching pattern '{self.csv_pattern}' found in {app_directory}")
                return None
            
            # Sort by filename (which includes date) to get the most recent
            csv_files.sort(reverse=True)
            most_recent = csv_files[0]
            
            logger.info(f"Found CSV file: {most_recent}")
            if len(csv_files) > 1:
                logger.info(f"Multiple CSV files found, using most recent: {most_recent.name}")
            
            return most_recent
            
        except Exception as e:
            logger.error(f"Error searching for CSV files: {e}")
            return None
    
    def validate_csv_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate that the CSV file has the correct format
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not file_path.exists():
                return False, "CSV-filen existerar inte"
            
            if not file_path.is_file():
                return False, "Sökvägen är inte en fil"
            
            # Check file size (reasonable limit: 10MB)
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                return False, f"CSV-filen är för stor ({file_size / 1024 / 1024:.1f} MB)"
            
            if file_size == 0:
                return False, "CSV-filen är tom"
            
            # Try to read first few lines to validate format
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                
                if not first_row:
                    return False, "CSV-filen innehåller inga rader"
                
                if len(first_row) != 2:
                    return False, f"CSV-filen måste ha exakt 2 kolumner (tidningsnamn, bib-kod), hittade {len(first_row)}"
                
                # Check a few more rows
                row_count = 1
                for _ in range(5):  # Check up to 5 more rows
                    row = next(reader, None)
                    if row is None:
                        break
                    if len(row) != 2:
                        return False, f"Rad {row_count + 1} har fel antal kolumner"
                    row_count += 1
            
            return True, "CSV-filen validerad"
            
        except UnicodeDecodeError:
            return False, "CSV-filen har fel teckenkodning (måste vara UTF-8)"
        except csv.Error as e:
            return False, f"CSV-formatfel: {str(e)}"
        except Exception as e:
            return False, f"Fel vid validering av CSV-fil: {str(e)}"
    
    def load_csv_file(self, file_path: Path) -> Tuple[bool, str, int]:
        """
        Load the CSV file and create the bib-code dictionary
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (success, message, count)
        """
        try:
            # First validate the file
            is_valid, msg = self.validate_csv_file(file_path)
            if not is_valid:
                return False, msg, 0
            
            # Clear existing dictionary
            self.bib_dict.clear()
            
            # Load the CSV file
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                for row_num, row in enumerate(reader, 1):
                    if len(row) != 2:
                        logger.warning(f"Skipping row {row_num}: incorrect number of columns")
                        continue
                    
                    newspaper_name, bib_code = row
                    
                    # Clean up the values (remove extra whitespace)
                    newspaper_name = newspaper_name.strip()
                    bib_code = bib_code.strip()
                    
                    if not newspaper_name or not bib_code:
                        logger.warning(f"Skipping row {row_num}: empty newspaper name or bib-code")
                        continue
                    
                    # Note: CSV has newspaper name first, bib-code second
                    # But we store as bib-code -> newspaper name for lookup
                    self.bib_dict[bib_code] = newspaper_name
            
            self.loaded_file = file_path
            count = len(self.bib_dict)
            
            logger.info(f"Loaded {count} bib-codes from CSV file")
            return True, f"Laddade {count} bib-koder från CSV-filen", count
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return False, f"Kunde inte ladda CSV-filen: {str(e)}", 0
    
    def get_newspaper_name(self, bib_code: str) -> Optional[str]:
        """
        Get the newspaper name for a given bib-code
        
        Args:
            bib_code: The bib-code to look up
            
        Returns:
            The newspaper name, or None if not found
        """
        return self.bib_dict.get(bib_code.strip())
    
    def is_loaded(self) -> bool:
        """Check if a CSV file has been loaded"""
        return bool(self.bib_dict) and self.loaded_file is not None
    
    def get_loaded_filename(self) -> Optional[str]:
        """Get the name of the currently loaded CSV file"""
        if self.loaded_file:
            return self.loaded_file.name
        return None
    
    def get_bib_code_count(self) -> int:
        """Get the number of loaded bib-codes"""
        return len(self.bib_dict)

    def load_alias_file(self, app_directory: Path) -> Tuple[bool, str, int]:
        """
        Load the alias CSV file (titles_bibids_aliases.csv) from app directory.

        The file has 3 columns: Tidningsnamn, bib-kod, alias
        Builds alias_dict: bib_code -> alias

        Returns:
            Tuple of (success, message, count)
        """
        self.alias_dict.clear()
        self.alias_file = None

        alias_path = app_directory / self.ALIAS_FILENAME
        if not alias_path.exists():
            logger.info(f"No alias file found at {alias_path}")
            return False, "Ingen alias-fil hittades", 0

        try:
            with open(alias_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)

                if not header or len(header) < 3:
                    return False, "Alias-filen har fel format (behöver 3 kolumner)", 0

                for row_num, row in enumerate(reader, 2):
                    if len(row) < 3:
                        logger.warning(f"Alias file: skipping row {row_num} with {len(row)} columns")
                        continue

                    _newspaper_name, bib_code, alias = row[0], row[1].strip(), row[2].strip()

                    if bib_code and alias:
                        self.alias_dict[bib_code] = alias

            self.alias_file = alias_path
            count = len(self.alias_dict)
            logger.info(f"Loaded {count} aliases from {alias_path.name}")
            return True, f"Laddade {count} alias från {alias_path.name}", count

        except Exception as e:
            logger.error(f"Error loading alias file: {e}")
            return False, f"Kunde inte ladda alias-filen: {str(e)}", 0

    def get_display_name(self, bib_code: str, use_alias: bool = False) -> str:
        """
        Get the display name for a bib-code, optionally using alias.

        Returns alias if use_alias=True and alias exists, otherwise full newspaper name.
        Returns "OKÄND" if bib-code not found at all.
        """
        bib_code = bib_code.strip()
        if use_alias and bib_code in self.alias_dict:
            return self.alias_dict[bib_code]
        return self.bib_dict.get(bib_code, "OKÄND")

    def is_alias_loaded(self) -> bool:
        """Check if alias file has been loaded"""
        return bool(self.alias_dict) and self.alias_file is not None