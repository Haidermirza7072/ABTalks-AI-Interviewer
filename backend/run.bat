@echo off
echo ============================================
echo   The Thread Puller - Backend Server
echo ============================================
echo.

cd /d "%~dp0"

:: Check if .venv exists and activate it
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Virtual environment activated.
) else (
    echo [WARN] No .venv found, using system Python.
)

:: Install dependencies if needed
echo.
echo Installing dependencies...
pip install -r requirements.txt -q

:: Run the server
echo.
echo Starting FastAPI server on http://0.0.0.0:8000
echo Swagger docs at http://localhost:8000/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
