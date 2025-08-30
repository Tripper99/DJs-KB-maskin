#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version checker module with secure GitHub API integration
Handles checking for updates from GitHub releases with comprehensive security
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from ..security import (
    NetworkValidator, 
    NetworkSecurityError
)
from ..version import get_version
from .models import UpdateInfo, UpdateCheckResult, ReleaseAssets, AssetInfo

logger = logging.getLogger(__name__)

# Cache settings
CACHE_DURATION_MINUTES = 30
MAX_CACHE_AGE = timedelta(minutes=CACHE_DURATION_MINUTES)

# Swedish error messages
ERROR_MESSAGES = {
    'network_error': 'Kunde inte ansluta till internet. Kontrollera din nätverksanslutning och försök igen.',
    'api_error': 'GitHub tjänsten är inte tillgänglig just nu. Försök igen senare.',
    'parse_error': 'Kunde inte läsa uppdateringsinformation. Besök GitHub manuellt för senaste versionen.',
    'no_releases': 'Inga utgåvor hittades i GitHub repository.',
    'invalid_release': 'Uppdateringsinformationen är ofullständig eller skadad.',
    'timeout_error': 'Anslutningen tog för lång tid. Kontrollera din internetanslutning.',
    'security_error': 'Säkerhetsfel vid kontroll av uppdateringar. Besök GitHub manuellt.',
    'validation_error': 'Ogiltiga uppdateringsdata mottagna från GitHub.'
}


class VersionChecker:
    """Secure version checker for GitHub releases"""
    
    def __init__(self, repo_owner: str, repo_name: str):
        """
        Initialize version checker for specific repository
        
        Args:
            repo_owner: GitHub repository owner/organization
            repo_name: GitHub repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.network_validator = NetworkValidator(repo_owner, repo_name)
        self.current_version = get_version()
        
        # Cache for update check results
        self._cache: Optional[UpdateCheckResult] = None
        self._cache_timestamp: Optional[datetime] = None
        
        # GitHub API configuration
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        logger.info(f"Version checker initialized for {repo_owner}/{repo_name}, current version: {self.current_version}")
        
    def check_for_updates(self, force_refresh: bool = False) -> UpdateCheckResult:
        """
        Check for available updates from GitHub releases
        
        Args:
            force_refresh: Skip cache and force fresh check
            
        Returns:
            UpdateCheckResult with update information or error details
        """
        logger.info("Starting update check...")
        
        # Check cache first unless forced refresh
        if not force_refresh and self._is_cache_valid():
            logger.info("Returning cached update check result")
            cached_result = self._cache
            cached_result.cached_result = True
            return cached_result
            
        try:
            # Validate API URL
            self.network_validator.validate_api_url(self.api_url)
            
            # Make secure request to GitHub API
            release_data = self._make_secure_request()
            
            # Parse and validate release data
            update_info = self._parse_release_data(release_data)
            
            # Create successful result
            result = UpdateCheckResult(
                success=True,
                update_info=update_info,
                cached_result=False
            )
            
            # Cache the result
            self._cache_result(result)
            
            logger.info(f"Update check completed successfully. Update available: {result.has_update}")
            return result
            
        except NetworkSecurityError as e:
            logger.warning(f"Security error during update check: {e}")
            return self._create_error_result('security_error', str(e))
            
        except requests.exceptions.Timeout:
            logger.warning("Update check timed out")
            return self._create_error_result('timeout_error')
            
        except requests.exceptions.ConnectionError:
            logger.warning("Network connection error during update check")
            return self._create_error_result('network_error')
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("No releases found in repository")
                return self._create_error_result('no_releases')
            else:
                logger.warning(f"GitHub API error: {e}")
                return self._create_error_result('api_error')
                
        except Exception as e:
            logger.error(f"Unexpected error during update check: {e}")
            return self._create_error_result('parse_error', str(e))
            
    def _make_secure_request(self) -> Dict[str, Any]:
        """Make secure HTTPS request to GitHub API"""
        # Get secure request configuration
        request_config = self.network_validator.get_secure_request_config()
        
        logger.debug(f"Making secure request to: {self.api_url}")
        
        # Make request with security configuration
        response = requests.get(self.api_url, **request_config)
        
        # Check HTTP status
        response.raise_for_status()
        
        # Validate response size and parse JSON
        validated_data = self.network_validator.validate_json_response(response.text)
        
        # Validate release data structure
        release_data = self.network_validator.validate_release_data(validated_data)
        
        logger.debug("GitHub API response validated successfully")
        return release_data
        
    def _parse_release_data(self, release_data: Dict[str, Any]) -> UpdateInfo:
        """Parse GitHub release data into UpdateInfo"""
        # Extract basic release information
        latest_version = release_data['tag_name']
        release_name = release_data.get('name', latest_version)
        release_url = release_data['html_url']
        release_notes = release_data.get('body', '')
        published_date = release_data.get('published_at', '')
        
        # Validate release URL
        self.network_validator.validate_release_url(release_url)
        
        # Sanitize display texts
        release_name = self.network_validator.sanitize_display_text(release_name, 100)
        release_notes = self.network_validator.sanitize_display_text(release_notes, 5000)
        
        # Parse assets
        assets = self._parse_assets(release_data.get('assets', []))
        
        # Create UpdateInfo
        update_info = UpdateInfo(
            current_version=self.current_version,
            latest_version=latest_version,
            release_url=release_url,
            release_notes=release_notes,
            assets=assets,
            published_date=published_date
        )
        
        logger.debug(f"Parsed release data: {latest_version}, assets: {assets.total_files}")
        return update_info
        
    def _parse_assets(self, assets_data: list) -> ReleaseAssets:
        """Parse GitHub assets into ReleaseAssets structure"""
        exe_file = None
        manual_file = None
        other_files = []
        
        for asset_data in assets_data:
            try:
                asset_info = AssetInfo(
                    name=asset_data['name'],
                    download_url=asset_data['browser_download_url'],
                    size=asset_data['size']
                )
                
                # Categorize asset by type
                if asset_info.is_exe_file:
                    exe_file = asset_info
                elif asset_info.is_manual_file:
                    manual_file = asset_info
                else:
                    other_files.append(asset_info)
                    
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid asset: {e}")
                continue
                
        return ReleaseAssets(
            exe_file=exe_file,
            manual_file=manual_file,
            other_files=other_files
        )
        
    def _create_error_result(self, error_key: str, details: str = None) -> UpdateCheckResult:
        """Create error result with Swedish error message"""
        error_message = ERROR_MESSAGES.get(error_key, 'Ett okänt fel uppstod')
        
        if details:
            error_message += f" (Detaljer: {details})"
            
        return UpdateCheckResult(
            success=False,
            error_message=error_message
        )
        
    def _is_cache_valid(self) -> bool:
        """Check if cached result is still valid"""
        if self._cache is None or self._cache_timestamp is None:
            return False
            
        cache_age = datetime.now() - self._cache_timestamp
        return cache_age < MAX_CACHE_AGE
        
    def _cache_result(self, result: UpdateCheckResult) -> None:
        """Cache update check result"""
        self._cache = result
        self._cache_timestamp = datetime.now()
        logger.debug(f"Cached update check result for {CACHE_DURATION_MINUTES} minutes")
        
    def clear_cache(self) -> None:
        """Clear cached update check results"""
        self._cache = None
        self._cache_timestamp = None
        logger.debug("Update check cache cleared")
        
    def get_cache_status(self) -> Dict[str, Any]:
        """Get information about current cache status"""
        if not self._is_cache_valid():
            return {
                'cached': False,
                'cache_age': None,
                'cache_expires': None
            }
            
        cache_age = datetime.now() - self._cache_timestamp
        cache_expires = self._cache_timestamp + MAX_CACHE_AGE
        
        return {
            'cached': True,
            'cache_age': cache_age,
            'cache_expires': cache_expires,
            'has_update': self._cache.has_update if self._cache else False
        }
        
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        try:
            v1_tuple = self._version_to_tuple(version1)
            v2_tuple = self._version_to_tuple(version2)
            
            if v1_tuple < v2_tuple:
                return -1
            elif v1_tuple > v2_tuple:
                return 1
            else:
                return 0
                
        except ValueError as e:
            logger.error(f"Error comparing versions {version1} and {version2}: {e}")
            return 0
            
    def _version_to_tuple(self, version: str) -> tuple:
        """Convert version string to comparable tuple"""
        # Remove 'v' prefix if present and convert to tuple
        clean_version = version.lstrip('v')
        return tuple(map(int, clean_version.split('.')))
        
    @property
    def repository_info(self) -> Dict[str, str]:
        """Get repository information"""
        return {
            'owner': self.repo_owner,
            'name': self.repo_name,
            'api_url': self.api_url,
            'current_version': self.current_version
        }


# Module-level convenience functions
def create_version_checker(repo_owner: str, repo_name: str) -> VersionChecker:
    """
    Create version checker instance
    
    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        
    Returns:
        VersionChecker instance
    """
    return VersionChecker(repo_owner, repo_name)


def quick_update_check(repo_owner: str, repo_name: str) -> UpdateCheckResult:
    """
    Perform quick update check
    
    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        
    Returns:
        UpdateCheckResult
    """
    checker = VersionChecker(repo_owner, repo_name)
    return checker.check_for_updates()