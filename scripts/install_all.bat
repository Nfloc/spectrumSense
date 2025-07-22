@echo off
setlocal

echo Installing Python packages...
powershell -ExecutionPolicy Bypass -File "%~dp0install_dependencies.ps1"

echo.
echo Installing ArgyllCMS...

:: Set target path relative to the script directory
set "SCRIPT_DIR=%~dp0"
set "TARGET_DIR=%SCRIPT_DIR%..\argyll"
set "ZIP_URL=https://www.argyllcms.com/Argyll_V2.3.1_win64_exe.zip"
set "ZIP_FILE=argyll.zip"

:: Create target folder
mkdir "%TARGET_DIR%"

:: Download ArgyllCMS
powershell -Command "Invoke-WebRequest '%ZIP_URL%' -OutFile '%ZIP_FILE%'"

:: Extract directly into TARGET_DIR
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TARGET_DIR%'"

:: Delete the downloaded zip
del "%ZIP_FILE%"

:: Clean up accidentally extracted folder (if needed)
if exist "%SCRIPT_DIR%Argyll_V2.3.1_win64" (
    echo Deleting accidental folder in scripts/
    rmdir /s /q "%SCRIPT_DIR%Argyll_V2.3.1_win64"
)

echo.
echo ✅ ArgyllCMS installed to: %TARGET_DIR%
echo.
pause
endlocal
