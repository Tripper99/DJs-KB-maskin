@echo off
REM Build executable for DJs KB-maskin v1.7.6
REM This script builds the standalone executable using PyInstaller

echo ====================================
echo Building DJs KB-maskin v1.7.6 EXE
echo ====================================
echo.

REM Set paths
set PROJECT_ROOT=%~dp0..\..
set SPEC_FILE=%PROJECT_ROOT%\build-tools\pyinstaller\DJs_KB_maskin_v1.7.6.spec
set OUTPUT_DIR=%PROJECT_ROOT%\dist

REM Clean previous builds
echo Cleaning previous builds...
if exist "%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6.exe" (
    del "%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6.exe"
    echo Removed old executable
)

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    echo Created output directory
)

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Build with PyInstaller
echo.
echo Building executable with PyInstaller...
echo Using spec file: %SPEC_FILE%
echo.

pyinstaller --clean --noconfirm "%SPEC_FILE%"

REM Check if build was successful
if exist "%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6.exe" (
    echo.
    echo ====================================
    echo BUILD SUCCESSFUL!
    echo ====================================
    echo Executable created: %OUTPUT_DIR%\DJs_KB_maskin_v1.7.6.exe
    
    REM Get file size - fixed for paths with parentheses
    setlocal EnableDelayedExpansion
    for %%A in ("%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6.exe") do (
        set SIZE=%%~zA
        set /a SIZE_MB=!SIZE! / 1048576
        echo File size: ~!SIZE_MB! MB
    )
    endlocal
) else (
    echo.
    echo ====================================
    echo BUILD FAILED!
    echo ====================================
    echo Please check the error messages above.
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul