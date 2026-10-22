
@echo off
setlocal

cd /d "%~dp0"

if not exist "logs" mkdir "logs"

".venv\Scripts\python.exe" "fetch_news.py" >> "logs\fetch_news.log" 2>&1

echo.
echo Proses pengumpulan berita selesai.
echo Log tersimpan di logs\fetch_news.log

endlocal
