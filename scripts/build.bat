@echo off

rem This script automates the PyInstaller executable building process

set SPEC_NAME=parser
if not "%1"=="" set SPEC_NAME=%1

set DB_FILE=measureparser/resources/database.db
set SCHEMA_FILE=measureparser/resources/measure.schema.json

cd %~dp0\..
call pyinstaller --clean --noconsole -y -n "%SPEC_NAME%"^
 --add-data="%DB_FILE%;measureparser/resources"^
 --add-data="%SCHEMA_FILE%;measureparser/resources"^
 measureparser/__main__.py