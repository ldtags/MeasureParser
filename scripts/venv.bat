rem This script is used for creating, activating and setting up a development environment

if "%1"=="" (
    set VIRTUAL_ENV=.venv
) else (
    set VIRTUAL_ENV=%1
)

cd %~dp0\..
call python -m venv %VIRTUAL_ENV%
call %VIRTUAL_ENV%\Scripts\activate.bat
pip install -r requirements.txt

pause