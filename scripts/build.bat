@echo off

rem This script automates the PyInstaller executable building process

set SPEC_NAME=parser
if not "%1"=="" set SPEC_NAME=%1

set DB_FILE=measureparser/data/database.db
set SCHEMA_FILE=measureparser/data/measure.schema.json

cd %~dp0\..
call pyinstaller --clean --noconsole -y -n "%SPEC_NAME%"^
 --add-data="%DB_FILE%;measureparser/data"^
 --add-data="%SCHEMA_FILE%;measureparser/data"^
 measureparser/__main__.py