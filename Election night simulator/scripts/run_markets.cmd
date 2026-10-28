@echo off
rem Wrapper for the Windows scheduled tasks ElectionSim-Markets*. Arguments pass through to capture_markets.py.
cd /d "%~dp0.."
if not exist "data\raw\markets" mkdir "data\raw\markets"
echo ==== %date% %time% capture_markets.py %* >> "data\raw\markets\capture.log"
py scripts\capture_markets.py %* >> "data\raw\markets\capture.log" 2>&1
