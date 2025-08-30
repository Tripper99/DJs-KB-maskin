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
from src.security.network_validator import (
    NetworkValidator, NetworkSecurityError, URLValidationError, ResponseValidationError
)


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


class TestNetworkValidator(unittest.TestCase):
    """Test network security validation functionality"""
    
    def setUp(self):
        self.validator = NetworkValidator("testuser", "testrepo")
        
    def test_repository_validation(self):
        """Test repository owner and name validation"""
        # Test valid repository info
        validator = NetworkValidator("valid-user", "valid-repo")
        self.assertEqual(validator.repo_owner, "valid-user")
        self.assertEqual(validator.repo_name, "valid-repo")
        
        # Test invalid repository owner
        with self.assertRaises(URLValidationError):
            NetworkValidator("", "testrepo")
            
        with self.assertRaises(URLValidationError):
            NetworkValidator(".invalid", "testrepo")
            
        with self.assertRaises(URLValidationError):
            NetworkValidator("invalid.", "testrepo")
            
        with self.assertRaises(URLValidationError):
            NetworkValidator("a" * 40, "testrepo")  # Too long
            
        with self.assertRaises(URLValidationError):
            NetworkValidator("invalid/chars", "testrepo")
            
    def test_api_url_validation(self):
        """Test GitHub API URL validation"""
        # Valid URLs
        valid_urls = [
            "https://api.github.com/repos/testuser/testrepo/releases/latest",
            "https://api.github.com/repos/testuser/testrepo/releases",
            "https://api.github.com/repos/testuser/testrepo/releases/123"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.validator.validate_api_url(url))
                
        # Invalid URLs
        invalid_urls = [
            "http://api.github.com/repos/testuser/testrepo/releases/latest",  # HTTP
            "https://evil.com/repos/testuser/testrepo/releases/latest",  # Wrong domain
            "https://api.github.com/repos/otheruser/testrepo/releases/latest",  # Wrong user
            "https://api.github.com/repos/testuser/otherrepo/releases/latest",  # Wrong repo
            "https://api.github.com/repos/testuser/testrepo/issues",  # Wrong endpoint
            "",  # Empty
            "not-a-url",  # Not a URL
            "ftp://api.github.com/repos/testuser/testrepo/releases/latest"  # Wrong scheme
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(URLValidationError):
                    self.validator.validate_api_url(url)
                    
    def test_release_url_validation(self):
        """Test GitHub release page URL validation"""
        # Valid URLs
        valid_urls = [
            "https://github.com/testuser/testrepo/releases/tag/v1.0.0",
            "https://github.com/testuser/testrepo/releases",
            "https://github.com/testuser/testrepo/releases/latest"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.validator.validate_release_url(url))
                
        # Invalid URLs
        invalid_urls = [
            "http://github.com/testuser/testrepo/releases/tag/v1.0.0",  # HTTP
            "https://evil.com/testuser/testrepo/releases/tag/v1.0.0",  # Wrong domain
            "https://github.com/otheruser/testrepo/releases/tag/v1.0.0",  # Wrong user
            "https://github.com/testuser/otherrepo/releases/tag/v1.0.0",  # Wrong repo
            "",  # Empty
            "not-a-url"  # Not a URL
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(URLValidationError):
                    self.validator.validate_release_url(url)
                    
    def test_secure_request_config(self):
        """Test secure request configuration"""
        config = self.validator.get_secure_request_config()
        
        self.assertIsInstance(config, dict)
        self.assertEqual(config['timeout'], 10)
        self.assertTrue(config['verify'])
        self.assertFalse(config['allow_redirects'])
        self.assertIn('User-Agent', config['headers'])
        self.assertIn('Accept', config['headers'])
        
    def test_json_response_validation(self):
        """Test JSON response validation"""
        # Valid JSON
        valid_json = '{"key": "value", "number": 123}'
        result = self.validator.validate_json_response(valid_json)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 123)
        
        # Invalid JSON
        invalid_json = '{"key": "value", "invalid": '
        with self.assertRaises(ResponseValidationError):
            self.validator.validate_json_response(invalid_json)
            
        # Too large response
        large_json = '{"data": "' + "x" * 2000000 + '"}'
        with self.assertRaises(ResponseValidationError):
            self.validator.validate_json_response(large_json, max_size=1000)
            
        # Non-object JSON
        array_json = '["not", "an", "object"]'
        with self.assertRaises(ResponseValidationError):
            self.validator.validate_json_response(array_json)
            
    def test_release_data_validation(self):
        """Test GitHub release data validation"""
        # Valid release data
        valid_release = {
            "tag_name": "v1.0.0",
            "name": "Version 1.0.0",
            "html_url": "https://github.com/testuser/testrepo/releases/tag/v1.0.0",
            "published_at": "2023-01-01T00:00:00Z",
            "body": "Release notes",
            "assets": [
                {
                    "name": "app.exe",
                    "browser_download_url": "https://github.com/testuser/testrepo/releases/download/v1.0.0/app.exe",
                    "size": 1024
                }
            ]
        }
        
        result = self.validator.validate_release_data(valid_release)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["tag_name"], "v1.0.0")
        self.assertEqual(len(result["assets"]), 1)
        
        # Missing required fields
        incomplete_release = {"tag_name": "v1.0.0"}
        with self.assertRaises(ResponseValidationError):
            self.validator.validate_release_data(incomplete_release)
            
        # Invalid version format
        invalid_version_release = valid_release.copy()
        invalid_version_release["tag_name"] = "invalid-version"
        with self.assertRaises(ResponseValidationError):
            self.validator.validate_release_data(invalid_version_release)
            
        # Invalid HTML URL
        invalid_url_release = valid_release.copy()
        invalid_url_release["html_url"] = "https://evil.com/malicious"
        with self.assertRaises(ResponseValidationError):
            self.validator.validate_release_data(invalid_url_release)
            
    def test_asset_data_validation(self):
        """Test individual asset data validation"""
        # Valid asset
        valid_asset = {
            "name": "app.exe",
            "browser_download_url": "https://github.com/testuser/testrepo/releases/download/v1.0.0/app.exe",
            "size": 1024
        }
        
        result = self.validator._validate_asset_data(valid_asset)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "app.exe")
        
        # Missing required fields
        incomplete_asset = {"name": "app.exe"}
        result = self.validator._validate_asset_data(incomplete_asset)
        self.assertIsNone(result)
        
        # Invalid download URL
        invalid_url_asset = valid_asset.copy()
        invalid_url_asset["browser_download_url"] = "http://evil.com/malware"
        result = self.validator._validate_asset_data(invalid_url_asset)
        self.assertIsNone(result)
        
        # Invalid size
        invalid_size_asset = valid_asset.copy()
        invalid_size_asset["size"] = -1
        result = self.validator._validate_asset_data(invalid_size_asset)
        self.assertIsNone(result)
        
    def test_text_sanitization(self):
        """Test text sanitization for GUI display"""
        # Normal text
        normal_text = "Normal release notes"
        sanitized = self.validator.sanitize_display_text(normal_text)
        self.assertEqual(sanitized, normal_text)
        
        # Text with control characters
        control_text = "Text\x00with\x01control\x02chars"
        sanitized = self.validator.sanitize_display_text(control_text)
        self.assertNotIn('\x00', sanitized)
        self.assertNotIn('\x01', sanitized)
        self.assertNotIn('\x02', sanitized)
        
        # Text too long
        long_text = "x" * 2000
        sanitized = self.validator.sanitize_display_text(long_text, max_length=100)
        self.assertEqual(len(sanitized), 100)
        
        # Non-string input
        non_string = 12345
        sanitized = self.validator.sanitize_display_text(non_string, max_length=10)
        self.assertEqual(sanitized, "12345")
        
        # Text with allowed special characters
        special_text = "Text with\nnewlines\tand\rreturns"
        sanitized = self.validator.sanitize_display_text(special_text)
        self.assertIn('\n', sanitized)
        self.assertIn('\t', sanitized)
        self.assertIn('\r', sanitized)
        
    def test_version_pattern_matching(self):
        """Test version number pattern validation"""
        import re
        from src.security.network_validator import VERSION_PATTERN
        
        # Valid versions
        valid_versions = ["1.0.0", "v1.0.0", "2.15.7", "v10.0.1"]
        for version in valid_versions:
            with self.subTest(version=version):
                self.assertTrue(VERSION_PATTERN.match(version))
                
        # Invalid versions
        invalid_versions = [
            "1.0", "v1", "1.0.0-beta", "1.0.0.0", "v1.0.0-rc1", 
            "1.x.0", "a.b.c", "", "1.0.0-alpha"
        ]
        for version in invalid_versions:
            with self.subTest(version=version):
                self.assertIsNone(VERSION_PATTERN.match(version))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)