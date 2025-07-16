# -*- coding: utf-8 -*-
"""
KB file processing functionality
"""

import logging
import os
import re
import shutil
import tempfile
import tkinter as tk
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from PIL import Image
    import pandas as pd
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

logger = logging.getLogger(__name__)

class KBProcessor:
    def __init__(self):
        self.cancel_requested = False  # Keep for backward compatibility
        self.cancel_event = None  # Will be set by GUI
        self.root = None  # Reference to root window for dialogs
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and invalid characters"""
        # Remove or replace dangerous characters
        # Keep Swedish characters and common punctuation
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\.\.+', '.', filename)  # Replace multiple dots
        filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
        
        # Ensure filename is not empty and not too long
        if not filename:
            filename = "unnamed"
        if len(filename) > 200:  # Reasonable limit
            filename = filename[:200]
        
        return filename
    
    def validate_image_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validate that a file is a valid image"""
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                return False, "PIL inte tillgängligt"
            
            # Check file size (reasonable limit: 100MB)
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                return False, f"Filen är för stor ({file_size / 1024 / 1024:.1f} MB)"
            
            # Try to open and verify the image
            with Image.open(file_path) as img:
                # Verify image format
                if img.format not in ['JPEG', 'JPG', 'PNG', 'BMP', 'TIFF']:
                    return False, f"Bildformat '{img.format}' stöds inte"
                
                # Check image dimensions (reasonable limit: 50MP)
                width, height = img.size
                if width * height > 50 * 1024 * 1024:  # 50 megapixels
                    return False, f"Bilden är för stor ({width}x{height} pixlar)"
                
                # Try to load image data to verify it's not corrupted
                # Use load() instead of verify() to avoid destroying the image
                img.load()
                
                return True, "Giltig bildfil"
                
        except Exception as e:
            return False, f"Ogiltig bildfil: {str(e)}"
    
    def load_image_safely(self, file_path: Path) -> Image.Image:
        """Load an image with proper resource management"""
        img = Image.open(file_path)
        # Convert to RGB if needed and return a copy to avoid issues with file handles
        if img.mode != 'RGB':
            rgb_img = img.convert('RGB')
            img.close()  # Close original
            return rgb_img
        else:
            # Create a copy to avoid file handle issues
            img_copy = img.copy()
            img.close()  # Close original
            return img_copy
    
    def process_images_in_batches(self, file_paths: List[Path], batch_size: int = 10):
        """Process images in batches to manage memory usage"""
        MAX_BATCH_SIZE = 10  # Limit batch size to prevent memory issues
        actual_batch_size = min(batch_size, MAX_BATCH_SIZE)
        
        for i in range(0, len(file_paths), actual_batch_size):
            if self.is_cancelled():
                break
                
            batch = file_paths[i:i + actual_batch_size]
            images = []
            
            try:
                # Load batch of images
                for file_path in batch:
                    if self.is_cancelled():
                        break
                    images.append(self.load_image_safely(file_path))
                
                yield images
                
            finally:
                # Clean up batch images
                for img in images:
                    try:
                        img.close()
                    except:
                        pass
    
    @contextmanager
    def temporary_directory(self, output_path: Path, keep_renamed: bool):
        """Context manager for temporary directory handling"""
        if keep_renamed:
            temp_path = output_path / "Jpg-filer med fina namn"
            temp_path.mkdir(parents=True, exist_ok=True)
            yield temp_path
            # No cleanup needed for permanent directory
        else:
            temp_path = Path(tempfile.mkdtemp(prefix="renamed_jpgs_"))
            try:
                yield temp_path
            finally:
                # Always cleanup temporary directory
                try:
                    shutil.rmtree(temp_path, ignore_errors=True)
                    logger.info("Cleaned up temporary files")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp files: {e}")
    
    def set_root(self, root: tk.Tk):
        """Set the root window for dialog purposes"""
        self.root = root
    
    def cancel_operation(self):
        self.cancel_requested = True
        if self.cancel_event:
            self.cancel_event.set()
    
    def reset_cancel_state(self):
        self.cancel_requested = False
        if self.cancel_event:
            self.cancel_event.clear()
    
    def is_cancelled(self):
        """Check if operation has been cancelled"""
        if self.cancel_event and self.cancel_event.is_set():
            return True
        return self.cancel_requested
    
    def validate_excel_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate Excel file format and content"""
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                return False, "Pandas inte installerat - KB-funktionalitet inte tillgänglig"
            
            df = pd.read_excel(file_path, header=None)
            
            if df.shape[1] < 2:
                return False, "Excel-filen måste ha minst 2 kolumner (bib-kod och tidningsnamn)"
            
            if df.shape[0] == 0:
                return False, "Excel-filen är tom"
            
            return True, f"Excel-filen validerad: {len(df)} bib-koder hittades"
            
        except Exception as e:
            return False, f"Fel vid läsning av Excel-fil: {str(e)}"
    
    def validate_directories(self, input_dir: str, output_dir: str) -> Tuple[bool, List[str]]:
        """Validate input and output directories"""
        errors = []
        
        if not input_dir or not os.path.exists(input_dir):
            errors.append("Input-mappen existerar inte")
        
        if not output_dir:
            errors.append("Output-mapp måste väljas")
        else:
            try:
                os.makedirs(output_dir, exist_ok=True)
                if not os.access(output_dir, os.W_OK):
                    errors.append("Output-mappen kan inte skrivas till")
            except Exception as e:
                errors.append(f"Kan inte skapa/komma åt output-mappen: {str(e)}")
        
        return len(errors) == 0, errors
    
    def process_files(self, excel_path: str, input_dir: str, output_dir: str, 
                     keep_renamed: bool = False, delete_originals: bool = True,
                     progress_callback=None, gui_update_callback=None) -> Dict:
        """Process KB files - real implementation"""
        self.reset_cancel_state()
        
        try:
            if not IMAGE_PROCESSING_AVAILABLE:
                raise Exception("PIL/Pandas inte installerat - KB-funktionalitet inte tillgänglig")
            
            logger.info(f"=== Starting KB processing ===")
            logger.info(f"Excel file: {excel_path}")
            logger.info(f"Input dir: {input_dir}")
            logger.info(f"Output dir: {output_dir}")
            logger.info(f"Keep renamed: {keep_renamed}")
            logger.info(f"Delete originals: {delete_originals}")
            
            # Load Excel file
            if progress_callback:
                progress_callback("Läser Excel-fil...", 2)
            if gui_update_callback:
                gui_update_callback()
            
            try:
                bib_df = pd.read_excel(excel_path, header=None)
                bib_dict = dict(zip(bib_df[0].astype(str), bib_df[1].astype(str)))
                logger.info(f"Loaded {len(bib_dict)} bib codes from Excel")
            except Exception as e:
                raise Exception(f"Kunde inte läsa Excel-filen: {str(e)}")
            
            # Setup directories
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Find JPG files
            jpg_files = sorted(f for f in input_path.glob("*.jpg") if f.is_file())
            
            if not jpg_files:
                return {
                    "total_files": 0,
                    "created_count": 0,
                    "error": "Inga JPG-filer hittades"
                }
            
            logger.info(f"Found {len(jpg_files)} JPG files to process")
            
            # Setup temporary directory (with manual cleanup)
            if keep_renamed:
                temp_path = output_path / "Jpg-filer med fina namn"
                temp_path.mkdir(parents=True, exist_ok=True)
                cleanup_temp = False
            else:
                temp_path = Path(tempfile.mkdtemp(prefix="renamed_jpgs_"))
                cleanup_temp = True
            
            try:
                
                # Phase 1: Rename files
                if progress_callback:
                    progress_callback("Fas 1: Döper om filer...", 5)
                if gui_update_callback:
                    gui_update_callback()
                
                renamed_files = []
                total_files = len(jpg_files)
                unknown_bib_codes = set()  # Track unknown bib codes
            
                for i, file in enumerate(jpg_files):
                    if self.is_cancelled():
                        return {"cancelled": True}
                    
                    # Update progress for renaming phase with percentage
                    rename_progress = 5 + int((i / total_files) * 30)  # 5-35%
                    percentage = int(((i + 1) / total_files) * 100)
                    if progress_callback:
                        progress_callback(f"Döper om fil {i+1}/{total_files} ({percentage}%): {file.name}", rename_progress)
                    if gui_update_callback:
                        gui_update_callback()
                    
                    # Validate image file
                    is_valid, validation_message = self.validate_image_file(file)
                    if not is_valid:
                        logger.warning(f"Skipping invalid image {file.name}: {validation_message}")
                        continue
                    
                    stem = file.stem
                    suffix = file.suffix
                    extra = ""
                    
                    # Handle duplicate numbering in parentheses
                    if "(" in stem and ")" in stem[-3:]:
                        base, extra = stem.rsplit("(", 1)
                        extra = "(" + extra
                        stem = base.strip("_ ")
                    
                    parts = stem.split("_")
                    if len(parts) < 5:
                        logger.warning(f"Skipping file with unexpected format: {file.name}")
                        continue
                    
                    bib = parts[0]
                    date_raw = parts[1]
                    
                    # Format date
                    try:
                        date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
                    except:
                        date = "0000-00-00"
                        logger.warning(f"Could not parse date from: {date_raw}")
                    
                    siffergrupper = "_".join(parts[2:5])
                    tidning = bib_dict.get(bib, "OKÄND").upper()
                    
                    # Track unknown bib codes
                    if tidning == "OKÄND":
                        unknown_bib_codes.add(bib)
                    
                    # Create new filename with bib code included - for OKÄND files, include the bib code
                    if tidning == "OKÄND":
                        new_name = f"{date} {tidning} {bib} {siffergrupper}{extra}{suffix}"
                    else:
                        new_name = f"{date} {tidning} {bib} {siffergrupper}{extra}{suffix}"
                    
                    # Sanitize filename for security
                    new_name = self.sanitize_filename(new_name)
                    dest = temp_path / new_name
                    
                    try:
                        if delete_originals:
                            # Move (rename) the file instead of copying
                            shutil.move(str(file), str(dest))
                            logger.debug(f"Moved and renamed: {file.name} -> {new_name}")
                        else:
                            # Copy the file, keeping original
                            shutil.copy(file, dest)
                            logger.debug(f"Copied and renamed: {file.name} -> {new_name}")
                        renamed_files.append(dest)
                    except Exception as e:
                        logger.error(f"Failed to {'move' if delete_originals else 'copy'} {file.name}: {e}")
                        continue
                
                logger.info(f"Successfully renamed {len(renamed_files)} files")
            
                # Group files for PDF creation
                if progress_callback:
                    progress_callback("Grupperar filer för PDF-skapande...", 35)
                if gui_update_callback:
                    gui_update_callback()
                
                grouped = {}
                for f in renamed_files:
                    parts = f.stem.split()
                    if len(parts) < 4:  # date, newspaper, bib, numbers
                        logger.warning(f"Unexpected renamed file format: {f.name}")
                        continue
                    
                    # For OKÄND files, include bib code in grouping key
                    if parts[1] == "OKÄND":
                        # Group by date, newspaper, and bib code for OKÄND files
                        key = (parts[0], f"{parts[1]} {parts[2]}")
                    else:
                        # Group by date and newspaper (excluding bib and numbers)
                        key = (parts[0], " ".join(parts[1:-2]))
                    grouped.setdefault(key, []).append(f)
                
                logger.info(f"Grouped {len(renamed_files)} files into {len(grouped)} PDF groups")
            
                # Phase 2: Create PDFs
                created_count = 0
                overwritten_count = 0
                skipped_count = 0
                pdfs_per_tidning = defaultdict(int)
                
                total_pdfs = len(grouped)
                
                for pdf_num, ((date, newspaper), files) in enumerate(grouped.items(), 1):
                    if self.is_cancelled():
                        return {"cancelled": True}
                    
                    # Update progress for PDF creation phase with percentage
                    pdf_progress = 35 + int((pdf_num / total_pdfs) * 60)  # 35-95%
                    percentage = int((pdf_num / total_pdfs) * 100)
                    if progress_callback:
                        progress_callback(f"Skapar PDF {pdf_num}/{total_pdfs} ({percentage}%): {newspaper}", pdf_progress)
                    if gui_update_callback:
                        gui_update_callback()
                    
                    if not files:
                        continue
                    
                    # Sort files for consistent ordering
                    sorted_files = sorted(files)
                    
                    # Pre-validate files to get accurate page count
                    valid_files_count = 0
                    for img_file in sorted_files:
                        is_valid, _ = self.validate_image_file(img_file)
                        if is_valid:
                            valid_files_count += 1
                    
                    # Skip if no valid files
                    if valid_files_count == 0:
                        logger.warning(f"No valid images found for group {date} {newspaper}")
                        continue
                    
                    # Determine PDF filename - always include page count
                    pdf_name = f"{date} {newspaper} ({valid_files_count} sid).pdf"
                    
                    # Sanitize PDF filename for security
                    pdf_name = self.sanitize_filename(pdf_name)
                    pdf_path = output_path / pdf_name
                
                    # Handle existing PDF files with dialog
                    if pdf_path.exists():
                        # Show dialog for PDF file conflict
                        dialog = tk.Toplevel(self.root)
                        dialog.title("PDF-filkonflikt")
                        dialog.geometry("500x400")
                        dialog.transient(self.root)
                        dialog.grab_set()
                        dialog.lift()
                        dialog.focus_force()
                        dialog.attributes('-topmost', True)
                        dialog.after(100, lambda: dialog.attributes('-topmost', False))
                        
                        # Center the dialog
                        dialog.update_idletasks()
                        x = (dialog.winfo_screenwidth() // 2) - (250)
                        y = (dialog.winfo_screenheight() // 2) - (200)
                        dialog.geometry(f"500x400+{x}+{y}")
                        
                        tk.Label(dialog, text=f"PDF-filen {pdf_name} finns redan.\nVad vill du göra?", 
                                font=("Arial", 12)).pack(pady=20)
                    
                        # Variables for dialog result
                        dialog_result = {"action": None}
                        
                        def set_overwrite():
                            dialog_result["action"] = "overwrite"
                            dialog.destroy()
                        
                        def set_overwrite_all():
                            dialog_result["action"] = "overwrite_all"
                            dialog.destroy()
                        
                        def set_skip():
                            dialog_result["action"] = "skip"
                            dialog.destroy()
                        
                        def set_skip_all():
                            dialog_result["action"] = "skip_all"
                            dialog.destroy()
                        
                        def set_cancel():
                            dialog_result["action"] = "cancel"
                            dialog.destroy()
                        
                        # Button frame for better layout
                        button_frame = tk.Frame(dialog)
                        button_frame.pack(pady=20)
                        
                        tk.Button(button_frame, text="Skriv över", command=set_overwrite, 
                                 width=15, font=("Arial", 10)).pack(pady=3)
                        tk.Button(button_frame, text="Skriv över alla", command=set_overwrite_all, 
                                 width=15, font=("Arial", 10)).pack(pady=3)
                        tk.Button(button_frame, text="Hoppa över", command=set_skip, 
                                 width=15, font=("Arial", 10)).pack(pady=3)
                        tk.Button(button_frame, text="Hoppa över alla", command=set_skip_all, 
                                 width=15, font=("Arial", 10)).pack(pady=3)
                        tk.Button(button_frame, text="Avbryt", command=set_cancel, 
                                 width=15, font=("Arial", 10)).pack(pady=3)
                        
                        # Wait for dialog result
                        dialog.wait_window()
                    
                        # Handle dialog result
                        if dialog_result["action"] == "cancel":
                            return {"cancelled": True}
                        elif dialog_result["action"] == "skip":
                            skipped_count += 1
                            logger.info(f"Skipped existing PDF: {pdf_name}")
                            continue
                        elif dialog_result["action"] == "skip_all":
                            # Skip all remaining PDFs
                            for remaining_pdf in grouped.items():
                                if remaining_pdf[0] != (date, newspaper):
                                    skipped_count += 1
                            logger.info(f"Skipping all remaining PDFs")
                            break
                        elif dialog_result["action"] == "overwrite_all":
                            # Overwrite all remaining PDFs
                            overwritten_count += 1
                            logger.info(f"Overwriting existing PDF: {pdf_name}")
                        else:  # overwrite
                            overwritten_count += 1
                            logger.info(f"Overwriting existing PDF: {pdf_name}")
                    else:
                        created_count += 1
                
                    # Validate all images before processing
                    valid_files = []
                    for img_file in sorted_files:
                        is_valid, validation_message = self.validate_image_file(img_file)
                        if not is_valid:
                            logger.error(f"Invalid image in PDF group {pdf_name}: {img_file.name} - {validation_message}")
                        else:
                            valid_files.append(img_file)
                    
                    # Skip PDF creation if no valid files
                    if valid_files:
                        # Create PDF using PIL
                        try:
                            # Load first image safely
                            first_img = self.load_image_safely(valid_files[0])
                        
                            try:
                                # Load additional images safely
                                additional_images = []
                                for f in valid_files[1:]:
                                    if self.is_cancelled():
                                        break
                                    additional_images.append(self.load_image_safely(f))
                                
                                # Create PDF with proper resource management
                                first_img.save(
                                    pdf_path,
                                    save_all=True,
                                    append_images=additional_images
                                )
                            finally:
                                # Clean up image resources
                                first_img.close()
                                for img in additional_images:
                                    img.close()
                        
                            pdfs_per_tidning[newspaper] += 1
                            logger.info(f"Created PDF: {pdf_name} ({len(valid_files)} pages)")
                            
                        except Exception as e:
                            logger.error(f"Failed to create PDF {pdf_name}: {e}")
                    else:
                        logger.error(f"No valid images found for PDF {pdf_name}")
            
                # Cleanup is handled by context manager
                if progress_callback:
                    progress_callback("KB-bearbetning slutförd!", 100)
                if gui_update_callback:
                    gui_update_callback()
                
                result = {
                    "total_files": len(jpg_files),
                    "created_count": created_count,
                    "overwritten_count": overwritten_count,
                    "skipped_count": skipped_count,
                    "pdfs_per_tidning": dict(pdfs_per_tidning),
                    "output_path": str(output_path.absolute()),
                    "unknown_bib_codes": list(unknown_bib_codes),
                    "unknown_bib_count": len(unknown_bib_codes)
                }
                
                logger.info(f"KB processing completed successfully: {result}")
                return result
            finally:
                # Cleanup temporary directory if needed
                if cleanup_temp:
                    try:
                        shutil.rmtree(temp_path, ignore_errors=True)
                        logger.info("Cleaned up temporary files")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp files: {e}")
            
        except Exception as e:
            logger.error(f"KB processing error: {e}")
            raise Exception(f"KB processing error: {str(e)}")