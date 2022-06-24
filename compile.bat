@echo off

:: Get the current directory
set batdir=%~dp0

pyinstaller --clean --onefile --name "Get Weathers" --add-data "%batdir%fonts\*ttf;fonts\." --icon "%batdir%weather.ico" "%batdir%main.py"