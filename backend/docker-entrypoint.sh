#!/bin/bash
set -e

echo "======================================"
echo "AgentHub Backend - Docker Entrypoint"
echo "======================================"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h redis ping 2>/dev/null; do
  echo "   Redis is unavailable - sleeping"
  sleep 1
done
echo "✅ Redis is ready!"

# Run migrations
echo ""
echo "🔧 Running Alembic migrations..."
alembic upgrade head
echo "✅ Migrations complete!"

# Check if we should seed data
if [ "$RUN_SEED" = "true" ]; then
  echo ""
  echo "🌱 Seeding eTMS tenant data..."
  python migrations/seed_etms_tenant.py || echo "⚠️  Seed script failed or data already exists"

  echo ""
  echo "📚 Seeding RAG data from PDF..."
  python migrations/seed_etms_rag_data.py || echo "⚠️  RAG seed script failed or data already exists"
fi

echo ""
echo "======================================"
echo "🚀 Starting backend server..."
echo "======================================"
echo ""

# Execute the main command
exec "$@"
