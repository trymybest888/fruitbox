@echo off
REM Build FruitBox.exe (single file, no console) into the dist\ folder.
cd /d "%~dp0"

echo [1/3] Installing requirements...
python -m pip install -r requirements.txt || goto :error

echo [2/3] Generating sounds and icon...
python tools\make_assets.py || goto :error

echo [3/3] Packaging with PyInstaller...
python -m PyInstaller --noconfirm --clean FruitBox.spec || goto :error

echo.
echo Done!  ->  dist\FruitBox.exe
goto :eof

:error
echo Build failed.
exit /b 1
