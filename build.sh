#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Install dependencies..."
pip install -r requirements.txt

echo "Collect static files..."
python manage.py collectstatic --no-input --clear

echo "Run database migrations..."
python manage.py migrate

echo "Build successful!"
