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
python "App DJs KB_maskin_v022_FUNKAR_testa_uppdelning_m_ClaudeCode.py"
```

## Architecture Overview

### Main Components

1. **Configuration** - JSON-based settings persistence (`combined_app_config.json`)
2. **Gmail Integration** - OAuth authentication, email search, attachment download with conflict resolution
3. **KB Processing** - JPG to PDF conversion with bib-code mapping, date grouping, and page counting
4. **GUI** - ttkbootstrap-based interface with progress tracking and cancellation support

### Key Features

- **Threading** - Background processing keeps GUI responsive
- **Cancellation** - All operations support immediate cancellation
- **Memory Efficient** - Streams images to PDFs to handle large batches
- **Auto-linking** - Gmail output directory auto-populates KB input directory
- **Duplicate Detection** - Prevents re-downloading files in same session
- **Conflict Resolution** - Interactive dialogs for handling existing files

### File Naming Conventions

- **Input JPGs**: `bib{code}_{date}_{sequence}.jpg`
- **Renamed JPGs**: `{date} {newspaper} {bib} {numbers}.jpg`
- **Output PDFs**: `{date} {newspaper} ({pages} sid).pdf`

## Development Guidelines

- Swedish UI language throughout
- Comprehensive error handling with user-friendly messages
- Logging to timestamped files
- Windows-first development (cross-platform compatible)
- Can be packaged with PyInstaller

## Testing Checklist

1. Gmail authentication and download functionality
2. KB Excel file reading and bib-code mapping
3. PDF creation with correct naming
4. Cancellation during operations
5. File conflict resolution dialogs
6. Large batch processing (100+ files)

## Current Status

The application is production-ready with:
- Responsive GUI with proper threading
- Comprehensive cancellation support
- KB-specific workflow optimizations
- Professional error handling and logging

For detailed development history and resolved issues, see [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md).