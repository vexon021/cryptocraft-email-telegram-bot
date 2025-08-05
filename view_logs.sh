#!/bin/bash

# Script to view logs from the running email bot container

echo "=== EMAIL BOT LOGS ==="
echo "Container: email-bot-production"
echo "Press Ctrl+C to stop viewing logs"
echo "========================"
echo

# Follow logs in real-time
docker logs -f email-bot-production
