@echo off

rem This script automates the PyInstaller executable building process

set EXEC_NAME=parser
if not "%1"=="" set EXEC_NAME=%1

set DB_FILE=src/resources/database.db
set SCHEMA_FILE=src/resources/measure.schema.json

cd %~dp0\..
call pyinstaller --clean --noconsole -y -n "%EXEC_NAME%"^
 --icon=src/assets/app.ico^
 --add-data="%DB_FILE%;src/resources"^
 --add-data="%SCHEMA_FILE%;src/resources"^
 cli.py
