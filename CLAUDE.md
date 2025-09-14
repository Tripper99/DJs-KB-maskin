# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

A Python GUI application for handling newspaper files from "Svenska Tidningar" (Swedish Newspapers):

1. **Gmail JPG Downloader** - Downloads JPG attachments from Gmail using the Gmail API
2. **KB File Processor** - Converts JPG files to PDFs with meaningful names and merges multi-page articles

## Quick Start

### Dependencies
```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install ttkbootstrap google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client Pillow
```

### Required Files
- `credentials.json` - Google API credentials (not in repository)
- `titles_bibids_YYYY-MM-DD.csv` - CSV file with bib-code to newspaper name mapping (auto-detected)
- `requirements.txt` - Python package dependencies with versions
- `Agg-med-smor-v4-transperent.ico` - Application icon
- `Manual.docx` - User manual

### Run Application
```bash
python app.py
```

## Architecture Overview

### Main Components

1. **Configuration** - JSON-based settings persistence (`djs_kb-maskin_settings.json`)
2. **Gmail Integration** - OAuth authentication, email search, attachment download with conflict resolution
3. **KB Processing** - JPG to PDF conversion with CSV-based bib-code mapping, date grouping, and page counting
4. **GUI** - ttkbootstrap-based interface with progress tracking and cancellation support
5. **Security** - Comprehensive path validation and secure file operations (`src/security/`)
6. **Version Management** - Centralized versioning system (`src/version.py`)

### Key Features

- **CSV-based Bib-code Lookup** - Uses built-in Python CSV module instead of Excel dependencies
- **Auto-detection** - Automatically finds CSV file in app directory (titles_bibids_*.csv pattern)
- **Update System** - GitHub Releases API integration for version checking
- **Threading** - Background processing keeps GUI responsive
- **Cancellation** - All operations support immediate cancellation
- **Memory Efficient** - Streams images to PDFs to handle large batches
- **Auto-linking** - Gmail output directory auto-populates KB input directory
- **Duplicate Detection** - Prevents re-downloading files in same session
- **Conflict Resolution** - Interactive dialogs for handling existing files
- **Security** - Path validation, injection prevention, filename sanitization, network validation
- **Version Control** - Centralized version management with history tracking

### File Naming Conventions

- **Input JPGs**: `bib{code}_{date}_{sequence}.jpg`
- **Renamed JPGs**: `{date} {newspaper} {bib} {numbers}.jpg`
- **Output PDFs**: `{date} {newspaper} ({pages} sid).pdf`

### CSV Format

The CSV file must be named `titles_bibids_YYYY-MM-DD.csv` and placed in the application directory. Format:
```csv
"NEWSPAPER NAME","bibcode"
"AFTONBLADET","4345612"
"DAGENS NYHETER","1234567"
```

The application automatically detects the most recent CSV file matching this pattern.

## File Structure

### Core Application
- `app.py` - Main entry point
- `src/version.py` - Centralized version management
- `src/config.py` - Configuration management

### Security Modules
- `src/security/path_validator.py` - Path validation and sanitization
- `src/security/secure_file_ops.py` - Secure file operation wrappers
- `src/security/network_validator.py` - Network security for update system
- `src/security/__init__.py` - Security module exports

### Update System Modules
- `src/update/version_checker.py` - GitHub API integration for version checking
- `src/update/update_dialog.py` - Swedish language update notifications
- `src/update/models.py` - Data models for update information
- `src/update/__init__.py` - Update module exports

### Functional Modules  
- `src/gmail/` - Gmail API integration
- `src/kb/` - KB file processing with CSV handler
- `src/gui/` - User interface

### Testing & Documentation
- `tests/test_security.py` - Security feature tests
- `DEVELOPMENT_HISTORY.md` - Detailed development history and resolved issues
- `TODO.md` - Prioritized list of known issues and improvements
- `Manual.docx` - User manual

## Development Guidelines

- Swedish UI language throughout
- Comprehensive error handling with user-friendly messages
- Logging to timestamped files
- Windows-first development (cross-platform compatible)
- Can be packaged with PyInstaller
- **Security-first approach** - All file operations use validated paths
- **Version management** - Update `src/version.py` for all releases

## Testing Checklist

1. Gmail authentication and download functionality
2. KB CSV file auto-detection and bib-code mapping
3. PDF creation with correct naming (with parentheses: `(1 sid)`)
4. Cancellation during operations
5. File conflict resolution dialogs
6. Large batch processing (100+ files)
7. CSV file validation and error handling
8. Manual CSV file selection when auto-detection fails
9. **Security validation** - Run `python -m pytest tests/test_security.py`
10. **Syntax checking** - Run `python -m ruff check src/`

## Current Status (v1.7.5 - Critical Path Resolution Bug Fix Completed 2025-09-13)

The application is production-ready with:
- **🚨 Critical Path Resolution Bug Fix** - Resolved mysterious issue where files disappeared when using default download folder in installed executable
- **File Conflict Resolution Fix** - "Overwrite All" and "Skip All" options persist across multiple conflicts during PDF creation
- **CSV Migration** - Replaced Excel dependency with built-in CSV module, reduced total dependencies from 9 to 7 packages
- **Simplified GUI** - Removed Excel file chooser, CSV files are auto-detected with pattern `titles_bibids_*.csv`
- **Critical Bib-code Fix** - Files like "bib13991089" now correctly find CSV entry "13991089" by stripping prefix
- **Requirements.txt** - Streamlined dependency list with exact version numbers
- **Professional Installer** - Inno Setup installer with Swedish interface, Start Menu shortcuts, and proper upgrade behavior
- **Organized Build Tools** - Complete build-tools directory structure with automated scripts
- **Update System** - GitHub Releases API integration for version checking and update notifications
- **Session Management Enhancement** - Date fields no longer persist between sessions, always start fresh
- **Email Confirmation Dialog** - Added confirmation dialog showing email count before download begins
- **Unicode Compatibility** - Resolved Windows encoding issues by removing emoji characters from logs
- **Complete Icon Consistency** - Application icon now displays on all 7 custom dialog windows
- **Dialog UX Improvements** - Proper sizing and button visibility for all confirmation dialogs
- **Critical Bug Fixes** - Resolved placeholder text configuration issue preventing Gmail search failures
- **PyInstaller Icon Support** - Application icon displays correctly in compiled .exe files
- **Improved Default Folder Handling** - Downloads default to app subdirectory with automatic creation
- **Comprehensive Tooltip System** - 15+ tooltips across all major GUI elements for enhanced user guidance
- **Dynamic User Interface** - Smart button text and status messages that adapt to user selections
- **Optimized Default Settings** - Sensible defaults (delete originals, don't save renamed JPGs) 
- **Enterprise-level security** - Path validation, injection prevention, secure file operations, network validation
- **Enhanced GUI** - 40% taller window, optimized screen positioning, logical field ordering, Help menu
- **Swedish Language Support** - Complete interface localization with proper character handling
- **Responsive interface** with proper threading and comprehensive cancellation support
- **KB-specific workflow** optimizations for Swedish newspaper processing
- **Professional error handling** and logging
- **Centralized version management** for easier maintenance
- **PyInstaller Integration** - Ready for .exe distribution with version-numbered builds and icon support
- **Complete documentation** - Full development history and architectural analysis
- **Clean Code** - All 50 Ruff linting errors fixed, full compliance achieved (2025-09-05)

## Documentation

- **[docs/codebase_analysis.md](docs/codebase_analysis.md)** - Comprehensive architecture analysis and documentation
- **[DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md)** - Complete development history and resolved issues  
- **[TODO.md](TODO.md)** - Prioritized list of known issues and future improvements
- **Security Features** - See `src/security/` modules for implementation details

## Recent Improvements (v1.5.9)

### Update Dialog Enhancement (v1.5.9)
- **Improved Dialog Height** - Doubled update dialog window height to 900px for full content visibility
- **Better UX** - All release notes, file lists, and buttons now fully accessible without scrolling issues
- **Maintained Responsiveness** - Dialog remains resizable with appropriate minimum constraints

## Previous Improvements (v1.5.8)

### Update System (v1.5.8)
- **GitHub Integration** - Version checking via GitHub Releases API with secure network validation
- **Swedish Update Notifications** - Displays new version info and available downloads in Swedish
- **Multi-file Support** - Shows all release assets (exe files, manual, Excel templates)
- **Browser Launch** - Opens GitHub release page for manual download
- **No Authentication** - End users can check for updates without GitHub accounts
- **Repository Configuration** - Pre-configured for Tripper99/DJs-KB-maskin repository

## Previous Improvements (v1.5.2 - v1.5.7)

### Session & Dialog Improvements (v1.5.2 - v1.5.7)
- **Date Field Reset** - Date fields now start fresh each session with placeholder text only
- **Download Confirmation** - Added Swedish confirmation dialog before email attachment download
- **Icon Integration** - Consistent application icon across all custom dialog windows:
  - Email confirmation dialog
  - File conflict dialogs (Gmail JPG and KB PDF)
  - Password input dialog
  - Error message dialogs
- **Dialog Sizing** - Fixed confirmation dialog dimensions for proper button visibility
- **Encoding Fixes** - Removed Unicode emojis causing Windows cp1252 encoding errors
- **Thread-Safe Callbacks** - Proper threading.Event implementation for GUI dialog callbacks

## Previous Improvements (v1.4.7 - v1.4.9)

### Default Folder Management (v1.4.7)
- **New Default Location** - Downloads now default to `Nedladdningar` subfolder within application directory
- **Automatic Creation** - Folder is created automatically if it doesn't exist
- **Cross-Platform** - Works consistently whether running as Python script or compiled executable
- **Benefits** - Keeps files organized with the application, easier file management

### PyInstaller Integration (v1.4.8)
- **Icon Display Fix** - Application icon now shows correctly in compiled .exe window title bar
- **Resource Bundling** - Proper handling of bundled resources using `sys._MEIPASS`
- **Build Command** - Updated with `--add-data` parameter for icon inclusion

### Configuration Stability (v1.4.9)
- **Critical Bug Fix** - Resolved placeholder text being saved to configuration file
- **Prevents Failures** - Eliminates date validation errors and Gmail search failures
- **Backwards Compatibility** - Handles existing corrupted configuration files gracefully
- **Robust Handling** - Added filtering in both save and load configuration methods

## GUI Enhancements (v1.4.6)

### Tooltip System
- **Comprehensive Coverage** - 15+ tooltips across all major interface elements
- **Swedish Language** - All tooltips in Swedish with proper UTF-8 character support
- **Contextual Help** - Field-specific guidance without cluttering the interface
- **Technical Implementation** - Uses ttkbootstrap.tooltip.ToolTip with 400ms delay and smart wrapping

### Dynamic Interface (v1.4.6)
- **Smart Button Text** - Start button adapts based on selected tools:
  - "Kör igång" (both tools selected)
  - "Starta hämtning av jpg-bilagor" (Gmail only) 
  - "Starta filkonvertering" (KB only)
- **Status Messages** - Contextual guidance messages that update based on form state
- **Optimized Defaults** - Sensible settings (delete originals, don't save renamed files)

### Window Improvements (v1.3.6)
- **Increased Height** - Main window now 1400px tall (40% increase from 1000px)
- **Better Positioning** - Window positioned at 5px from top for optimal screen usage
- **Logical Field Order** - Excel file selection moved to top of KB section for intuitive workflow
- **File Dialog Consistency** - All file dialogs start in application directory (.exe compatibility)
- **Date Field Placeholders** - Shows "ÅÅÅÅ-MM-DD" format hint that disappears on focus

### Build & Distribution (v1.6.0+)

#### Build Tools Organization
All build-related files are organized in the `build-tools/` directory:
- **PyInstaller specs**: `build-tools/pyinstaller/`
- **Inno Setup scripts**: `build-tools/inno-setup/`
- **Resources**: `build-tools/resources/` (icon, manual, Excel template)
- **Build scripts**: `build-tools/scripts/`
- **Output files**: `build-tools/output/` (exe and installer)

#### Building the Application

**Complete Build (Recommended)**:
```bash
cd build-tools/scripts
build_all.bat
```

**Individual Steps**:
- Build executable: `build_exe.bat`
- Build installer: `build_installer.bat` (requires executable)

#### Requirements
- Python 3.x with all dependencies
- PyInstaller: `pip install pyinstaller`
- Inno Setup 6: https://jrsoftware.org/isdl.php

#### Output Files
- Executable: `build-tools/output/exe/DJs_KB_maskin_v1.6.0.exe`
- Installer: `build-tools/output/installer/DJs_KB_maskin_v1.6.0_setup.exe`

#### Installer Features
- Swedish language interface
- Includes Manual.docx and Excel template  
- Creates Start Menu shortcuts
- Optional desktop shortcut
- Application icon properly set
- Creates default folders (Nedladdningar, logs)

## Security Features (v1.3+)

### Path Validation
- Prevents path traversal attacks (`../`, `..\`)
- Blocks Windows reserved names (CON, PRN, etc.)
- Blocks UNC paths (`\\server\share`)
- Unicode normalization against homograph attacks
- File size and path length limits

### Secure Operations
- All file operations use validated paths
- Filename sanitization preserving Swedish characters and parentheses
- Subprocess protection (prevents shell injection)
- Secure Excel file reading with validation
- Automatic directory validation and creation
- Always save new version before coding. Commit it with info on what changes are attempted. After successful testing commit again with new info on successful implementation.