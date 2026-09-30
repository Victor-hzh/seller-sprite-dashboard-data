@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo [1/2] 构建静态网站...
call npm run build
if errorlevel 1 goto :failed

echo.
echo [2/2] 上传 out 到阿里云 OSS...
python scripts\deploy_oss.py --directory out
if errorlevel 1 goto :failed

echo.
echo 发布完成：https://sellersprite.uwant.cc/
pause
exit /b 0

:failed
echo.
echo 发布失败。请阅读上方错误信息，窗口会保持打开。
pause
exit /b 1
