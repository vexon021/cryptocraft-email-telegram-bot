# GitHub Personal Access Token Setup

## Option 1: Create Personal Access Token Manually

### Step 1: Create a Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `Email Bot Render Deployment`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
5. Click "Generate token"
6. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Use Token for Git Authentication
```bash
# Add remote with token
git remote add origin https://YOUR_TOKEN@github.com/vexon021/cryptocraft-email-telegram-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_TOKEN` with the token you copied.

## Option 2: Use GitHub CLI (Easier)

Just run our setup script:
```bash
./setup_github.sh
```

This will:
1. Authenticate you with GitHub (opens browser)
2. Create the repository automatically
3. Push your code

## Repository will be created at:
https://github.com/vexon021/cryptocraft-email-telegram-bot

## After GitHub Setup is Complete:
1. Go to https://render.com
2. Sign in with GitHub
3. Create new "Blueprint"
4. Select your repository
5. Set environment variables:
   - ZOHO_USER: your_email@zohomail.eu
   - ZOHO_PASS: your_zoho_app_password
   - TG_TOKEN: your_telegram_bot_token
   - TG_CHAT_ID: your_telegram_chat_id
6. Deploy!
