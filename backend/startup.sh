#!/bin/bash

# Azure App Service startup script for Boloo Backend
echo "Starting Boloo Backend on Azure App Service..."

# Run database migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start Uvicorn server
echo "Starting Uvicorn server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info
