#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Install Playwright and its dependencies
playwright install chromium
playwright install-deps chromium

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
