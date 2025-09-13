@echo off
REM Build both executable and installer for DJs KB-maskin v1.7.4
REM This script runs both build steps in sequence

echo ====================================
echo Building DJs KB-maskin v1.7.4
echo Complete Build Process
echo ====================================
echo.

REM Set script directory
set SCRIPT_DIR=%~dp0

REM Step 1: Build executable
echo Step 1: Building executable...
echo ====================================
call "%SCRIPT_DIR%build_exe_v1.7.4.bat"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Executable build failed!
    echo Stopping build process.
    pause
    exit /b 1
)

echo.
echo Step 1 completed successfully!
echo.
echo ====================================
echo.

REM Step 2: Build installer
echo Step 2: Building installer...
echo ====================================
call "%SCRIPT_DIR%build_installer_v1.7.4.bat"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Installer build failed!
    pause
    exit /b 1
)

echo.
echo ====================================
echo COMPLETE BUILD SUCCESSFUL!
echo ====================================
echo.
echo Build artifacts created:
echo - Executable: build-tools\output\exe\DJs_KB_maskin_v1.7.4.exe
echo - Installer: build-tools\output\installer\DJs_KB_maskin_v1.7.4_setup.exe
echo.
echo The installer is ready for distribution!
echo.
echo Press any key to exit...
pause >nul