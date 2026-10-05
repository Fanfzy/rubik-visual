@rem ---------- Select an existing Python interpreter ----------
@rem Return rubik_selected_python to the calling launcher without installing anything.
@set "rubik_selected_python="
@rem An explicit interpreter always has the highest priority.
@if defined RUBIK_PYTHON goto explicit_python
@rem Prefer the environment the user intentionally activated.
@if defined CONDA_PREFIX goto active_conda
@rem Preserve the original double-click setup on the maintainer's computer.
@set "rubik_selected_python=D:\conda_envs\rubik_visual\python.exe"
@rem Validate the selected file before starting any program.
@goto verify_python

@rem ---------- Explicit configuration ----------
:explicit_python
@rem RUBIK_PYTHON contains a full path without surrounding quotes.
@set "rubik_selected_python=%RUBIK_PYTHON%"
@rem Do not silently replace a wrong explicit setting.
@goto verify_python

@rem ---------- Activated conda environment ----------
:active_conda
@rem Windows conda environments keep python.exe at their root.
@set "rubik_selected_python=%CONDA_PREFIX%\python.exe"

@rem ---------- Verify and report the result ----------
:verify_python
@rem A successful caller receives both the path and exit code zero.
@if exist "%rubik_selected_python%" exit /b 0
@rem Use ASCII text so cmd parsing never depends on its code page.
@echo Python interpreter not found: %rubik_selected_python%
@rem Explain how other users can choose their own environment.
@echo Activate rubik_visual with conda, or set RUBIK_PYTHON to its python.exe.
@rem Fail explicitly instead of using base or a user-level Python.
@exit /b 1
