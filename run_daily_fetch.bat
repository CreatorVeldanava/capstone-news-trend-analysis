@echo off
setlocal

cd /d "%~dp0"
if errorlevel 1 goto root_failed

if not exist "logs\" mkdir "logs" 2>nul
if not exist "logs\" goto log_directory_failed

set "LOG_TEST_TOKEN=LOG_WRITE_TEST_%RANDOM%_%RANDOM%"
>> "logs\fetch_news.log" echo Pemeriksaan akses tulis log: %LOG_TEST_TOKEN%

findstr /L /C:"%LOG_TEST_TOKEN%" "logs\fetch_news.log" >nul
if errorlevel 1 goto log_write_failed

>> "logs\fetch_news.log" echo.

echo ============================================================>> "logs\fetch_news.log"
echo PROSES PENGAMBILAN DAN PREPROCESSING BERITA>> "logs\fetch_news.log"
echo Waktu mulai: %date% %time%>> "logs\fetch_news.log"
echo ============================================================>> "logs\fetch_news.log"

REM ============================================================
REM PREFLIGHT CHECK
REM ============================================================

if not exist ".venv\Scripts\python.exe" goto missing_python
if not exist "data-engineering\fetch_news.py" goto missing_fetch
if not exist "data-engineering\preprocess_news.py" goto missing_preprocess
if not exist "data\news.db" goto missing_database

echo PREFLIGHT CHECK: SEMUA DEPENDENSI TERSEDIA.>> "logs\fetch_news.log"

REM ============================================================
REM TAHAP 1: FETCH RSS
REM ============================================================

echo.>> "logs\fetch_news.log"
echo [TAHAP 1] PENGAMBILAN BERITA RSS>> "logs\fetch_news.log"

".venv\Scripts\python.exe" "data-engineering\fetch_news.py" >> "logs\fetch_news.log" 2>&1

set "FETCH_RESULT=%ERRORLEVEL%"
>> "logs\fetch_news.log" echo Exit code pengambilan RSS: %FETCH_RESULT%

REM ============================================================
REM TAHAP 2: PREPROCESSING
REM Tetap dijalankan meskipun fetch gagal.
REM ============================================================

echo.>> "logs\fetch_news.log"
echo [TAHAP 2] PREPROCESSING BERITA>> "logs\fetch_news.log"

".venv\Scripts\python.exe" "data-engineering\preprocess_news.py" >> "logs\fetch_news.log" 2>&1

set "PREPROCESS_RESULT=%ERRORLEVEL%"
>> "logs\fetch_news.log" echo Exit code preprocessing: %PREPROCESS_RESULT%

REM ============================================================
REM PENENTUAN STATUS AKHIR
REM ============================================================

if not "%PREPROCESS_RESULT%"=="0" goto preprocess_failed
if not "%FETCH_RESULT%"=="0" goto fetch_failed

set "RESULT=0"
echo STATUS AKHIR: PENGAMBILAN DAN PREPROCESSING BERHASIL.>> "logs\fetch_news.log"
goto finish

:preprocess_failed
set "RESULT=%PREPROCESS_RESULT%"
echo STATUS AKHIR: PREPROCESSING GAGAL.>> "logs\fetch_news.log"
if not "%FETCH_RESULT%"=="0" echo Pengambilan RSS juga mengalami kegagalan.>> "logs\fetch_news.log"
goto finish

:fetch_failed
set "RESULT=%FETCH_RESULT%"
echo STATUS AKHIR: PENGAMBILAN RSS BERMASALAH, PREPROCESSING TELAH DIJALANKAN.>> "logs\fetch_news.log"
goto finish

:missing_python
set "PREFLIGHT_ERROR=Python virtual environment tidak ditemukan."
goto preflight_failed

:missing_fetch
set "PREFLIGHT_ERROR=Script fetch_news.py tidak ditemukan."
goto preflight_failed

:missing_preprocess
set "PREFLIGHT_ERROR=Script preprocess_news.py tidak ditemukan."
goto preflight_failed

:missing_database
set "PREFLIGHT_ERROR=Database data\news.db tidak ditemukan."
goto preflight_failed

:preflight_failed
set "RESULT=10"
echo PREFLIGHT GAGAL: %PREFLIGHT_ERROR%>> "logs\fetch_news.log"
echo STATUS AKHIR: PROSES DIBATALKAN SEBELUM EKSEKUSI.>> "logs\fetch_news.log"
goto finish

:finish
echo.>> "logs\fetch_news.log"
echo Waktu selesai: %date% %time%>> "logs\fetch_news.log"
>> "logs\fetch_news.log" echo Exit code akhir: %RESULT%
echo ============================================================>> "logs\fetch_news.log"

endlocal & exit /b %RESULT%

:log_directory_failed
echo ERROR: Folder logs tidak dapat dibuat.
endlocal & exit /b 11

:log_write_failed
echo ERROR: File log tidak dapat ditulis.
endlocal & exit /b 12

:root_failed
echo ERROR: Direktori project tidak dapat diakses.
endlocal & exit /b 13
