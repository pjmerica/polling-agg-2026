@echo off
rem Election night: open the dashboard and keep the projector writing its data every 30 s.
rem Leave this window open all night (Ctrl+C stops it). The page reloads its data every 15 s.
cd /d "%~dp0..\.."
start "" "%~dp0..\dashboard.html"
py "Election night simulator\scripts\live_project.py" --watch 30
