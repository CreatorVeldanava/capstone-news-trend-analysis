
@echo off
setlocal

cd /d "%~dp0"

if not exist "logs" mkdir "logs"

echo.>> "logs\fetch_news.log"
echo ============================================================>> "logs\fetch_news.log"
echo Waktu mulai: %date% %time%>> "logs\fetch_news.log"
echo ============================================================>> "logs\fetch_news.log"

".venv\Scripts\python.exe" "data-engineering\fetch_news.py" >> "logs\fetch_news.log" 2>&1

set "RESULT=%ERRORLEVEL%"

echo Waktu selesai: %date% %time%>> "logs\fetch_news.log"
echo Exit code: %RESULT%>> "logs\fetch_news.log"

endlocal & exit /b %RESULT%
