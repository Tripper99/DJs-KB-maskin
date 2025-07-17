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

## Current Development Status (2025-07-17)

### Recent Work Completed
- Implemented 3-phase security and stability improvements
- Added thread-safe cancellation using `threading.Event`
- Fixed memory leaks in image processing
- Added comprehensive input validation and sanitization
- Improved error handling and logging
- **MAJOR UPDATE (2025-07-17)**: Fixed critical GUI threading issues and responsiveness problems

### ✅ RESOLVED - All Critical Issues Fixed (2025-07-17)

## Summary of Issues Resolved:

### 1. ✅ Fixed Cancel Button Not Working During Gmail Download
**Root Cause**: Gmail API calls were blocking operations that didn't check cancellation frequently enough.

**Solution Implemented**:
- Added `cancel_check` parameter to `get_email_details()` and `download_attachment()` methods in `src/gmail/processor.py`
- Added cancellation checks before and after each Gmail API call
- Added multiple cancellation checkpoints throughout the attachment processing loop in `src/gmail/downloader.py`
- Enhanced logging to show exactly when and where cancellation occurs

**Files Modified**:
- `src/gmail/processor.py`: Added cancel_check parameters and cancellation logic to API methods
- `src/gmail/downloader.py`: Added extensive cancellation checks in email and attachment processing loops

### 2. ✅ Fixed Cancel Button Not Working During KB File Processing
**Root Cause**: File processing loops and PDF conflict dialogs didn't respect cancellation events.

**Solution Implemented**:
- Added cancellation checks before every major file operation (validation, copying/moving, PDF creation)
- Enhanced PDF conflict dialogs to periodically check for cancellation and auto-close if cancelled
- Added cancellation checks during image loading and PDF generation
- Proper resource cleanup when cancellation occurs during image processing

**Files Modified**:
- `src/kb/processor.py`: Added comprehensive cancellation checks throughout file processing workflow

### 3. ✅ Fixed Progress Text Clearing Problem
**Root Cause**: The double-set approach (space then empty) was ineffective for clearing progress text.

**Solution Implemented**:
- Created robust `clear_progress_text()` method using multiple clearing strategies:
  - Unique placeholder text method
  - Widget reconfiguration
  - Pack/unpack to force visual refresh
- Replaced all instances of the old clearing method with the new robust approach

**Files Modified**:
- `src/gui/main_window.py`: Added `clear_progress_text()` method and updated all progress clearing locations

## Comprehensive Testing Completed:

### ✅ Syntax and Import Validation
- All modified Python files pass syntax validation
- All imports work correctly
- No breaking changes introduced

### ✅ Cancellation Logic Testing
- Threading.Event cancellation mechanism verified working
- Both Gmail and KB processors correctly respond to cancellation events
- Proper state management confirmed

### ✅ Integration Testing
- App startup and initialization works correctly
- No regression in existing functionality
- All components properly connected

## Technical Details:

### Cancellation Implementation Strategy
1. **Frequent Checkpoint Pattern**: Added cancellation checks at all critical points in processing loops
2. **API Wrapper Pattern**: Modified Gmail API calls to accept and use cancel_check callbacks
3. **Resource Cleanup Pattern**: Ensured proper cleanup of resources (file handles, images) when cancellation occurs
4. **Dialog Cancellation Pattern**: Made modal dialogs responsive to cancellation events

### Progress Text Clearing Strategy
1. **Multi-method Approach**: Uses three different clearing techniques for maximum reliability
2. **Unique Placeholder**: Uses distinctive text that won't match existing content
3. **Widget Refresh**: Forces complete visual refresh of the progress label

### Enhanced Logging
- Added detailed cancellation logging to track exactly where and when cancellation occurs
- Improved error handling and reporting throughout the cancellation flow

## Files Modified Summary:
- `src/gmail/processor.py` - Enhanced with cancellation-aware API methods
- `src/gmail/downloader.py` - Added comprehensive cancellation checkpoints
- `src/kb/processor.py` - Implemented thorough cancellation support in file processing
- `src/gui/main_window.py` - Fixed progress text clearing and updated cancellation flow

### 4. ✅ Fixed Critical GUI Freezing and Threading Issues (2025-07-17)
**Root Cause**: All long-running operations were executing in the main GUI thread, causing the application to freeze when window lost focus, during processing, or when cancel was pressed.

**Solution Implemented**:
- **Background Threading**: Moved entire processing workflow (`run_processing_workflow()`) to background thread
- **Thread-Safe GUI Updates**: All GUI updates now use `self.root.after(0, ...)` to execute safely on main thread
- **Non-Blocking Progress Updates**: Progress bar and status text updates are scheduled on main thread
- **Thread-Safe Cleanup**: Success, error, and cancellation handling all execute safely on main thread
- **Responsive Cancel**: Cancel button now works immediately without blocking GUI

**Technical Implementation**:
- `start_processing()` starts background thread with `threading.Thread(target=self.run_processing_workflow, daemon=True)`
- `update_progress()`, `update_status()`, `gui_update()` - All made thread-safe with `root.after()` scheduling
- `_finalize_processing_success()`, `_finalize_processing_error()`, `_cleanup_after_cancel_safe()` - Safe completion handlers
- `_handle_no_emails_found()` - Thread-safe no results handling

**Files Modified**:
- `src/gui/main_window.py`: Complete threading architecture overhaul
- `src/gmail/downloader.py`: Enhanced cancellation support for file conflict dialogs
- `src/kb/processor.py`: Path normalization fixes for Excel file handling

**Benefits Achieved**:
- ✅ **No GUI Freezing**: Application remains responsive when clicking other windows
- ✅ **Immediate Cancel Response**: Cancel button works instantly without delay
- ✅ **Window Movability**: Can move and resize window during processing
- ✅ **Stable Progress Updates**: Smooth progress bar and status text updates
- ✅ **Professional UX**: Application behaves like modern, responsive software

## Comprehensive Testing Completed (2025-07-17):

### ✅ GUI Responsiveness Testing
- Window focus changes during processing: ✅ No freezing
- Cancel button during operations: ✅ Immediate response
- Window moving/resizing during processing: ✅ Fully responsive
- Progress text clearing: ✅ Clean updates without overlay text

### 5. ✅ KB-Specific Workflow Improvements (2025-07-17)
**Enhancement**: Added KB library specific workflow features for processing hundreds of newspaper page images.

**Features Implemented**:
- **Duplicate Detection**: Track files downloaded in current session to prevent duplicate downloads
- **Large PDF Progress Tracking**: Special progress tracking for PDFs with >10 pages
- **Enhanced Dialog Positioning**: All conflict resolution dialogs center over application window
- **Scrollable Conflict Dialogs**: Support for long content with scrollbars

**Implementation Details**:
- `DownloadManager.downloaded_in_session` - Set to track files downloaded in current session
- `check_duplicate_in_session()` - Silent skip for files already downloaded
- Large PDF sub-progress tracking with detailed loading and creation progress
- Dialog positioning calculation to center over parent window instead of screen
- Canvas and scrollbar implementation for overflow content

**Files Modified**:
- `src/gmail/downloader.py`: Added session duplicate tracking and enhanced dialog positioning
- `src/kb/processor.py`: Added large PDF progress tracking and cancellation-aware dialogs

### 6. ✅ User Interface Refinements (2025-07-17)
**Enhancement**: Professional UI improvements based on user feedback for production use.

**Improvements Implemented**:
- **Auto-Linking Visualization**: Gray out auto-linked fields to show they're not manually editable
- **Consistent Entry Field Appearance**: Removed readonly state differences for uniform look
- **Optimal Window Sizing**: Increased help window sizes by 25% for better readability
- **Dialog Size Optimization**: Proper sizing for conflict resolution dialogs with scrollbar support
- **Result Text Improvements**: Enhanced summary messages and formatting

**Technical Implementation**:
- Auto-linked fields shown with gray background (`#f0f0f0`) when populated automatically
- Entry fields maintain consistent appearance across all input types
- Help dialog heights increased to 485px and 405px for comfortable reading
- Improved text formatting in result summaries and status updates

**Files Modified**:
- `src/gui/main_window.py`: UI consistency improvements and auto-linking visualization
- `src/gmail/downloader.py`: Dialog sizing and positioning refinements
- `src/kb/processor.py`: Enhanced dialog layouts and conflict resolution

### 7. ✅ Configuration and Settings Management (2025-07-17)
**Enhancement**: Improved default behavior and configuration persistence.

**Features Implemented**:
- **Smart Default Settings**: "Delete original files" switch always starts enabled for KB processing
- **Enhanced Field Linking**: Visual feedback when fields are auto-populated from other tools
- **Persistent Configuration**: Maintains user preferences between sessions appropriately

**Implementation Details**:
- Modified default configuration to enable delete_originals by default
- Auto-linking behavior clearly communicated through visual cues
- Configuration saves important user choices while resetting per-session behaviors

**Files Modified**:
- `src/gui/main_window.py`: Default configuration and auto-linking behavior

## Latest Development Status (2025-07-17)

### ✅ All Critical Issues Resolved
- **GUI Threading**: Complete responsive GUI with background processing
- **Cancel Functionality**: Immediate cancellation support throughout all operations
- **Progress Tracking**: Accurate progress updates including large PDF sub-progress
- **KB Workflow**: Professional features for processing hundreds of newspaper images
- **User Interface**: Polished, consistent UI with proper visual feedback
- **Configuration**: Smart defaults and persistent settings management

## Final Result:
**The application is now production-ready with professional-grade responsiveness, comprehensive cancellation support, and specialized workflow features for KB (Kungliga biblioteket) newspaper processing. All GUI freezing issues are resolved, the cancel button works immediately throughout all operations, duplicate detection prevents redundant downloads, and the interface provides clear visual feedback for auto-linked fields and processing progress. The application handles hundreds of newspaper page images efficiently with proper resource management and user-friendly conflict resolution.**