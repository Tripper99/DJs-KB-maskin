@echo off
REM Complete build script for DJs KB-maskin
REM Version: 1.6.0
REM Created: 2025-09-07
REM
REM This script builds both the executable and installer

echo ================================================
echo Complete Build Process for DJs KB-maskin v1.6.0
echo ================================================
echo.

REM Navigate to scripts directory
cd /d "%~dp0"

REM Step 1: Build the executable
echo STEP 1: Building executable...
echo ------------------------------
call build_exe.bat
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Executable build failed!
    echo Aborting build process.
    pause
    exit /b 1
)

echo.
echo ================================================
echo.

REM Step 2: Build the installer
echo STEP 2: Building installer...
echo -----------------------------
call build_installer.bat
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Installer build failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo COMPLETE BUILD SUCCESSFUL!
echo ================================================
echo.
echo Output files:
echo - Executable: build-tools\output\exe\DJs_KB_maskin_v1.6.0.exe
echo - Installer:  build-tools\output\installer\DJs_KB_maskin_v1.6.0_setup.exe
echo.
echo The installer is ready for distribution!
echo ================================================
echo.
pause