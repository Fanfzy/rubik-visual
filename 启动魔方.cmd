@rem ---------- Console and project location ----------
@echo off
rem Keep launcher variables local.
setlocal
rem Use readable UTF-8 console output while keeping this file ASCII.
chcp 65001 >nul
rem Start from the project directory regardless of the caller's location.
pushd "%~dp0"

rem ---------- Select an existing interpreter ----------
rem A user-specified interpreter has the highest priority.
if defined RUBIK_PYTHON goto explicit_python
rem Prefer the conda environment the user activated.
if defined CONDA_PREFIX goto active_conda
rem Preserve the original double-click environment on this computer.
set "rubik_selected_python=D:\conda_envs\rubik_visual\python.exe"
rem Validate the selected interpreter before starting.
goto launch

rem ---------- Explicit interpreter ----------
:explicit_python
rem Use the supplied path without changing or installing anything.
set "rubik_selected_python=%RUBIK_PYTHON%"
rem Do not silently replace an invalid explicit choice.
goto launch

rem ---------- Activated conda environment ----------
:active_conda
rem Windows conda keeps python.exe at the environment root.
set "rubik_selected_python=%CONDA_PREFIX%\python.exe"

rem ---------- Start the complete interface ----------
:launch
rem Missing interpreters require the documented environment setup.
if not exist "%rubik_selected_python%" goto missing_environment
rem Ignore user-level packages and run the project entry point.
"%rubik_selected_python%" -s main.py
rem Save the Python result before restoring the working directory.
set "rubik_exit=%errorlevel%"
rem Keep failures visible when the user double-clicks the launcher.
if not "%rubik_exit%"=="0" pause
rem Restore the caller's directory.
popd
rem Preserve the original Python success or failure status.
exit /b %rubik_exit%

rem ---------- Missing environment feedback ----------
:missing_environment
rem Explain the missing interpreter using encoding-independent text.
echo Python interpreter not found: %rubik_selected_python%
rem Point to the environment guide without installing dependencies.
echo See README.md. Activate conda or set RUBIK_PYTHON to an existing python.exe.
rem Keep the message visible.
pause
rem Restore the caller's directory.
popd
rem Report failure explicitly.
exit /b 1
