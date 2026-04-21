@echo off
:: The 'timeout' gives a tiny buffer, and 'start' creates a totally independent process
start "" cmd /c "timeout /t 1 /nobreak && taskkill /F /IM python.exe"
exit