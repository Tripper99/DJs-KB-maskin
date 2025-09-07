@echo off
REM Build script for DJs KB-maskin Inno Setup installer
REM Version: 1.6.0
REM Created: 2025-09-07

echo ==========================================
echo Building DJs KB-maskin v1.6.0 installer
echo ==========================================
echo.

REM Navigate to project root
cd /d "%~dp0\..\.."

REM Check if executable exists
if not exist "build-tools\output\exe\DJs_KB_maskin_v1.6.0.exe" (
    echo ERROR: Executable not found!
    echo Please run build_exe.bat first to create the executable.
    pause
    exit /b 1
)

REM Check if Inno Setup is installed
set INNO_PATH=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else (
    echo ERROR: Inno Setup 6 not found!
    echo Please install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo.
    echo If Inno Setup is installed in a custom location, please update this script.
    pause
    exit /b 1
)

echo Found Inno Setup at: %INNO_PATH%
echo.

REM Compile the installer
echo Compiling installer...
echo ------------------------
"%INNO_PATH%" "build-tools\inno-setup\DJs_KB_maskin_setup.iss"

REM Check if compilation was successful
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Installer compilation failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Installer created successfully!
echo Location: build-tools\output\installer\
echo ==========================================
echo.

REM List the created installer file
dir /b "build-tools\output\installer\*.exe" 2>nul
echo.
pause