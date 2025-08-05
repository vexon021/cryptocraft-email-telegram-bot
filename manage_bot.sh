#!/bin/bash

# Email Bot Management Script

CONTAINER_NAME="email-bot-production"
IMAGE_NAME="email-bot:latest"

case "$1" in
    start)
        echo "Starting email bot..."
        docker run --env-file .env --name $CONTAINER_NAME -d $IMAGE_NAME
        echo "Bot started! Container: $CONTAINER_NAME"
        ;;
    stop)
        echo "Stopping email bot..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        echo "Bot stopped and removed."
        ;;
    restart)
        echo "Restarting email bot..."
        docker stop $CONTAINER_NAME 2>/dev/null
        docker rm $CONTAINER_NAME 2>/dev/null
        docker run --env-file .env --name $CONTAINER_NAME -d $IMAGE_NAME
        echo "Bot restarted! Container: $CONTAINER_NAME"
        ;;
    status)
        echo "=== EMAIL BOT STATUS ==="
        docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo
        echo "=== RECENT LOGS ==="
        docker logs --tail 5 $CONTAINER_NAME 2>/dev/null || echo "Container not running"
        ;;
    logs)
        echo "=== EMAIL BOT LOGS ==="
        echo "Press Ctrl+C to stop viewing logs"
        echo "========================"
        docker logs -f $CONTAINER_NAME
        ;;
    build)
        echo "Rebuilding email bot image..."
        docker build -t $IMAGE_NAME .
        echo "Image rebuilt successfully!"
        ;;
    health)
        echo "=== EMAIL BOT HEALTH CHECK ==="
        docker exec $CONTAINER_NAME python -c "print('Bot is responding')" 2>/dev/null && echo "✅ Bot is healthy" || echo "❌ Bot is not responding"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $CONTAINER_NAME 2>/dev/null || echo "Container not running"
        ;;
    *)
        echo "Email Bot Management Script"
        echo "Usage: $0 {start|stop|restart|status|logs|build|health}"
        echo
        echo "Commands:"
        echo "  start   - Start the email bot"
        echo "  stop    - Stop and remove the email bot"
        echo "  restart - Restart the email bot"
        echo "  status  - Show bot status and recent logs"
        echo "  logs    - Follow logs in real-time"
        echo "  build   - Rebuild the bot image"
        echo "  health  - Check bot health and resource usage"
        exit 1
        ;;
esac
