#!/bin/bash

# =============================================================================
# Seedance V2 Minimal User Data Script
# This script only performs minimal system initialization
# All application deployment is handled by deploy-app.sh
# =============================================================================

set -e

echo "=== Seedance V2 Minimal Setup Started ==="
echo "$(date): Starting minimal system initialization" > /var/log/seedance-init.log

# Basic system update
echo "Updating package list..."
apt-get update >> /var/log/seedance-init.log 2>&1

# Install only essential packages for SSH access and basic functionality  
echo "Installing essential packages..."
apt-get install -y curl wget >> /var/log/seedance-init.log 2>&1

# Set a basic hostname
echo "seedance-v2" > /etc/hostname

# Configure timezone
echo "Setting timezone..."
timedatectl set-timezone Asia/Shanghai 2>/dev/null || echo "Could not set timezone"

# Create a marker file to indicate basic setup is complete
echo "$(date): Basic system initialization completed" >> /var/log/seedance-init.log
touch /tmp/seedance-init-complete

echo "=== Minimal Setup Complete ==="
echo "The system is ready for application deployment via deploy-app.sh"