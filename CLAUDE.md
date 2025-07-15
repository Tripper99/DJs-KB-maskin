# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python GUI application for handling files from "Svenska Tidningar" (Swedish Newspapers). The application provides two main functionalities:

1. **Gmail JPG Downloader** - Downloads JPG attachments from Gmail using the Gmail API
2. **KB File Processor** - Converts JPG files to PDFs with meaningful names and merges multi-page articles

## Development Environment

### Python Dependencies
Install dependencies using pip:
```bash
pip install ttkbootstrap google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client Pillow pandas openpyxl
```

### Required Files
- `credentials.json` - Google API credentials file (not in repository)
- `Agg-med-smor-v4-transperent.ico` - Application icon
- `Manual.docx` - User manual (referenced in code)

### Running the Application
```bash
python "App DJs KB_maskin_v022_FUNKAR_testa_uppdelning_m_ClaudeCode.py"
```

## Architecture

### Main Components

1. **Configuration Management** (`load_config`, `save_config`)
   - Saves/loads settings to/from `combined_app_config.json`
   - Handles default values and validation

2. **Gmail Integration Classes**
   - `GmailAuthenticator` - Handles OAuth authentication and token management
   - `GmailSearcher` - Builds search queries and retrieves email messages
   - `AttachmentProcessor` - Extracts and downloads JPG attachments
   - `DownloadManager` - Handles file saving with conflict resolution
   - `GmailDownloader` - Orchestrates the Gmail download process

3. **KB Processing Classes**
   - `KBProcessor` - Processes JPG files into PDFs with proper naming
   - Handles file renaming using bib-code to newspaper name mapping
   - Groups files by date and newspaper for PDF creation
   - Uses PIL for image processing and PDF creation

4. **GUI Application** (`CombinedApp`)
   - Built with `ttkbootstrap` for modern styling
   - Supports enabling/disabling individual tools
   - Auto-linking between Gmail output and KB input directories
   - Progress tracking and cancellation support

### Key Design Patterns

- **Separation of Concerns**: Each major functionality is in its own class
- **Progress Callbacks**: All long-running operations support progress reporting
- **Cancellation Support**: Operations can be cancelled mid-process
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Configuration Persistence**: Settings are saved between sessions

### File Processing Flow

1. **Gmail Download**: 
   - Authenticate with Gmail API
   - Search for emails from specified sender and date range
   - Download JPG attachments with conflict resolution

2. **KB Processing**:
   - Read Excel file mapping bib-codes to newspaper names
   - Rename JPG files with format: `{date} {newspaper} {bib} {numbers}.jpg`
   - Group files by date and newspaper
   - Create PDFs with page count in filename: `{date} {newspaper} ({pages} sid).pdf`

### Important Implementation Details

- **Date Validation**: Supports both YYYY-MM-DD and YYYYMMDD formats
- **File Conflict Resolution**: Interactive dialogs for overwrite/skip decisions
- **Memory Management**: Streams images to PDFs to minimize memory usage
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Threading**: Uses GUI updates to prevent freezing during long operations

## Development Notes

- The application uses Swedish language for the UI
- All logging is done to timestamped files in the application directory
- Configuration is stored in JSON format for easy modification
- The application can be packaged as a standalone executable using PyInstaller
- Error messages are user-friendly and localized in Swedish

## Testing

Run the application and test both Gmail and KB functionality:
1. Configure Gmail credentials and test email download
2. Test KB processing with sample Excel file and JPG files
3. Verify PDF creation and file naming conventions
4. Test cancellation and error handling scenarios