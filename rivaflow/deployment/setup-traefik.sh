#!/bin/bash
set -e

echo "Setting up Traefik for RivaFlow..."

# Create traefik config directory
mkdir -p /root/traefik-config

# Copy RivaFlow routing config
cp /var/www/rivaflow/rivaflow/deployment/traefik-config/rivaflow.yml /root/traefik-config/

# Backup existing docker-compose
cp /root/docker-compose.yml /root/docker-compose.yml.backup

# Copy updated docker-compose
cp /var/www/rivaflow/rivaflow/deployment/docker-compose-traefik.yml /root/docker-compose.yml

# Restart Docker services
cd /root
docker-compose down
docker-compose up -d

echo ""
echo "Traefik configured!"
echo ""
echo "Your app should be available at:"
echo "  http://72.60.41.251"
echo "  http://srv973361.hstgr.cloud"
echo ""
echo "n8n remains at: https://n8n.srv973361.hstgr.cloud"
