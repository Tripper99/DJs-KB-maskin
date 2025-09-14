@echo off
REM Build complete package for DJs KB-maskin v1.7.6
REM This script builds both the executable and the installer

echo ====================================
echo Building DJs KB-maskin v1.7.6 Complete Package
echo ====================================
echo.

REM Set paths
set PROJECT_ROOT=%~dp0..\..
set SCRIPTS_DIR=%~dp0

REM Build executable
echo Step 1: Building executable...
echo --------------------------------
call "%SCRIPTS_DIR%build_exe_v1.7.6.bat"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Executable build failed!
    exit /b 1
)

echo.
echo Step 2: Building installer...
echo --------------------------------
call "%SCRIPTS_DIR%build_installer_v1.7.6.bat"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Installer build failed!
    exit /b 1
)

echo.
echo ====================================
echo COMPLETE BUILD SUCCESSFUL!
echo ====================================
echo.
echo Build artifacts:
echo - Executable: %PROJECT_ROOT%\dist\DJs_KB_maskin_v1.7.6.exe
echo - Installer: %PROJECT_ROOT%\dist\DJs_KB_maskin_v1.7.6_setup.exe
echo.
echo Press any key to exit...
pause >nul