@echo off
TITLE Run Coletor App

echo Changing directory to the project's src folder...
cd C:\Users\Gui\coletor\src

echo.
echo Starting the Flet app...

REM We run "flet run" without "--ios" because .bat files are for Windows.
flet run

echo.
echo The app window might be open. The script will close when you close the app window.
pause
