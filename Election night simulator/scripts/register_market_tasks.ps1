# Registers the market-price recorder's Windows scheduled tasks (same settings as State election results' StateResults-ElectionNight:
# wake the PC, run on battery, start late if missed, 21-day limit). Run once in PowerShell:
#   powershell -ExecutionPolicy Bypass -File "State election results\scripts\register_market_tasks.ps1"
# Remove after the election with the Unregister line in Election night simulator/README.md (it matches ElectionSim-*).
$cmd = Join-Path $PSScriptRoot 'run_markets.cmd'
$set = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Days 21)
$pr = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
function Reg($name, $trigger, $argz, $desc) {
  $act = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ""' + $cmd + '" ' + $argz + '"')
  Register-ScheduledTask -TaskName $name -Action $act -Trigger $trigger -Settings $set -Principal $pr -Description $desc -Force | Out-Null
}
# one pass a day until election morning: checks every market is still found, and keeps a pre-election baseline
$daily = New-ScheduledTaskTrigger -Daily -At '2026-10-29T09:05:00'
$daily.EndBoundary = '2026-11-03T08:00:00'
Reg 'ElectionSim-MarketsCheck' $daily '--once' 'capture_markets.py one pass: daily check and pre-election baseline'
# election day from noon ET (a baseline before the first polls close) to Friday noon ET, every 20 s
Reg 'ElectionSim-Markets' (New-ScheduledTaskTrigger -Once -At '2026-11-03T12:00:00') '--interval 20 --until 2026-11-06T17:00' 'capture_markets.py every 20 s, Nov 3 noon ET to Nov 6 noon ET'
# late counts (NV, AK, ME ranked-choice), every 5 min
Reg 'ElectionSim-MarketsLate' (New-ScheduledTaskTrigger -Once -At '2026-11-06T12:05:00') '--interval 300 --until 2026-11-26T05:00' 'capture_markets.py every 5 min, Nov 6 to Nov 26'
Get-ScheduledTask -TaskName 'ElectionSim-*' | ForEach-Object { '{0}: starts {1}  {2}' -f $_.TaskName, $_.Triggers[0].StartBoundary, $_.Actions[0].Arguments }
