#!/bin/bash

# Setup Test Database Script
# This script creates and migrates the test database for running tests

set -e  # Exit on error

echo "🔧 Setting up test database..."

# Load test environment variables
export $(cat .env.test | grep -v '^#' | xargs)

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
  echo "❌ PostgreSQL is not running on localhost:5432"
  echo "Please start PostgreSQL before running tests"
  exit 1
fi

# Drop and recreate test database
echo "📦 Creating test database..."
psql -h localhost -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'helpdesk_test'" | grep -q 1 && \
  psql -h localhost -U postgres -c "DROP DATABASE helpdesk_test" || true

psql -h localhost -U postgres -c "CREATE DATABASE helpdesk_test"

# Create test user if not exists
psql -h localhost -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = 'test'" | grep -q 1 || \
  psql -h localhost -U postgres -c "CREATE USER test WITH PASSWORD 'test'"

# Grant permissions
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE helpdesk_test TO test"

# Run migrations
echo "🚀 Running Prisma migrations..."
npx prisma migrate deploy

echo "✅ Test database setup complete!"
