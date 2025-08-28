# TODO - DJs KB-maskin Application

This document tracks known issues, improvements, and future development tasks.

## ✅ Recently Completed (v1.5.7)

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

## 📦 Build & Distribution

### PyInstaller Configuration
- **Spec File**: `DJs_KB_maskin.spec` configured with version in filename
- **Current Version**: v1.5.7
- **Build Command**: `pyinstaller DJs_KB_maskin.spec`
- **Output**: `dist/DJs_KB_maskin_v1.4.6.exe`
- **Icon**: Uses `Agg-med-smor-v4-transperent.ico`

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