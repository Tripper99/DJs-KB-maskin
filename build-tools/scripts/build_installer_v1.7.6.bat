@echo off
REM Build installer for DJs KB-maskin v1.7.6
REM This script builds the installer using Inno Setup

echo ====================================
echo Building DJs KB-maskin v1.7.6 Installer
echo ====================================
echo.

REM Set paths
set PROJECT_ROOT=%~dp0..\..
set ISS_FILE=%PROJECT_ROOT%\build-tools\inno-setup\DJs_KB_maskin_setup_v1.7.6.iss
set OUTPUT_DIR=%PROJECT_ROOT%\dist
set EXE_FILE=%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6.exe

REM Check if executable exists
if not exist "%EXE_FILE%" (
    echo ERROR: Executable not found^^!
    echo Please build the executable first using build_exe_v1.7.6.bat
    echo Expected file: "%EXE_FILE%"
    exit /b 1
)

REM Try to find Inno Setup compiler
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else (
    echo ERROR: Inno Setup 6 not found!
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    exit /b 1
)

echo Found Inno Setup: %ISCC%
echo.

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Build installer
echo Building installer...
echo Using script: %ISS_FILE%
echo.

%ISCC% "%ISS_FILE%"

REM Check if build was successful
if exist "%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6_setup.exe" (
    echo.
    echo ====================================
    echo BUILD SUCCESSFUL!
    echo ====================================
    echo Installer created: %OUTPUT_DIR%\DJs_KB_maskin_v1.7.6_setup.exe
    
    REM Get file size
    setlocal EnableDelayedExpansion
    for %%A in ("%OUTPUT_DIR%\DJs_KB_maskin_v1.7.6_setup.exe") do (
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