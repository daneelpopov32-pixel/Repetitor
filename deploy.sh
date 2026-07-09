#!/bin/bash
# ═══════════════════════════════════════════════════
# Deploy Репетитор (kimstudy.ru) on Ubuntu 24.04
# Run as root: bash deploy.sh
# ═══════════════════════════════════════════════════
set -e

DOMAIN="kimstudy.ru"
APP_DIR="/opt/repetitor"

echo "═══════════════════════════════════════"
echo "  Deploying Репетитор to ${DOMAIN}"
echo "═══════════════════════════════════════"

# 1. Update system
echo "[1/8] Updating system..."
apt update -qq && apt upgrade -y -qq

# 2. Install Docker
echo "[2/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable docker && systemctl start docker

# 3. Install Docker Compose plugin
echo "[3/8] Installing Docker Compose..."
if ! docker compose version &> /dev/null; then
  apt install -y docker-compose-plugin
fi

# 4. Install Nginx
echo "[4/8] Installing Nginx..."
apt install -y nginx
systemctl enable nginx

# 5. Install Certbot (Let's Encrypt)
echo "[5/8] Installing Certbot..."
apt install -y certbot python3-certbot-nginx

# 6. Clone project
echo "[6/8] Cloning project..."
if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR" && git pull
else
  git clone https://github.com/daneelpopov32-pixel/Repetitor.git "$APP_DIR"
  cd "$APP_DIR"
fi

# 7. Create .env for production
echo "[7/8] Creating production .env..."
cat > backend/.env << 'ENVEOF'
DATABASE_URL=postgresql+asyncpg://repetitor:repetitor@db:5432/repetitor
DATABASE_URL_SYNC=postgresql+psycopg2://repetitor:repetitor@db:5432/repetitor
REDIS_URL=redis://redis:6379/0
SECRET_KEY=$(openssl rand -hex 32)
GIGACHAT_API_KEY=
GIGACHAT_API_URL=https://api.sbercloud.ru/v1/chat/completions
S3_ENDPOINT=
S3_BUCKET=repetitor-media
S3_ACCESS_KEY=
S3_SECRET_KEY=
CORS_ORIGINS=["https://kimstudy.ru","http://kimstudy.ru"]
ENVEOF

# Generate proper SECRET_KEY
sed -i "s|\$(openssl rand -hex 32)|$(openssl rand -hex 32)|" backend/.env

# 8. Configure Nginx
echo "[8/8] Configuring Nginx..."
cat > /etc/nginx/sites-available/repetitor << 'NGINXEOF'
server {
    listen 80;
    server_name kimstudy.ru www.kimstudy.ru;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Media files
    location /media/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/repetitor /etc/nginx/sites-enabled/repetitor
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 9. Update docker-compose for production
echo "Configuring Docker Compose..."
cat > docker-compose.prod.yml << 'DCEOF'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: repetitor
      POSTGRES_PASSWORD: repetitor
      POSTGRES_DB: repetitor
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U repetitor"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  backend:
    build: ./backend
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - media_data:/app/media
    restart: unless-stopped

  celery-worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2
    env_file: ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - media_data:/app/media
    restart: unless-stopped

  frontend:
    build: ./frontend
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
  media_data:
DCEOF

# 10. Start services
echo "Starting Docker services..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "═══════════════════════════════════════"
echo "  Services started!"
echo "═══════════════════════════════════════"
echo ""
echo "Now run SSL setup:"
echo "  certbot --nginx -d kimstudy.ru -d www.kimstudy.ru --non-interactive --agree-tos --email admin@kimstudy.ru"
echo ""
echo "Check status:"
echo "  docker compose -f docker-compose.prod.yml ps"
echo "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
