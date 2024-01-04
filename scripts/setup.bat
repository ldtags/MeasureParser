@echo off

rem This script is used for setting up a development environment

set VIRTUAL_ENV=.venv
if not "%1"=="" set VIRTUAL_ENV=%1

cd %~dp0\..
call python -m venv %VIRTUAL_ENV%
call .\%VIRTUAL_ENV%\Scripts\activate.bat
call pip install -r requirements.txt
move %VIRTUAL_ENV%\Scripts\pip_autoremove.py %VIRTUAL_ENV%\Lib\site-packages
call python -m pip install --upgrade pip