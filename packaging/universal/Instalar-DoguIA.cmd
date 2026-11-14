@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Instalar-DoguIA.ps1" %*
if errorlevel 1 (
  echo.
  echo A instalação não foi concluída. Confira a mensagem acima.
  pause
  exit /b 1
)
