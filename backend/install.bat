@echo off
rem 学生刷脸考勤系统 - 后端依赖安装脚本（首次运行）

cd /d "%~dp0"
echo ============================================
echo   安装后端依赖（首次运行需要）
echo ============================================

rem 用系统 Python 3.11 创建虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo 正在创建虚拟环境...
    "D:\python311\python.exe" -m venv ".venv"
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败，请确认 D:\python311\python.exe 存在
        pause
        exit /b 1
    )
)

echo 正在安装依赖（约需几分钟，请耐心等待）...
".venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 依赖安装完成！现在可以双击 start.bat 启动服务。
pause
