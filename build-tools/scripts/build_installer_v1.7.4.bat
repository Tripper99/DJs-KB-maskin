@echo off
REM Build installer for DJs KB-maskin v1.7.4
REM This script builds the Inno Setup installer

echo ====================================
echo Building DJs KB-maskin v1.7.4 Installer
echo ====================================
echo.

REM Set paths
set PROJECT_ROOT=%~dp0..\..
set ISS_FILE=%PROJECT_ROOT%\build-tools\inno-setup\DJs_KB_maskin_setup_v1.7.4.iss
set EXE_FILE=%PROJECT_ROOT%\build-tools\output\exe\DJs_KB_maskin_v1.7.4.exe
set OUTPUT_DIR=%PROJECT_ROOT%\build-tools\output\installer

REM Check if executable exists
if not exist "%EXE_FILE%" (
    echo ERROR: Executable not found!
    echo Please run build_exe_v1.7.4.bat first to create the executable.
    echo Expected file: %EXE_FILE%
    echo.
    pause
    exit /b 1
)

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    echo Created installer output directory
)

REM Try to find Inno Setup compiler
set "ISCC="
set "PROGFILES86=%ProgramFiles(x86)%"
set "PROGFILES=%ProgramFiles%"

if exist "%PROGFILES86%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%PROGFILES86%\Inno Setup 6\ISCC.exe"
    goto found_iscc
)
if exist "%PROGFILES%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%PROGFILES%\Inno Setup 6\ISCC.exe"
    goto found_iscc
)
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto found_iscc
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto found_iscc
)

echo ERROR: Inno Setup 6 not found!
echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
echo.
pause
exit /b 1

:found_iscc

echo Found Inno Setup at: "%ISCC%"
echo.

REM Compile the installer
echo Compiling installer...
echo Using script: %ISS_FILE%
echo.

"%ISCC%" "%ISS_FILE%"

REM Check if build was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo INSTALLER BUILD SUCCESSFUL!
    echo ====================================
    echo Installer created: %OUTPUT_DIR%\DJs_KB_maskin_v1.7.4_setup.exe
    
    REM Get file size - fixed for paths with parentheses
    setlocal EnableDelayedExpansion
    if exist "%OUTPUT_DIR%\DJs_KB_maskin_v1.7.4_setup.exe" (
        for %%A in ("%OUTPUT_DIR%\DJs_KB_maskin_v1.7.4_setup.exe") do (
            set SIZE=%%~zA
            set /a SIZE_MB=!SIZE! / 1048576
            echo Installer size: ~!SIZE_MB! MB
        )
    )
    endlocal
) else (
    echo.
    echo ====================================
    echo INSTALLER BUILD FAILED!
    echo ====================================
    echo Please check the error messages above.
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul