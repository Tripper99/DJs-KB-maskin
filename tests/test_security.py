#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for security modules
"""

import unittest
import tempfile
from pathlib import Path
import pandas as pd

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.security.path_validator import PathValidator
from src.security.secure_file_ops import SecureFileOps


class TestPathValidator(unittest.TestCase):
    """Test path validation functionality"""
    
    def setUp(self):
        self.validator = PathValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are blocked"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "test/../../../etc/hosts",
            "..\\test\\..\\..\\secret.txt",
            "./../../sensitive.txt"
        ]
        
        for dangerous_path in dangerous_paths:
            with self.subTest(path=dangerous_path):
                is_valid, error_msg, _ = self.validator.is_safe_path(
                    dangerous_path, must_exist=False
                )
                self.assertFalse(is_valid, f"Should reject path traversal: {dangerous_path}")
                self.assertIsNotNone(error_msg)
    
    def test_windows_reserved_names(self):
        """Test that Windows reserved names are handled"""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        
        for name in reserved_names:
            with self.subTest(name=name):
                sanitized = self.validator.sanitize_filename(name)
                self.assertNotEqual(sanitized.upper(), name.upper())
                self.assertTrue(sanitized.endswith('_safe'))
    
    def test_dangerous_characters_removal(self):
        """Test removal of dangerous characters"""
        dangerous_filenames = [
            "test<script>.txt",
            "file|pipe.doc", 
            'name"quote.pdf',
            "path\\injection.jpg",
            "null\x00byte.png"
        ]
        
        for filename in dangerous_filenames:
            with self.subTest(filename=filename):
                sanitized = self.validator.sanitize_filename(filename)
                # Should not contain original dangerous characters
                self.assertNotIn('<', sanitized)
                self.assertNotIn('|', sanitized)
                self.assertNotIn('"', sanitized)
                self.assertNotIn('\\', sanitized)
                self.assertNotIn('\x00', sanitized)
    
    def test_length_limits(self):
        """Test filename and path length limits"""
        # Very long filename
        long_filename = "a" * 300 + ".txt"
        sanitized = self.validator.sanitize_filename(long_filename)
        self.assertLessEqual(len(sanitized), 255)
        
        # Very long path
        long_path = "C:\\" + "\\".join(["verylongdirectoryname"] * 20) + "\\file.txt"
        is_valid, error_msg, _ = self.validator.is_safe_path(
            long_path, must_exist=False
        )
        self.assertFalse(is_valid)  # Should reject very long paths
    
    def test_unicode_normalization(self):
        """Test Unicode normalization against homograph attacks"""
        # Unicode characters that look similar to ASCII
        unicode_filename = "tеst.txt"  # Contains Cyrillic 'е' instead of 'e'
        sanitized = self.validator.sanitize_filename(unicode_filename)
        # Should be normalized and safe
        self.assertIsInstance(sanitized, str)
        self.assertTrue(len(sanitized) > 0)
    
    def test_excel_file_validation(self):
        """Test Excel file validation"""
        # Create a test Excel file
        test_excel = self.temp_path / "test.xlsx"
        df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})
        df.to_excel(test_excel, index=False)
        
        # Test valid Excel file
        is_valid, error_msg, safe_path = self.validator.validate_excel_path(str(test_excel))
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertEqual(safe_path, test_excel.resolve())
        
        # Test non-Excel file
        text_file = self.temp_path / "test.txt"
        text_file.write_text("not an excel file")
        
        is_valid, error_msg, _ = self.validator.validate_excel_path(str(text_file))
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
    
    def test_directory_validation(self):
        """Test directory validation and creation"""
        # Test existing directory
        is_valid, error_msg, safe_path = self.validator.validate_directory(
            str(self.temp_path), must_exist=True
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        
        # Test non-existing directory with creation
        new_dir = self.temp_path / "newdir"
        is_valid, error_msg, safe_path = self.validator.validate_directory(
            str(new_dir), must_exist=False, create_if_missing=True
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertTrue(new_dir.exists())
        
        # Test file instead of directory
        test_file = self.temp_path / "notadir.txt"
        test_file.write_text("test")
        
        is_valid, error_msg, _ = self.validator.validate_directory(
            str(test_file), must_exist=True
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)


class TestSecureFileOps(unittest.TestCase):
    """Test secure file operations"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.secure_ops = SecureFileOps()
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_secure_excel_reading(self):
        """Test secure Excel file reading"""
        # Create test Excel file
        test_excel = self.temp_path / "test.xlsx"
        test_data = pd.DataFrame({
            'bibcode': ['123', '456', '789'],
            'newspaper': ['Dagens Nyheter', 'Svenska Dagbladet', 'Aftonbladet']
        })
        test_data.to_excel(test_excel, index=False, header=False)
        
        # Test reading with secure ops
        df = self.secure_ops.read_excel(str(test_excel), header=None)
        self.assertEqual(len(df), 3)
        self.assertEqual(len(df.columns), 2)
        
        # Test invalid path should raise ValueError
        with self.assertRaises(ValueError):
            self.secure_ops.read_excel("../../../etc/passwd")
    
    def test_secure_file_saving(self):
        """Test secure file saving with sanitization"""
        # Test saving with dangerous filename
        dangerous_filename = "../../../malicious<script>.txt"
        content = "test content"
        
        saved_path = self.secure_ops.save_file(
            content=content,
            filename=dangerous_filename,
            output_dir=str(self.temp_path),
            binary=False
        )
        
        # Filename should be sanitized
        self.assertTrue(saved_path.exists())
        self.assertNotIn("..", saved_path.name)
        self.assertNotIn("<", saved_path.name)
        self.assertNotIn("script", saved_path.name)
        
        # Content should be correct
        self.assertEqual(saved_path.read_text(), content)
    
    def test_secure_subprocess_prevention(self):
        """Test subprocess security measures"""
        # Test that shell=True is blocked
        with self.assertRaises(ValueError):
            self.secure_ops.safe_subprocess_run(
                ["echo", "test"], shell=True
            )
        
        # Test file validation in subprocess
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        
        # This should work (though subprocess might fail based on system)
        try:
            result = self.secure_ops.safe_subprocess_run(
                ["echo", "test"], 
                file_arg=str(test_file),
                check=False  # Don't fail test if command doesn't exist
            )
        except (FileNotFoundError, OSError):
            # Command not found is OK for this test
            pass
        
        # Dangerous file path should be rejected
        with self.assertRaises(ValueError):
            self.secure_ops.safe_subprocess_run(
                ["echo", "test"],
                file_arg="../../../etc/passwd"
            )
    
    def test_glob_security(self):
        """Test secure file globbing"""
        # Create test files
        (self.temp_path / "test1.txt").write_text("test1")
        (self.temp_path / "test2.txt").write_text("test2")
        (self.temp_path / "other.doc").write_text("other")
        
        # Test normal globbing
        txt_files = self.secure_ops.glob_files(str(self.temp_path), "*.txt")
        self.assertEqual(len(txt_files), 2)
        
        # Test with invalid directory
        with self.assertRaises(ValueError):
            self.secure_ops.glob_files("../../../etc", "*")
    
    def test_temp_file_creation(self):
        """Test secure temporary file creation"""
        content = "temporary content"
        temp_file = self.secure_ops.create_temp_file(
            suffix="txt",
            prefix="test_",
            content=content,
            binary=False
        )
        
        self.assertTrue(temp_file.exists())
        self.assertEqual(temp_file.read_text(), content)
        self.assertTrue(temp_file.name.startswith("test_"))
        self.assertTrue(temp_file.name.endswith(".txt"))
        
        # Clean up
        temp_file.unlink()
    
    def test_file_copy_security(self):
        """Test secure file copying"""
        # Create source file
        source = self.temp_path / "source.txt"
        source.write_text("source content")
        
        # Test normal copy
        dest_dir = self.temp_path / "dest"
        dest_dir.mkdir()
        
        copied = self.secure_ops.copy_file(str(source), str(dest_dir))
        self.assertTrue(copied.exists())
        self.assertEqual(copied.read_text(), "source content")
        
        # Test with dangerous paths
        with self.assertRaises(ValueError):
            self.secure_ops.copy_file("../../../etc/passwd", str(dest_dir))
        
        with self.assertRaises(ValueError):
            self.secure_ops.copy_file(str(source), "../../../tmp")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)