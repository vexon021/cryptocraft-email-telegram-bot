# Deploy Email-to-Telegram Bot on Render

## Step 1: Create GitHub Repository

Since you need to push your code to GitHub first, here are the manual steps:

1. Go to https://github.com and log into your account
2. Click "New repository" (green button)
3. Name it: `email-to-telegram-bot`
4. Make it **Public** (required for free Render plan)
5. Don't initialize with README (you already have your code)
6. Click "Create repository"

## Step 2: Push Your Code to GitHub

After creating the repository, GitHub will show you commands. Run these in your terminal:

```bash
git remote add origin https://github.com/YOUR_USERNAME/email-to-telegram-bot.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 3: Deploy on Render

1. Go to https://render.com and sign up/login
2. Connect your GitHub account
3. Click "New +" → "Blueprint"
4. Select your `email-to-telegram-bot` repository
5. Render will automatically detect the `render.yaml` file
6. Before deploying, set your environment variables:
   - ZOHO_USER: your_email@zohomail.eu
   - ZOHO_PASS: your_zoho_app_password
   - TG_TOKEN: your_telegram_bot_token
   - TG_CHAT_ID: your_telegram_chat_id

## Step 4: Environment Variables Setup

In Render dashboard:
- Go to your service
- Click "Environment" tab
- Add these variables:
  - `ZOHO_USER`: Your Zoho email address
  - `ZOHO_PASS`: Your Zoho app password (NOT regular password)
  - `TG_TOKEN`: Get from @BotFather on Telegram
  - `TG_CHAT_ID`: Get by sending message to bot, then visit https://api.telegram.org/bot{TOKEN}/getUpdates

## Step 5: Deploy and Monitor

- Click "Create Blueprint" or "Deploy"
- Monitor the build logs
- Once deployed, check the logs to ensure the bot is running
- Test by sending an email to your Zoho account

Your bot will run 24/7 on Render's free tier!
