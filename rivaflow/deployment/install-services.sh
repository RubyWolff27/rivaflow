#!/bin/bash
set -e

echo "Installing RivaFlow services..."

# Install serve for frontend
npm install -g serve

# Copy systemd service files
cp /var/www/rivaflow/deployment/rivaflow-api.service /etc/systemd/system/
cp /var/www/rivaflow/deployment/rivaflow-web.service /etc/systemd/system/

# Copy nginx config
cp /var/www/rivaflow/deployment/nginx-rivaflow.conf /etc/nginx/sites-available/rivaflow
ln -sf /etc/nginx/sites-available/rivaflow /etc/nginx/sites-enabled/

# Reload systemd and start services
systemctl daemon-reload
systemctl enable rivaflow-api rivaflow-web
systemctl start rivaflow-api rivaflow-web

# Test nginx config and reload
nginx -t
systemctl reload nginx

echo ""
echo "Services installed and started!"
echo ""
echo "Check status:"
echo "  systemctl status rivaflow-api"
echo "  systemctl status rivaflow-web"
echo "  systemctl status nginx"
echo ""
echo "Your app should be available at: http://72.60.41.251"
