@rem ---------- Console and project location ----------
@echo off
rem Keep environment variables local to this launcher.
setlocal
rem Enable readable Python output while keeping this file ASCII.
chcp 65001 >nul
rem Preserve the original directory and use the project directory.
pushd "%~dp0"

rem ---------- Locate the existing dedicated environment ----------
rem Use the same interpreter selection as normal startup.
call "%~dp0scripts\find_python.cmd"
rem Stop if the chosen interpreter is unavailable.
if errorlevel 1 goto missing_environment

rem ---------- Full acceptance tests ----------
rem Execute tests with only the approved environment dependencies.
"%rubik_selected_python%" -s run_tests.py %*
rem Save the test exit code before pausing.
set "rubik_exit=%errorlevel%"
rem Keep test output visible for inspection.
pause
rem Restore the original working directory.
popd
rem Preserve success or failure for callers.
exit /b %rubik_exit%

rem ---------- Missing environment feedback ----------
:missing_environment
rem Refer users to the documented setup without installing packages.
echo See README.md for the conda environment setup.
rem Keep the message visible when launched by double-clicking.
pause
rem Restore the original working directory.
popd
rem Return a clear failure code.
exit /b 1
