#!/bin/bash
# Beta deployment script
# This script deploys the application to the beta environment

set -e  # Exit on error

echo "================================"
echo "Deploying to Beta Environment"
echo "================================"

# Navigate to app directory
cd /app/whatsapp-ai

# Pull latest code
echo "Pulling latest code from main branch..."
git pull origin main

# Build and deploy with Docker Compose
echo "Building and deploying containers..."
docker-compose -f infrastructure/docker-compose.beta.yml pull
docker-compose -f infrastructure/docker-compose.beta.yml up -d --build

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Run database migrations
echo "Running database migrations..."
docker-compose -f infrastructure/docker-compose.beta.yml exec -T web python backend/manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker-compose -f infrastructure/docker-compose.beta.yml exec -T web python backend/manage.py collectstatic --noinput

# Check deployment status
echo "Checking deployment status..."
docker-compose -f infrastructure/docker-compose.beta.yml ps

echo "================================"
echo "Beta deployment completed successfully!"
echo "================================"
