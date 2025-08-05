#!/bin/bash

echo "🚀 Setting up GitHub repository for Render deployment..."
echo ""

# Check if already authenticated
if gh auth status &>/dev/null; then
    echo "✅ Already authenticated with GitHub"
else
    echo "🔐 Authenticating with GitHub..."
    echo "This will open your browser for authentication."
    echo "Choose 'HTTPS' when prompted for Git protocol."
    echo ""
    read -p "Press Enter to continue..."
    
    gh auth login
fi

echo ""
echo "📁 Creating GitHub repository..."

# Create repository
gh repo create cryptocraft-email-telegram-bot --public --description "Email to Telegram bot for CryptoCraft alerts"

echo ""
echo "📤 Pushing code to GitHub..."

# Add remote and push
git remote add origin https://github.com/$(gh api user --jq .login)/cryptocraft-email-telegram-bot.git
git branch -M main
git push -u origin main

echo ""
echo "✅ Success! Your repository is now on GitHub:"
echo "   https://github.com/$(gh api user --jq .login)/cryptocraft-email-telegram-bot"
echo ""
echo "🎯 Next steps:"
echo "1. Go to https://render.com"
echo "2. Sign in with GitHub"
echo "3. Create new Blueprint"
echo "4. Select your cryptocraft-email-telegram-bot repository"
echo "5. Set your environment variables (ZOHO_USER, ZOHO_PASS, TG_TOKEN, TG_CHAT_ID)"
echo "6. Deploy!"
