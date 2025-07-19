@echo off
echo Installing Python packages...
powershell -ExecutionPolicy Bypass -File "%~dp0install_dependencies.ps1"

echo.
echo Installing ArgyllCMS...

set ARGYLL_URL=https://www.argyllcms.com/Argyll_V2.3.1_win64_exe.zip
set ARGYLL_DIR=%~dp0..\argyll

mkdir %ARGYLL_DIR%
powershell -Command "Invoke-WebRequest %ARGYLL_URL% -OutFile argyll.zip"
powershell -Command "Expand-Archive -Path argyll.zip -DestinationPath %ARGYLL_DIR%"
del argyll.zip

echo.
echo Adding ArgyllCMS to PATH (current session only)...
set PATH=%ARGYLL_DIR%\Argyll_V2.3.1_win64\bin;%PATH%

echo.
echo ✅ Installation complete!
pause
