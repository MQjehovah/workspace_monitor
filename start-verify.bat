@echo off
REM ============================================================
REM  workspace_monitor-master 本地验证启动脚本
REM  在 PowerShell 或 CMD 中运行此脚本
REM ============================================================

echo.
echo ============================================
echo   重大项目监控看板 - 本地验证环境
echo ========================================
echo.

REM ---- Step 1: 检查 Python ----
set PY=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PY%" (
    echo [ERROR] 找不到 managed Python: %PY%
    echo 请先确认 Python 路径
    pause
    exit /b 1
)
echo [OK] Python: %PY%

REM ---- Step 2: 安装/验证依赖 ----
echo.
echo [1/5] 检查后端依赖...
%PY% -m pip install fastapi uvicorn sqlalchemy pydantic python-multipart openpyxl >nul 2>&1
echo [OK] 依赖就绪（含openpyxl用于Excel导入导出）

REM ---- Step 2.5: 删除旧数据库重建（模型有变更） ----
echo.
echo [2/5] 清理旧数据库...
if exist "D:\workspace\workspace_monitor-master\backend\data\bigscreen.db" (
    del /f "D:\workspace\workspace_monitor-master\backend\data\bigscreen.db"
    echo [OK] 已删除旧数据库文件
) else (
    echo [OK] 无旧数据库，跳过
)

REM ---- Step 3: 启动后端 (端口8000) ----
echo.
echo [3/5] 启动后端服务 (http://localhost:8000) ...
echo      Swagger文档: http://localhost:8000/docs
echo.
start "Backend-API" cmd /k "cd /d D:\workspace\workspace_monitor-master\backend && %PY% -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
timeout /t 6 /nobreak >nul

REM ---- Step 3.5: 初始化种子数据 ----
echo.
echo [4/5] 初始化种子数据（项目+目标+里程碑+评分）...
%PY% -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/api/seed',timeout=10); import json; d=json.loads(r.read()); print('[OK]', d['message'])" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] 种子数据初始化失败，请手动访问 http://localhost:8000/api/seed
)

REM ---- Step 5: 启动前端 (端口5173) ----
echo.
echo [5/5] 启动前端开发服务器...
echo      前端地址: http://localhost:5173/project/
echo.
start "Frontend-Dev" cmd /k "cd /d D:\workspace\workspace_monitor-master\frontend && npm run dev"

echo.
echo ============================================
echo   启动完成！
echo ============================================
echo.
echo   前端地址: http://localhost:5173/project/
echo   后端API:  http://localhost:8000/docs
echo.
echo   验证清单:
echo   1. 打开前端首页，确认顶部有"成员专项绩效"+"专项目标"按钮
echo   2. 点"成员专项绩效"进入新页面，检查子团队成员数据+评分规则弹窗
echo   3. 点"专项目标"进入目标管理页，检查目标卡片+编辑目标值+批量导入
echo   4. 进入某项目详情 - 目标Tab应有8列(含当月实际/完成率等)
echo   5. 项目详情 - 子团队Tab每个成员应显示彩色评分徽章
echo   6. 打开后台管理(/admin)，检查目标的4个新列和扩展评分弹窗
echo   7. 目标管理页点"下载模板"，再点"批量导入"测试导入功能
echo   8. 打开 http://localhost:8000/docs 确认新API已注册（含batch-import/template）
echo.
echo   按任意键打开浏览器...
pause >nul

start http://localhost:5173/project/
