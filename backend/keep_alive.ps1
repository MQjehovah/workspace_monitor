# Workspace Monitor Backend Keep-Alive Script
# 用法: 在 PowerShell 中运行 .\keep_alive.ps1
# 功能: 每5秒检测一次 8003 端口，挂了就自动重启

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$PYTHON = "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
$WORKDIR = "D:\workspace\workspace_monitor-master\backend"
$PORT = 8003
$MAX_RESTART = 100
$restartCount = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Workspace Monitor 后端保活服务" -ForegroundColor Cyan
Write-Host "  端口: $PORT" -ForegroundColor Green
Write-Host "  工作目录: $WORKDIR" -ForegroundColor Green
Write-Host "  最大重启次数: $MAX_RESTART" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    # 检测端口是否在监听
    $listening = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }

    if ($listening) {
        # 正常运行中，每5秒检测一次
        Start-Sleep -Seconds 5
        continue
    }

    # 端口未监听，需要重启
    $restartCount++
    if ($restartCount -gt $MAX_RESTART) {
        Write-Host "[$(Get-Date)] 已达到最大重启次数 $MAX_RESTOP，停止保活" -ForegroundColor Red
        break
    }

    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] 检测到后端服务未运行，正在启动... (第 $restartCount 次)" -ForegroundColor Yellow

    # 清理残留进程
    Get-Process -Name python -ErrorAction SilentlyContinue | ForEach-Object {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        if ($cmd -and $cmd -match "uvicorn.*$PORT") {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Milliseconds 500

    # 启动服务（后台窗口）
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PYTHON
    $psi.Arguments = "-m uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload"
    $psi.WorkingDirectory = $WORKDIR
    $psi.WindowStyle = "Minimized"
    $psi.UseShellExecute = $true
    [System.Diagnostics.Process]::Start($psi) | Out-Null

    Write-Host "[$(Get-Date)] 已发送启动命令，等待服务就绪..." -ForegroundColor Yellow

    # 等待最多15秒让服务起来
    $waited = 0
    while ($waited -lt 15) {
        Start-Sleep -Seconds 1
        $waited++
        $check = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
        if ($check) {
            Write-Host "[$(Get-Date)] 后端服务启动成功！端口 $PORT 已就绪 ✓" -ForegroundColor Green
            break
        }
    }

    if (-not $check) {
        Write-Host "[$(Get-Date)] 警告：后端可能未能正常启动，10秒后将重试..." -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}
