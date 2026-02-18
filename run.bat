@echo off
setlocal
pushd "%~dp0"
python -m src.main %*
set exit_code=%ERRORLEVEL%
popd
endlocal & exit /b %exit_code%
