@echo off
rem Election night: the projector (every 30 s), the home server for your phone, and the delayed public copy.
rem Leave these windows open all night (Ctrl+C in each stops it).
cd /d "%~dp0..\.."
start "Home server" py "Election night simulator\scripts\serve_home.py"
start "Public copy" py "Election night simulator\scripts\publish_live.py"
start "" "%~dp0..\dashboard.html"
py "Election night simulator\scripts\live_project.py" --watch 30
