# MeasureParser
A command-line driven measure parsing application

## Initial Setup (do this before anything else)
  1. Navigate to the root directory of the application in your CLI
  2. Run the command  *pip install -r requirements.txt*

## Running the Script
  1. Navigate to the src/measure_parser directory or the location of the executable in your CLI
  2. Execute main with the file path to the eTRM measure JSON file as an argument

### Flags
  - -console
    - redirects all output to the console

## Building the Executable
  1. Navigate to the root directory of the application in your CLI
  2. Run the command  *pyinstaller [path to main python file] --noconfirm*

When built, the executable will be in the main folder in the newly created directory *dist*
