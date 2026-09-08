@echo off
title Forex & Gold AI Live Trading Terminal
echo ====================================================
echo  Starting Forex & Gold AI Live Trading Terminal...
echo ====================================================
cd /d "%~dp0"
start http://localhost:5000
python server.py
pause
