#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network security validation module for update system
Provides secure URL validation, JSON parsing, and network request controls
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RELEASE_BASE = "https://github.com"
ALLOWED_GITHUB_DOMAINS = ["api.github.com", "github.com"]

# Security limits
MAX_JSON_RESPONSE_SIZE = 1024 * 1024  # 1MB
MAX_REQUEST_TIMEOUT = 10  # seconds
MAX_VERSION_LENGTH = 20
MAX_RELEASE_NOTES_LENGTH = 5000
MAX_ASSET_NAME_LENGTH = 100

# Version number validation pattern (semantic versioning)
VERSION_PATTERN = re.compile(r'^v?\d+\.\d+\.\d+$')

# GitHub release URL patterns
GITHUB_RELEASE_URL_PATTERN = re.compile(
    r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/releases(/tag/[a-zA-Z0-9_.-]+|/latest)?/?$'
)
GITHUB_API_RELEASES_PATTERN = re.compile(
    r'^https://api\.github\.com/repos/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/releases(/latest|/\d+)?$'
)


class NetworkSecurityError(Exception):
    """Base exception for network security violations"""
    pass


class URLValidationError(NetworkSecurityError):
    """URL validation failed"""
    pass


class ResponseValidationError(NetworkSecurityError):
    """Response validation failed"""
    pass


class NetworkValidator:
    """Secure network operations validator for update system"""
    
    def __init__(self, repo_owner: str, repo_name: str):
        """
        Initialize network validator for specific GitHub repository
        
        Args:
            repo_owner: GitHub repository owner/organization
            repo_name: GitHub repository name
        """
        self.repo_owner = self._validate_repo_component(repo_owner, "owner")
        self.repo_name = self._validate_repo_component(repo_name, "name")
        self.allowed_api_url = f"{GITHUB_API_BASE}/repos/{self.repo_owner}/{self.repo_name}/releases"
        self.allowed_release_base = f"{GITHUB_RELEASE_BASE}/{self.repo_owner}/{self.repo_name}/releases"
        
    def _validate_repo_component(self, component: str, component_type: str) -> str:
        """Validate GitHub repository owner/name component"""
        if not component or not isinstance(component, str):
            raise URLValidationError(f"Repository {component_type} must be a non-empty string")
            
        if len(component) > 39:  # GitHub limit
            raise URLValidationError(f"Repository {component_type} too long (max 39 characters)")
            
        if not re.match(r'^[a-zA-Z0-9_.-]+$', component):
            raise URLValidationError(f"Repository {component_type} contains invalid characters")
            
        if component.startswith('.') or component.endswith('.'):
            raise URLValidationError(f"Repository {component_type} cannot start or end with dot")
            
        return component
        
    def validate_api_url(self, url: str) -> bool:
        """
        Validate GitHub API URL for release checking
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid
            
        Raises:
            URLValidationError: If URL is invalid or not allowed
        """
        if not url or not isinstance(url, str):
            raise URLValidationError("URL must be a non-empty string")
            
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise URLValidationError(f"Failed to parse URL: {e}")
            
        # Check scheme
        if parsed.scheme != 'https':
            raise URLValidationError("Only HTTPS URLs are allowed")
            
        # Check domain
        if parsed.netloc not in ALLOWED_GITHUB_DOMAINS:
            raise URLValidationError(f"Domain not in allowlist: {parsed.netloc}")
            
        # Validate against expected patterns
        if not GITHUB_API_RELEASES_PATTERN.match(url):
            raise URLValidationError("URL does not match expected GitHub API releases pattern")
            
        # Ensure URL belongs to our repository
        expected_path_prefix = f"/repos/{self.repo_owner}/{self.repo_name}/releases"
        if not parsed.path.startswith(expected_path_prefix):
            raise URLValidationError(f"URL does not belong to expected repository: {self.repo_owner}/{self.repo_name}")
            
        return True
        
    def validate_release_url(self, url: str) -> bool:
        """
        Validate GitHub release page URL for browser opening
        
        Args:
            url: Release page URL to validate
            
        Returns:
            True if valid
            
        Raises:
            URLValidationError: If URL is invalid or not allowed
        """
        if not url or not isinstance(url, str):
            raise URLValidationError("URL must be a non-empty string")
            
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise URLValidationError(f"Failed to parse URL: {e}")
            
        # Check scheme
        if parsed.scheme != 'https':
            raise URLValidationError("Only HTTPS URLs are allowed")
            
        # Check domain
        if parsed.netloc != 'github.com':
            raise URLValidationError(f"Only github.com domain allowed for release URLs: {parsed.netloc}")
            
        # Validate against expected pattern
        if not GITHUB_RELEASE_URL_PATTERN.match(url):
            raise URLValidationError("URL does not match expected GitHub release page pattern")
            
        # Ensure URL belongs to our repository
        expected_path_prefix = f"/{self.repo_owner}/{self.repo_name}/releases"
        if not parsed.path.startswith(expected_path_prefix):
            raise URLValidationError(f"URL does not belong to expected repository: {self.repo_owner}/{self.repo_name}")
            
        return True
        
    def get_secure_request_config(self) -> Dict[str, Any]:
        """
        Get secure configuration for HTTP requests
        
        Returns:
            Dictionary with secure request configuration
        """
        return {
            'timeout': MAX_REQUEST_TIMEOUT,
            'verify': True,  # Verify SSL certificates
            'allow_redirects': False,  # No automatic redirects
            'headers': {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'DJs-KB-maskin-UpdateChecker/1.0'
            }
        }
        
    def validate_json_response(self, response_text: str, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Safely parse and validate JSON response from GitHub API
        
        Args:
            response_text: Raw response text
            max_size: Maximum allowed response size (default: MAX_JSON_RESPONSE_SIZE)
            
        Returns:
            Parsed and validated JSON data
            
        Raises:
            ResponseValidationError: If response is invalid or dangerous
        """
        if max_size is None:
            max_size = MAX_JSON_RESPONSE_SIZE
            
        # Check response size
        if len(response_text) > max_size:
            raise ResponseValidationError(f"Response too large: {len(response_text)} bytes (max {max_size})")
            
        # Parse JSON safely
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ResponseValidationError(f"Invalid JSON response: {e}")
            
        if not isinstance(data, dict):
            raise ResponseValidationError("Response must be a JSON object")
            
        return data
        
    def validate_release_data(self, release_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate GitHub release data structure and content
        
        Args:
            release_data: Parsed release data from GitHub API
            
        Returns:
            Validated release data
            
        Raises:
            ResponseValidationError: If release data is invalid
        """
        required_fields = ['tag_name', 'name', 'html_url', 'assets', 'published_at']
        
        # Check required fields
        for field in required_fields:
            if field not in release_data:
                raise ResponseValidationError(f"Missing required field: {field}")
                
        # Validate tag_name (version)
        tag_name = release_data.get('tag_name', '')
        if not isinstance(tag_name, str) or len(tag_name) > MAX_VERSION_LENGTH:
            raise ResponseValidationError("Invalid tag_name field")
            
        if not VERSION_PATTERN.match(tag_name):
            raise ResponseValidationError(f"Invalid version format: {tag_name}")
            
        # Validate release name
        name = release_data.get('name', '')
        if not isinstance(name, str) or len(name) > MAX_VERSION_LENGTH * 2:
            raise ResponseValidationError("Invalid name field")
            
        # Validate HTML URL
        html_url = release_data.get('html_url', '')
        if html_url:
            try:
                self.validate_release_url(html_url)
            except URLValidationError as e:
                raise ResponseValidationError(f"Invalid release URL: {e}")
                
        # Validate release notes (body)
        body = release_data.get('body', '')
        if body and (not isinstance(body, str) or len(body) > MAX_RELEASE_NOTES_LENGTH):
            raise ResponseValidationError("Invalid or too long release notes")
            
        # Validate assets
        assets = release_data.get('assets', [])
        if not isinstance(assets, list):
            raise ResponseValidationError("Assets must be a list")
            
        validated_assets = []
        for asset in assets:
            if isinstance(asset, dict):
                validated_asset = self._validate_asset_data(asset)
                if validated_asset:
                    validated_assets.append(validated_asset)
                    
        release_data['assets'] = validated_assets
        
        return release_data
        
    def _validate_asset_data(self, asset_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate individual asset data"""
        required_asset_fields = ['name', 'browser_download_url', 'size']
        
        # Check required fields
        for field in required_asset_fields:
            if field not in asset_data:
                logger.warning(f"Asset missing required field: {field}")
                return None
                
        # Validate asset name
        name = asset_data.get('name', '')
        if not isinstance(name, str) or len(name) > MAX_ASSET_NAME_LENGTH:
            logger.warning(f"Invalid asset name: {name}")
            return None
            
        # Validate download URL
        download_url = asset_data.get('browser_download_url', '')
        if not isinstance(download_url, str) or not download_url.startswith('https://'):
            logger.warning(f"Invalid asset download URL: {download_url}")
            return None
            
        # Validate size
        size = asset_data.get('size', 0)
        if not isinstance(size, int) or size < 0:
            logger.warning(f"Invalid asset size: {size}")
            return None
            
        return {
            'name': name,
            'browser_download_url': download_url,
            'size': size
        }
        
    def sanitize_display_text(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize text for safe display in GUI
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text safe for display
        """
        if not isinstance(text, str):
            return str(text)[:max_length]
            
        # Remove control characters and limit length
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        return sanitized[:max_length]


# Module-level convenience functions
_default_validator: Optional[NetworkValidator] = None


def get_network_validator(repo_owner: str, repo_name: str) -> NetworkValidator:
    """
    Get network validator instance for specified repository
    
    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        
    Returns:
        NetworkValidator instance
    """
    return NetworkValidator(repo_owner, repo_name)


def set_default_network_validator(repo_owner: str, repo_name: str) -> None:
    """Set default network validator for the application"""
    global _default_validator
    _default_validator = NetworkValidator(repo_owner, repo_name)


def get_default_network_validator() -> Optional[NetworkValidator]:
    """Get default network validator instance"""
    return _default_validator