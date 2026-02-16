# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its system dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy project
COPY . /app/

# Create directory for static files
RUN mkdir -p /app/staticfiles

# Script to run migrations and start server
COPY ./vps_entrypoint.sh /app/
RUN chmod +x /app/vps_entrypoint.sh

# Expose port
EXPOSE 8080

ENTRYPOINT ["/app/vps_entrypoint.sh"]
