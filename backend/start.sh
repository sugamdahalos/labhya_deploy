#!/bin/bash
# Labhya Compute - Development Startup Script

echo "🚀 Starting Labhya Compute Platform..."

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check for virtual environment
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install/upgrade dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if none exists
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@labhya.com', 'admin123')
    print('Created superuser: admin/admin123')
else:
    print('Superuser already exists')
"

# Clean up any dead tunnels
echo "🔧 Cleaning up any dead tunnels..."
python manage.py manage_tunnels --action=cleanup

echo "✅ Setup complete!"
echo ""
echo "🌐 Starting Django development server..."
echo "   Backend API: http://localhost:8000/api/"
echo "   Admin Panel: http://localhost:8000/admin/"
echo ""
echo "📝 To start a host agent:"
echo "   cd agent && python agent_app.py"
echo ""

# Start Django development server
python manage.py runserver 0.0.0.0:8000
