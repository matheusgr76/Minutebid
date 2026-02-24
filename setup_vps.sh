#!/bin/bash

# setup_vps.sh - Automated setup for Minutebid bot on a fresh Linux VPS (Ubuntu/Debian)

echo "--- Starting Minutebid Bot Setup ---"

# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker
if ! command -v docker &> /dev/null
then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
else
    echo "Docker already installed."
fi

# 3. Build the bot image
echo "Building bot image..."
sudo docker build -t minutebid-bot .

# 4. Instructions for user
echo ""
echo "--- SETUP COMPLETE ---"
echo "To run the bot, you need to create your .env file first:"
echo "nano .env"
echo ""
echo "Then start the bot with:"
echo "sudo docker run -d --name minutebid --restart always --env-file .env -v $(pwd)/.dashboard_msg_id:/app/.dashboard_msg_id minutebid-bot"
echo ""
echo "The bot will now run 24/7 and restart if the server reboots!"
