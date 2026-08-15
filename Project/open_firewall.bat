@echo off
:: Self-elevate to admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo Adding firewall rules for SweatSync...
netsh advfirewall firewall add rule name="SweatSync Backend 8000" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="SweatSync Frontend 5173" dir=in action=allow protocol=TCP localport=5173
echo.
echo Done! Firewall rules added. You can close this window.
pause
