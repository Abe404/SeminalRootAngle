# SeminalRootAngle
GUI application to measure seminal root angle from segmentations

### Development and Build process
The application is developed and built with python 3.9

#### To setup the development environment on OSX with python3.9

Create virtual environment (if you haven't already)
> python -m env venv

Activate it 
> source ./env/bin/activate

Install requirements
> pip install -r requirements.txt


#### To run the application from source

This assumues you already have the required dependencies installed from the development environment
> python main.py


#### Building the application.

To create the application using PyInstaller [0], which bundles an application and it's dependencies into a single package.
> python build/freeze.py

To build the installer.
> python build/installer.py


[0] https://pyinstaller.readthedocs.io/en/stable/
