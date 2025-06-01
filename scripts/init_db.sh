# Exit on error
set -e

echo "Setting up PostgreSQL database..."

if ! docker compose ps postgres | grep -q "Up"; then
  echo "PostgreSQL container is not running. Please start it with 'docker compose up -d' first."
  exit 1
fi

echo "Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U postgres; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "Creating database if it doesn't exist..."
docker compose exec postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'ibkr_mcp'" | grep -q 1 || docker compose exec postgres psql -U postgres -c "CREATE DATABASE ibkr_mcp"

echo "Initializing database tables..."
python -c "
import asyncio
from src.web.database import init_db

async def main():
  await init_db()

asyncio.run(main())
"

echo "Database setup completed successfully!"
