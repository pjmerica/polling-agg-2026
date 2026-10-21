@echo off
rem Wrapper for the Windows scheduled tasks (StateResults-*). Arguments pass through to capture_live.py.
cd /d "%~dp0.."
if not exist "data\raw\live" mkdir "data\raw\live"
echo ==== %date% %time% capture_live.py %* >> "data\raw\live\capture.log"
py scripts\capture_live.py %* >> "data\raw\live\capture.log" 2>&1
