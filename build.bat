@echo off
echo ========================================
echo  盲人按摩店排班系统 - 打包脚本
echo ========================================
echo.

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

echo 开始打包...
pyinstaller --onefile --windowed --name "按摩店排班系统" --add-data "gui;gui" main.py

echo.
if exist "dist\按摩店排班系统.exe" (
    echo ✅ 打包成功！
    echo 输出文件: dist\按摩店排班系统.exe
) else (
    echo ❌ 打包失败，请检查错误信息
)

pause
