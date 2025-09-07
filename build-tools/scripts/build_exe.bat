@echo off
REM Build script for DJs KB-maskin executable
REM Version: 1.6.0
REM Created: 2025-09-07

echo ========================================
echo Building DJs KB-maskin v1.6.0 executable
echo ========================================
echo.

REM Navigate to project root
cd /d "%~dp0\..\.."

REM Clean previous build artifacts
echo Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "build-tools\output\exe\DJs_KB_maskin_v1.6.0.exe" del /q "build-tools\output\exe\DJs_KB_maskin_v1.6.0.exe"

REM Run PyInstaller
echo.
echo Running PyInstaller...
echo ------------------------
pyinstaller --distpath "build-tools\output\exe" --workpath "build" "build-tools\pyinstaller\DJs_KB_maskin_v1.6.0.spec"

REM Check if build was successful
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Build failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

REM Clean up build artifacts
echo.
echo Cleaning up build artifacts...
if exist "build" rmdir /s /q "build"

echo.
echo ========================================
echo Build completed successfully!
echo Executable location: build-tools\output\exe\DJs_KB_maskin_v1.6.0.exe
echo ========================================
echo.
pause