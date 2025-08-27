@echo off
REM Labhya Compute - Development Startup Script for Windows

echo 🚀 Starting Labhya Compute Platform...

REM Check if we're in the backend directory
if not exist "manage.py" (
    echo ❌ Please run this script from the backend directory
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Check for virtual environment
if not exist "venv" if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
if exist "venv" (
    echo 🔄 Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv" (
    call .venv\Scripts\activate.bat
)

REM Install/upgrade dependencies
echo 📋 Installing dependencies...
pip install -r requirements.txt

REM Run migrations
echo 🗄️  Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create superuser if none exists
echo 👤 Checking for superuser...
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@labhya.com', 'admin123') if not User.objects.filter(is_superuser=True).exists() else print('Superuser already exists')"

REM Clean up any dead tunnels
echo 🔧 Cleaning up any dead tunnels...
python manage.py manage_tunnels --action=cleanup

echo ✅ Setup complete!
echo.
echo 🌐 Starting Django development server...
echo    Backend API: http://localhost:8000/api/
echo    Admin Panel: http://localhost:8000/admin/
echo.
echo 📝 To start a host agent:
echo    cd agent ^&^& python agent_app.py
echo.

REM Start Django development server
python manage.py runserver 0.0.0.0:8000
