@echo off
chcp 65001 >nul
title Workspace Monitor Backend - Keep Alive (Port 8003)

set "PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "WORKDIR=D:\workspace\workspace_monitor-master\backend"
set "PORT=8003"
set "MAX_RESTART=50"
set "RESTART_COUNT=0"

echo ========================================
echo   Workspace Monitor 后端保活服务
echo   端口: %PORT%
echo   工作目录: %WORKDIR%
echo   最大重启次数: %MAX_RESTART%
echo ========================================
echo.

:LOOP
REM 检查端口是否在监听
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    REM 端口正常，等待5秒再检查
    timeout /t 5 /nobreak >nul
    goto :LOOP
)

REM 端口不在监听，需要启动或重启
set /a RESTART_COUNT+=1
if %RESTART_COUNT% GTR %MAX_RESTART% (
    echo [%date% %time%] 已达到最大重启次数 %MAX_RESTART%，停止保活
    goto :EOF
)

echo [%date% %time%] 检测到后端服务未运行，正在启动... (第 %RESTART_COUNT% 次)

REM 先清理可能残留的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% "') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM 启动后端服务（使用 start 在新窗口中后台运行）
start "UVICORN-8003" /MIN "%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload

REM 等待服务就绪
echo [%date% %time%] 等待服务启动...
timeout /t 8 /nobreak >nul

REM 验证是否启动成功
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 后端服务启动成功！
) else (
    echo [%date% %time%] 警告：后端可能未能正常启动，10秒后重试...
    timeout /t 10 /nobreak >nul
)

goto :LOOP
