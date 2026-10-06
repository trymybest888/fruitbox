@echo off
REM Build FruitBox.exe (single file, no console) into the dist\ folder.
cd /d "%~dp0"

REM Sounds/icon are already in assets\ (regenerate with: python tools\make_assets.py)
echo [1/2] Installing requirements...
python -m pip install -r requirements.txt || goto :error

echo [2/2] Packaging with PyInstaller...
python -m PyInstaller --noconfirm --clean FruitBox.spec || goto :error

echo.
echo Done!  ->  dist\FruitBox.exe
goto :eof

:error
echo Build failed.
exit /b 1
