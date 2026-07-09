#!/bin/bash
# Restore database and images from seed dump
# Run this on the server after docker-compose up

set -e

SEED_DIR="$(cd "$(dirname "$0")" && pwd)"
DUMP_FILE="$SEED_DIR/dump.sql"
IMAGES_DIR="$SEED_DIR/media/images"

echo "=== Restoring Repetitor database ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until docker exec repetitor-db-1 pg_isready -U repetitor > /dev/null 2>&1; do
    sleep 2
done
echo "PostgreSQL is ready."

# Drop and recreate database
echo "Dropping existing database..."
docker exec repetitor-db-1 psql -U repetitor -d postgres -c "DROP DATABASE IF EXISTS repetitor;"
docker exec repetitor-db-1 psql -U repetitor -d postgres -c "CREATE DATABASE repetitor OWNER repetitor;"

# Restore from dump
echo "Restoring database from dump..."
docker exec -i repetitor-db-1 pg_restore -U repetitor -d repetitor --no-owner --no-privileges < "$DUMP_FILE"

echo "Database restored successfully."

# Copy images to backend container
echo "Copying images to backend container..."
docker exec repetitor-backend-1 mkdir -p /app/media/images

# Copy images via tar
tar czf - -C "$SEED_DIR/media" images/ | docker exec -i repetitor-backend-1 tar xzf - -C /app/media/

echo "Images copied successfully."

# Verify
TASK_COUNT=$(docker exec repetitor-db-1 psql -U repetitor -d repetitor -t -c "SELECT count(*) FROM tasks;")
IMAGE_COUNT=$(docker exec repetitor-backend-1 ls /app/media/images/ | wc -l)

echo ""
echo "=== Restore complete ==="
echo "Tasks in database: $TASK_COUNT"
echo "Images on disk: $IMAGE_COUNT"
echo ""
echo "All 4 image scenarios preserved:"
echo "  1. Tasks without images: stored in text_content with empty/null images"
echo "  2. Tasks with context image only: images[0] = inherited from standalone block"
echo "  3. Tasks with own image only: images[0] = ShowPictureQ from task block"
echo "  4. Tasks with both: images[0] = context, images[1] = own"
