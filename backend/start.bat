@echo off
rem 学生刷脸考勤系统 - 后端一键启动脚本
rem 双击运行即可启动后端服务，浏览器访问 http://127.0.0.1:8000/docs 查看接口文档

cd /d "%~dp0"
echo ============================================
echo   学生刷脸考勤系统 - 后端启动
echo ============================================

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请先运行 install.bat
    pause
    exit /b 1
)

echo 正在启动服务...
echo 接口文档: http://127.0.0.1:8000/docs
echo 按 Ctrl+C 停止服务
echo.

".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
