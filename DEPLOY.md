# Hetzner Deployment Guide

## 1) Server packages

Install Docker and the Docker Compose plugin.

Ubuntu example:
```bash
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Open ports:
- 22 (SSH)
- 80 and 443 (HTTP/HTTPS)

Optional UFW:
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

## 2) Folder and user

Create the folder and clone:
```bash
mkdir -p /opt/ppd-api
cd /opt/ppd-api
git clone <YOUR_GITHUB_REPO_URL> .
```

Ensure docker can run (root or add user to docker group):
```bash
usermod -aG docker <user>
```

## 3) Environment file on server

Create `/opt/ppd-api/.env` on the server (do not commit this file):
```
DATABASE_URL=postgresql://app:app_password@db:5432/ppd_db
MIN_GROUP_COUNT=2
LOG_LEVEL=info
CADDY_HOST=api.iooki.com
```

Adjust values as needed for production.

## 4) First run

```bash
cd /opt/ppd-api
docker compose up -d --build
curl -fsS http://localhost/health
```

## 5) GitHub Secrets

Configure these repository secrets for deploy:
- `HETZNER_HOST` (IP or hostname)
- `HETZNER_USER` (SSH user)
- `HETZNER_SSH_KEY` (OpenSSH private key block)
- `HETZNER_PORT` (optional, default 22)
