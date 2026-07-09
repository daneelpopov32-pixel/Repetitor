# Seed Data

Database dump and images for offline deployment (server without FIPI access).

## Contents

- `dump.sql` — PostgreSQL custom format dump (schema + data)
- `media/images/` — 414 downloaded FIPI images (15.8 MB)
- `restore.sh` — One-command restore script

## Restore on server

```bash
# 1. Start services
docker-compose up -d

# 2. Run restore
bash backend/seed/restore.sh
```

## Image scenarios preserved

| Scenario | Description | Example in `text_content.images` |
|----------|-------------|----------------------------------|
| No image | Task without any image | `[]` or `null` |
| Context only | Image inherited from standalone FIPI block | `["images/abc.jpg"]` |
| Own only | Image from task's ShowPictureQ | `["images/xyz.jpg"]` |
| Context + own | Both images, context first | `["images/abc.jpg", "images/xyz.jpg"]` |
