# TODO - DJs KB-maskin Application

This document tracks known issues, improvements, and future development tasks.

## ✅ Recently Completed (2025-09-10)

### File Conflict Resolution Bug Fix (v1.7.4) - COMPLETED 2025-09-10
- ✅ **Persistent Flag System**: Added class-level overwrite_all and skip_all flags
- ✅ **Pre-Dialog Logic**: Check persistent flags before showing conflict dialog
- ✅ **Dialog Handler Updates**: "Overwrite All" and "Skip All" buttons set persistent flags
- ✅ **Code Quality**: Fixed significant indentation issues in dialog block
- ✅ **Testing**: All Ruff syntax checks passed, minor test cleanup completed
- ✅ **User Impact**: "Overwrite All" now works correctly across multiple file conflicts

### CSV Migration & UI Improvements (v1.7.0 - v1.7.3) - COMPLETED 2025-09-10
- ✅ **Major Migration**: Replaced Excel dependency with CSV for bib-code lookup (v1.7.0)
- ✅ **Dependency Reduction**: Reduced from 9 to 7 packages (removed pandas, openpyxl)
- ✅ **GUI Simplification**: Removed Excel file chooser, added auto-detection
- ✅ **Critical Bug Fix**: Fixed bib-code extraction to strip 'bib' prefix (v1.7.1)
- ✅ **UI Cleanup**: Removed obsolete Excel references from user messages (v1.7.2)
- ✅ **Layout Improvement**: Moved CSV status to bottom of KB section (v1.7.3)

## ✅ Previously Completed (2025-09-08)

### Code Cleanup & Documentation (v1.6.1 - v1.6.2) - COMPLETED 2025-09-08
- ✅ **Code Optimization**: Removed unnecessary if statement from KB processor (v1.6.1)
- ✅ **Requirements File**: Created requirements.txt with all dependencies and versions (v1.6.2)
- ✅ **Python Version**: Documented Python 3.13.5 requirement
- ✅ **Dependency Versions**: Listed exact versions for all packages
- ✅ **Installation Guide**: Added pip install command for easy setup

## ✅ Previously Completed (2025-09-07)

### Inno Setup Installer Implementation (v1.6.0) - COMPLETED 2025-09-07
- ✅ **Build Tools Organization**: Created organized `build-tools/` directory structure
- ✅ **Inno Setup Script**: Complete Swedish language installer configuration  
- ✅ **PyInstaller Integration**: Updated spec file with proper resource handling
- ✅ **Build Automation**: Created `build_exe.bat`, `build_installer.bat`, `build_all.bat`
- ✅ **Resource Management**: Icon, Manual.docx, and Excel template properly included
- ✅ **Documentation**: Updated CLAUDE.md with comprehensive build instructions
- ✅ **Architecture Fix**: Resolved x64 deprecation warning (x64compatible)
- ✅ **Successful Compilation**: Created 62.4MB installer with Swedish interface
- ✅ **Upgrade Behavior**: Confirmed proper version replacement (no duplicates)

### Code Quality - Linting Compliance (2025-09-05)
- ✅ **Ruff Linting**: Fixed all 50 linting errors for clean codebase
- ✅ **Import Cleanup**: Replaced import star usage with explicit imports
- ✅ **Exception Handling**: Fixed bare except clauses with specific exceptions
- ✅ **Variable Fixes**: Resolved undefined and unused variable issues
- ✅ **CLAUDE.md**: Added to .gitignore to keep project instructions private

## ✅ Previously Completed (v1.5.9)

### Update Dialog UI Fix - COMPLETED 2025-08-30
- ✅ **Dialog Height**: Doubled update dialog height from 500px to 900px (v1.5.9)
- ✅ **Content Visibility**: All release notes, file lists, and buttons now fully visible
- ✅ **Minimum Size**: Adjusted minimum height to 850px to prevent content cutoff

## ✅ Previously Completed (v1.5.8)

### Update System Implementation - COMPLETED 2025-08-29
- ✅ **GitHub Integration**: Added version checking via GitHub Releases API (v1.5.8)
- ✅ **Swedish Update Dialog**: Shows new version info and downloadable files in Swedish
- ✅ **Security Validation**: Comprehensive network security for API calls and URL validation
- ✅ **No Authentication Required**: End users can check updates without GitHub accounts
- ✅ **Multi-file Support**: Displays all release assets (exe, manual, Excel files)
- ✅ **Browser Launch**: Opens GitHub release page for manual download

### Session Improvements - COMPLETED 2025-08-28
- ✅ **Date Field Persistence Fix**: Date fields no longer remember values between sessions (v1.5.2)
- ✅ **Email Confirmation Dialog**: Added dialog showing email count before download (v1.5.3)
- ✅ **Unicode Compatibility**: Removed emoji characters causing Windows encoding errors (v1.5.4)
- ✅ **Icon Consistency**: Added application icon to all 7 custom dialog windows (v1.5.5-v1.5.7)
- ✅ **Dialog Sizing**: Fixed confirmation dialog size to show all buttons properly (v1.5.6)

### Tooltip System Implementation - COMPLETED 2025-08-23
- ✅ **Comprehensive Tooltips**: Added tooltips to all major GUI fields (15+ tooltips)
- ✅ **Main Tool Switches**: Added tooltips to Gmail and KB selection checkboxes
- ✅ **Start Button**: Added playful tooltip with "whoopee machine" reference
- ✅ **Swedish Language**: All tooltips in Swedish with proper character support

### UI/UX Improvements - COMPLETED 2025-08-23
- ✅ **Delete Logic Reversal**: "Bevara bib-filerna" now OFF by default (deletes originals)
- ✅ **Default Settings**: "Spara omdöpta jpg-filer" now OFF by default
- ✅ **Layout Optimization**: Moved delete/save option to bottom of KB section
- ✅ **Dynamic Button Text**: Start button text changes based on selected tools
- ✅ **Status Messages**: Improved user guidance messages

### Previously Completed (v1.3.6)
- ✅ **File Dialog Initial Directory**: All file dialogs now start in application directory for .exe compatibility
- ✅ **Window Positioning**: Window now opens at 5 pixels from top for better screen usage
- ✅ **Date Field Placeholders**: Added "ÅÅÅÅ-MM-DD" placeholder text with proper focus behavior
- ✅ **Validation Preservation**: All existing validation and functionality maintained

## 📦 Build & Distribution (v1.6.0+)

### Inno Setup Installer - COMPLETED ✅
- **Current Version**: v1.6.0 with professional installer
- **Installer**: `build-tools/output/installer/DJs_KB_maskin_v1.6.0_setup.exe` (62.4MB)
- **Executable**: `build-tools/output/exe/DJs_KB_maskin_v1.6.0.exe` (61.4MB)
- **Build Command**: `cd build-tools/scripts && build_all.bat`
- **Features**: Swedish interface, Start Menu shortcuts, proper uninstall, upgrade behavior

## 🔧 Known Issues & Improvements Needed

### High Priority

#### 1. Security Test Failures 
**Status**: 🔴 Needs Investigation
- Several security tests are failing due to overly restrictive validation
- Path validation rejecting legitimate Windows temp paths
- Need to adjust validation rules for test environment compatibility
- **Files**: `tests/test_security.py`
- **Impact**: Tests failing but application works in practice

#### 2. OAuth Token Management
**Status**: 🟡 Improvement Opportunity  
- OAuth tokens are currently stored in plaintext JSON files
- Consider implementing secure credential storage (Windows Credential Manager)
- Add token refresh error handling
- **Files**: Token files, `src/gmail/authenticator.py`
- **Impact**: Security best practice improvement

#### 3. File Size Validation Tuning
**Status**: 🟡 Performance Optimization
- Current limits: 100MB files, 50MP images
- May be too large for typical newspaper scanning use case
- Consider reducing to more reasonable limits (e.g., 10MB, 5MP)
- **Files**: `src/security/path_validator.py`, `src/kb/processor.py`
- **Impact**: Better DoS protection

### Medium Priority

#### 4. Enhanced Input Validation in GUI
**Status**: 🟡 User Experience
- Add real-time path validation in file picker dialogs
- Show visual feedback for invalid paths before processing
- Prevent form submission with invalid inputs
- **Files**: `src/gui/main_window.py`
- **Impact**: Better user experience

#### 5. Logging Security Review
**Status**: 🟡 Privacy Enhancement
- Review what sensitive information is being logged
- Implement log sanitization for email addresses and file paths
- Consider log rotation and retention policies
- **Files**: All modules with logging
- **Impact**: Privacy compliance

#### 6. Configuration Security
**Status**: 🟡 Security Enhancement
- Validate all configuration file paths on load
- Sanitize configuration values before use
- Add configuration file integrity checks
- **Files**: `src/config.py`, `djs_kb-maskin_settings.json`
- **Impact**: Configuration tampering protection

### Low Priority

#### 7. Performance Monitoring
**Status**: 🟢 Enhancement
- Add performance metrics for large batch operations
- Monitor memory usage during PDF generation
- Add progress estimation improvements
- **Files**: `src/kb/processor.py`, `src/gmail/downloader.py`
- **Impact**: Better user feedback for large operations

#### 8. Error Message Localization
**Status**: 🟢 User Experience
- Ensure all error messages are in Swedish
- Standardize error message formatting
- Add user-friendly explanations for technical errors
- **Files**: All modules
- **Impact**: Consistent Swedish language experience

#### 9. Code Documentation
**Status**: 🟢 Maintenance
- Add comprehensive docstrings to all security functions
- Update CLAUDE.md with security implementation details
- Create API documentation for security modules
- **Files**: `src/security/`, `CLAUDE.md`
- **Impact**: Better code maintainability

#### 10. Dependency Management
**Status**: 🟢 Maintenance
- Regular dependency updates and security scanning
- Pin dependency versions for reproducible builds
- Document minimum required versions
- **Files**: Requirements file (to be created)
- **Impact**: Security and stability

## 🧪 Testing Improvements Needed

### 1. Integration Tests
- Test full workflow from Gmail download to PDF creation
- Test cancellation during different phases
- Test error recovery scenarios

### 2. Security Test Environment
- Fix test failures by adjusting validation for test environments
- Add performance tests for security validation overhead
- Test with malicious input files

### 3. User Acceptance Testing
- Test with actual newspaper files from KB
- Validate filename formats meet KB requirements
- Test with large batches (100+ files)

## 📦 Deployment & Distribution

### 1. PyInstaller Configuration
- Ensure security modules are included in executable
- Test standalone executable with all features
- Verify icon and version information

### 2. Installation Package
- Create proper Windows installer
- Include Manual.docx and required files
- Add uninstall capability

## 🔄 Future Enhancements

### 1. Advanced Security Features
- File type validation beyond extensions
- Virus scanning integration
- Digital signature verification for Excel files

### 2. User Interface Improvements
- Drag-and-drop file selection
- Progress bars with time estimates
- Recent files/directories memory

### 3. Workflow Enhancements
- Batch processing queue
- Resume interrupted operations
- Duplicate detection improvements

---

## 📋 Completion Criteria

**For each TODO item:**
- [ ] Implementation complete
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Version incremented

**Priority Legend:**
- 🔴 High Priority (Security/Stability)
- 🟡 Medium Priority (Functionality/UX) 
- 🟢 Low Priority (Enhancement/Maintenance)