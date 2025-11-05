# Requires -Version 5.1

param(
  [string]$PythonPath = "venv\Scripts\python.exe",
  [string]$WorkingDir = (Resolve-Path "..").Path,
  [int]$IntervalMinutes = 60,
  [string]$TaskName = "MyBlogPipeline"
)

$ErrorActionPreference = "Stop"

# 작업 디렉터리 기준 실행 인자 구성
$scriptPath = "scripts\run_scheduler.py"

Write-Host "Registering Windows Scheduled Task: $TaskName"
Write-Host "Python: $PythonPath"
Write-Host "WorkingDir: $WorkingDir"

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $scriptPath -WorkingDirectory $WorkingDir
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)

try {
  # 기존 태스크 제거(있다면)
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
} catch {}

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "YouTube/Gmail 수집 및 포스팅 자동화" | Out-Null

Write-Host "Done. Task '$TaskName' registered."


