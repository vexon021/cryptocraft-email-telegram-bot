# Email to Telegram Bot

This bot monitors a Zoho email account and forwards new emails to a Telegram chat.

## Features

- Monitors Zoho email inbox for new messages
- Forwards emails to Telegram with formatted content
- Special handling for CryptoCraft alerts with impact level indicators
- Tracks processed emails to avoid duplicates
- Production-grade stability and error handling

### Production Features
- **Comprehensive logging** with log rotation (10MB max, 5 backup files)
- **Automatic retry logic** for email and Telegram connections (up to 5 retries)
- **Rate limit handling** for Telegram API
- **Graceful shutdown** handling (SIGTERM/SIGINT)
- **Health monitoring** with consecutive failure tracking
- **Memory management** with garbage collection
- **Connection stability** with automatic reconnection
- **Startup/shutdown notifications** sent to Telegram

## Setup

1. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**

   Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   Or manually export environment variables:

   ```bash
   export ZOHO_USER='your_email@zohomail.eu'
   export ZOHO_PASS='your_email_password'
   export TG_TOKEN='your_telegram_bot_token'
   export TG_CHAT_ID='your_telegram_chat_id'
   ```

## 🏃‍♂️ Running the Bot

### Option 1: Production Docker (Recommended)
```bash
# Build the Docker image
docker build -t email-bot .

# Start the bot (detached mode)
./manage_bot.sh start

# Check status
./manage_bot.sh status

# View logs
./manage_bot.sh logs

# Stop the bot
./manage_bot.sh stop
```

### Option 2: Direct Python Execution (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python app/email_bot.py
```

## 🛠️ Management Commands

The `manage_bot.sh` script provides easy management of the production bot:

```bash
# View all available commands
./manage_bot.sh

# Start the bot
./manage_bot.sh start

# Check bot status and recent logs
./manage_bot.sh status

# Follow logs in real-time
./manage_bot.sh logs

# Check bot health and resource usage
./manage_bot.sh health

# Restart the bot
./manage_bot.sh restart

# Stop the bot
./manage_bot.sh stop

# Rebuild the Docker image
./manage_bot.sh build
```

## Deployment on Render

To deploy this bot on Render:

### 1. Link Your Repository
- Go to [Render Dashboard](https://dashboard.render.com)
- Click "New" → "Web Service"
- Connect your GitHub/GitLab repository
- Select this repository

### 2. Configure the Service
- **Name**: Choose a name for your service
- **Branch**: Select your main branch (usually `main` or `master`)
- **Build Command**: Leave empty (Docker will handle this)
- **Start Command**: Leave empty (uses Dockerfile CMD)

### 3. Set Environment Variables
In the Render dashboard, add these environment variables:
- `ZOHO_USER`: Your Zoho email address
- `ZOHO_PASS`: Your Zoho email password
- `TG_TOKEN`: Your Telegram bot token
- `TG_CHAT_ID`: Your Telegram chat ID

### 4. Deploy
- Click "Create Web Service"
- Render will automatically build and deploy your bot
- Monitor the deployment logs for any issues

### Important Notes for Render:
- **Disk Space**: Ensure your Render plan includes sufficient disk space for the `last_check.json` file that tracks processed emails
- **Persistent Storage**: The bot stores processed email IDs locally. Consider upgrading to a plan with persistent disks if you need long-term email tracking
- **Always-On**: Make sure your service is set to "always on" to prevent the bot from sleeping

## Environment Variables

- `ZOHO_USER`: Your Zoho email address
- `ZOHO_PASS`: Your Zoho email password  
- `TG_TOKEN`: Your Telegram bot token
- `TG_CHAT_ID`: Your Telegram chat ID

### Getting Your Telegram Bot Token:
1. Message @BotFather on Telegram
2. Create a new bot with /newbot
3. Copy the provided token

### Getting Your Telegram Chat ID:
1. Send a message to your bot
2. Visit: https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates
3. Find your chat ID in the response

## Security

- Never commit the `.env` file to version control
- Keep your credentials secure
- The bot only reads emails, it doesn't send or modify them

## How it Works

1. Connects to Zoho IMAP server
2. Checks for new emails every 10 seconds
3. Parses email content (with special handling for CryptoCraft alerts)
4. Sends formatted messages to Telegram
5. Tracks processed emails to avoid duplicates

## Testing

Run the test suite to ensure everything is working correctly:

```bash
pytest tests/
```

The tests include:
- CryptoCraft email parsing functionality
- Impact level detection from HTML content
- Edge cases and malformed content handling

## Additional Notes

- **Telegram has a 4096-character limit on messages.** Long messages will be truncated to prevent errors.
- **Render deployment requires adequate disk space** for storing processed email tracking data.
- The bot includes automatic retry mechanisms for handling network errors and service interruptions.
