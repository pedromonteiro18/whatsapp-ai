#!/bin/bash
# Docker entrypoint script for WhatsApp AI Chatbot
# This script runs as the 'django' user (non-root)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WhatsApp AI Chatbot - Starting Up${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for database...${NC}"

    # Get database connection details from environment or use defaults
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-whatsapp_chatbot}

    max_retries=30
    retry_count=0

    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U postgres > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))

        if [ $retry_count -ge $max_retries ]; then
            echo -e "${RED}✗ Database connection failed after $max_retries attempts${NC}"
            exit 1
        fi

        echo -e "${YELLOW}  Attempt $retry_count/$max_retries - Database not ready, waiting...${NC}"
        sleep 2
    done

    echo -e "${GREEN}✓ Database is ready!${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}⏳ Running database migrations...${NC}"

    if python manage.py migrate --noinput; then
        echo -e "${GREEN}✓ Migrations completed successfully${NC}"
    else
        echo -e "${RED}✗ Migration failed${NC}"
        exit 1
    fi
}

# Function to collect static files
collect_static() {
    echo -e "${YELLOW}⏳ Collecting static files...${NC}"

    if python manage.py collectstatic --noinput --clear; then
        echo -e "${GREEN}✓ Static files collected${NC}"
    else
        echo -e "${YELLOW}⚠ Static files collection failed (non-critical)${NC}"
    fi
}

# Function to create superuser if specified
create_superuser() {
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
        echo -e "${YELLOW}⏳ Creating superuser...${NC}"

        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

        echo -e "${GREEN}✓ Superuser check completed${NC}"
    fi
}

# Function to validate configuration
validate_config() {
    echo -e "${YELLOW}⏳ Validating configuration...${NC}"

    if python manage.py validate_config --skip-external; then
        echo -e "${GREEN}✓ Configuration is valid${NC}"
    else
        echo -e "${RED}✗ Configuration validation failed${NC}"
        echo -e "${RED}  Please check your environment variables${NC}"
        exit 1
    fi
}

# Function to ensure logs directory exists
setup_logs() {
    echo -e "${YELLOW}⏳ Setting up logs directory...${NC}"

    if [ ! -d "/app/logs" ]; then
        mkdir -p /app/logs
    fi

    echo -e "${GREEN}✓ Logs directory ready${NC}"
}

# Trap SIGTERM and SIGINT for graceful shutdown
cleanup() {
    echo -e "${YELLOW}⏳ Received shutdown signal, cleaning up...${NC}"

    # Kill any child processes
    pkill -P $$ || true

    echo -e "${GREEN}✓ Cleanup completed${NC}"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Main startup sequence
main() {
    # Ensure we're in the app directory
    cd /app

    # Run startup tasks
    wait_for_db
    setup_logs
    validate_config
    run_migrations
    collect_static
    create_superuser

    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}✓ Startup completed successfully!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Starting application server...${NC}"
    echo ""

    # Execute the command passed to the entrypoint
    exec "$@"
}

# Run main function
main "$@"
