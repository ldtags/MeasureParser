# Measure Parser
Make eTRM measure QA/QC simple with this tool!

## Overview
The Measure Parser is a Python-based application that aims to automate eTRM measure QA/QC.

Various Batch scripts are provided in the **scripts** directory which simplify the setup and execution processes.

## OS Support
Currently, the Measure Parser only supports Windows 10/11. There are no plans to provide support to Unix-based systems in the near future.

## Upcoming Features
As of March 27th, 2024, this tool is under development. New enhancements are on the way!

Enhancements and Bug Fixes:
- [ ] Permutation QA/QC Support
  - The existing permutation QA/QC macro will be implemented into the Measure Parser, placing all of your QA/QC tools in one location!
- [ ] Direct eTRM connection
  - Instead of being forced to process the JSON file of a measure, users will be able to select a measure to be parsed by entering its version ID.

## Batch Scripts
### setup
Simplify the development environment setup process by running this batch script. A Python virtual environment, named .venv, will be created at the root of this project directory. All dependencies will be installed from the **requirements.txt** file.


### build
Build the Measure Parser executable by running this script. The resulting build will be found in the newly-created **dist** directory as a folder named **parser**.
