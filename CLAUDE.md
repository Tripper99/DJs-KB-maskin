# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

A Python GUI application for handling newspaper files from "Svenska Tidningar" (Swedish Newspapers):

1. **Gmail JPG Downloader** - Downloads JPG attachments from Gmail using the Gmail API
2. **KB File Processor** - Converts JPG files to PDFs with meaningful names and merges multi-page articles

## Quick Start

### Dependencies
```bash
pip install ttkbootstrap google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client Pillow pandas openpyxl
```

### Required Files
- `credentials.json` - Google API credentials (not in repository)
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
3. **KB Processing** - JPG to PDF conversion with bib-code mapping, date grouping, and page counting
4. **GUI** - ttkbootstrap-based interface with progress tracking and cancellation support
5. **Security** - Comprehensive path validation and secure file operations (`src/security/`)
6. **Version Management** - Centralized versioning system (`src/version.py`)

### Key Features

- **Threading** - Background processing keeps GUI responsive
- **Cancellation** - All operations support immediate cancellation
- **Memory Efficient** - Streams images to PDFs to handle large batches
- **Auto-linking** - Gmail output directory auto-populates KB input directory
- **Duplicate Detection** - Prevents re-downloading files in same session
- **Conflict Resolution** - Interactive dialogs for handling existing files
- **Security** - Path validation, injection prevention, filename sanitization
- **Version Control** - Centralized version management with history tracking

### File Naming Conventions

- **Input JPGs**: `bib{code}_{date}_{sequence}.jpg`
- **Renamed JPGs**: `{date} {newspaper} {bib} {numbers}.jpg`
- **Output PDFs**: `{date} {newspaper} ({pages} sid).pdf`

## File Structure

### Core Application
- `app.py` - Main entry point
- `src/version.py` - Centralized version management
- `src/config.py` - Configuration management

### Security Modules
- `src/security/path_validator.py` - Path validation and sanitization
- `src/security/secure_file_ops.py` - Secure file operation wrappers
- `src/security/__init__.py` - Security module exports

### Functional Modules  
- `src/gmail/` - Gmail API integration
- `src/kb/` - KB file processing
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
2. KB Excel file reading and bib-code mapping
3. PDF creation with correct naming (with parentheses: `(1 sid)`)
4. Cancellation during operations
5. File conflict resolution dialogs
6. Large batch processing (100+ files)
7. **Security validation** - Run `python -m pytest tests/test_security.py`
8. **Syntax checking** - Run `python -m ruff check src/`

## Current Status (v1.3.6)

The application is production-ready with:
- **Enterprise-level security** - Path validation, injection prevention, secure file operations
- **Enhanced GUI** - 40% taller window, optimized screen positioning at 5px from top, logical field ordering
- **Improved user experience** - File dialogs start in app directory, date fields show ÅÅÅÅ-MM-DD placeholders
- **Responsive interface** with proper threading
- **Comprehensive cancellation** support throughout all operations
- **KB-specific workflow** optimizations for Swedish newspaper processing
- **Professional error handling** and logging with Swedish language support
- **Centralized version management** for easier maintenance
- **Comprehensive testing** suite for security features
- **Complete documentation** - Full codebase analysis available in `docs/`

## Documentation

- **[docs/codebase_analysis.md](docs/codebase_analysis.md)** - Comprehensive architecture analysis and documentation
- **[DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md)** - Complete development history and resolved issues  
- **[TODO.md](TODO.md)** - Prioritized list of known issues and future improvements
- **Security Features** - See `src/security/` modules for implementation details

## GUI Enhancements (v1.3.6)

### Window Improvements
- **Increased Height** - Main window now 1400px tall (40% increase from 1000px)
- **Better Positioning** - Window positioned at 5px from top for optimal screen usage
- **Logical Field Order** - Excel file selection moved to top of KB section for intuitive workflow

### User Experience Improvements (v1.3.6)
- **File Dialog Consistency** - All file dialogs start in application directory (.exe compatibility)
- **Date Field Placeholders** - Shows "ÅÅÅÅ-MM-DD" format hint that disappears on focus
- **Visual Guidance** - Gray placeholder text provides clear input format expectations

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