@rem ---------- Console and project location ----------
@echo off
rem Keep environment variables local to this launcher.
setlocal
rem Enable readable Python output while keeping this file ASCII.
chcp 65001 >nul
rem Preserve the original directory and use the project directory.
pushd "%~dp0"

rem ---------- Locate the existing dedicated environment ----------
rem Share environment selection with the test launcher.
call "%~dp0scripts\find_python.cmd"
rem Stop if the selected interpreter does not exist.
if errorlevel 1 goto missing_environment
rem Allow the existing desktop-window test to verify this launcher.
if /i "%~1"=="--test-window" goto test_window
rem Start the normal interface without user-level packages.
"%rubik_selected_python%" -s main.py
rem Continue to the shared result handling after the interface closes.
goto finished

rem ---------- Desktop-window verification ----------
rem This optional branch opens and closes the existing test window.
:test_window
rem Use the same environment and the real interface constructor.
"%rubik_selected_python%" -s -m tests.window_smoke

rem ---------- Preserve the Python result ----------
rem Normal startup and verification share this result handler.
:finished
rem Save the exit code before pause or directory restoration changes it.
set "rubik_exit=%errorlevel%"
rem Keep failures visible for inspection.
if not "%rubik_exit%"=="0" pause
rem Restore the original working directory.
popd
rem Return the original Python exit code.
exit /b %rubik_exit%

rem ---------- Missing environment feedback ----------
rem Only an absent selected interpreter reaches this branch.
:missing_environment
rem Use ASCII feedback so script parsing never depends on encoding.
echo See README.md for the conda environment setup.
rem Keep the error visible.
pause
rem Restore the original working directory.
popd
rem Signal that startup failed without installing anything.
exit /b 1
