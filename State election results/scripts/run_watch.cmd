@echo off
rem Wrapper for the Windows scheduled task StateResults-SourceWatch.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
echo ==== %date% %time% >> "sources\watch.log"
py scripts\watch_sources.py >> "sources\watch.log" 2>&1
