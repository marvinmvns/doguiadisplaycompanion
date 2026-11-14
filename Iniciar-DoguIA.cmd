@echo off
chcp 65001 >nul
where py >nul 2>&1
if %errorlevel% equ 0 (
  py -3 "%~dp0iniciar.py"
  if errorlevel 1 pause
  exit /b
)
where python >nul 2>&1
if %errorlevel% equ 0 (
  python "%~dp0iniciar.py"
  if errorlevel 1 pause
  exit /b
)
echo Python não encontrado. Use o instalador DoguIA que já inclui Python.
echo Ou instale Python 3.9+ em https://www.python.org/downloads/windows/
echo Ajuda: https://www.doguia.com.br/ajuda/display/
pause
exit /b 1
