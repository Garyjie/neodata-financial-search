@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM NeoData 金融数据查询 - Windows CMD 封装
REM
REM Usage:
REM   query.cmd "腾讯最新财报"
REM   query.cmd "贵州茅台股价"
REM   query.cmd "上证指数"
REM
REM 环境变量:
REM   NEODATA_TIMEOUT - 超时时间(秒) (默认: 15)

if "%~1"=="" (
    echo 用法: query.cmd ^<query^>
    echo 示例:
    echo   query.cmd "贵州茅台股价"
    echo   query.cmd "上证指数"
    echo   query.cmd "比亚迪"
    exit /b 1
)

set "QUERY=%~1"

if not defined NEODATA_TIMEOUT set "NEODATA_TIMEOUT=15"

REM 调用 Python 脚本
python "%~dp0query.py" --query "%QUERY%" --timeout %NEODATA_TIMEOUT%

if errorlevel 1 (
    echo 查询失败 >&2
    exit /b 1
)

endlocal
