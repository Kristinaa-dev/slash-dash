#!/bin/bash

# Start PostgreSQL and Redis services
sudo systemctl start postgresql
sudo systemctl start redis-server

# Activate your virtual environment
source venv/bin/activate

# Navigate to your app directory
cd app

# Start Celery worker and beat in the background
celery -A app worker -l info &
celery -A app beat -l info &

# Start Uvicorn in the background
uvicorn app.asgi:application --host 0.0.0.0 --port 8001 &

# Start Django development server (this will run in the foreground)
python3 manage.py runserver
