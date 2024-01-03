@echo off

rem This script automates the PyInstaller executable building process

set SPEC_NAME=parser
if not "%1"=="" set SPEC_NAME=%1

set DB_FILE=measure_parser\resources\database.db
set SCHEMA_FILE=measure_parser\resources\measure.schema.json

cd %~dp0\..
call pyinstaller --clean -y -n "%SPEC_NAME%"^
 --add-data="%DB_FILE%;resources"^
 --add-data="%SCHEMA_FILE%;resources"^
 measure_parser/main.py