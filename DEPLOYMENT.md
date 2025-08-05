# CryptoCraft Email-to-Telegram Bot - Deployment Guide

## Step 9: Repository Push & Deployment

This guide covers the complete deployment process for the CryptoCraft Email-to-Telegram Bot on Render.com.

## 📋 Prerequisites

- GitHub account
- Render.com account
- Telegram bot token and chat ID
- Zoho email credentials

## 🚀 Deployment Steps

### 1. Push to GitHub Repository

1. **Create GitHub Repository**
   ```bash
   # Go to github.com and create a new repository
   # Name: cryptocraft-email-telegram-bot
   # Don't initialize with README (we already have one)
   ```

2. **Add Remote and Push**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/cryptocraft-email-telegram-bot.git
   git branch -M main
   git push -u origin main
   ```

### 2. Deploy to Render

1. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `cryptocraft-email-telegram-bot`

2. **Configure Service**
   - **Name**: `cryptocraft-email-bot`
   - **Environment**: `Docker`
   - **Plan**: `Free` (or higher as needed)
   - **Auto-Deploy**: `Yes`

3. **Set Environment Variables**
   ```
   ZOHO_USER=your_email@zohomail.eu
   ZOHO_PASS=your_app_password
   TG_TOKEN=your_telegram_bot_token
   TG_CHAT_ID=your_chat_id
   ```

### 3. Verify Deployment

#### Build Logs Check
Look for these messages in Render build logs:
```
✅ Successfully built Docker image
✅ Container started successfully
✅ Health check passed
```

#### Runtime Logs Check
Look for this startup message:
```
Email to Telegram Bot started...
Checking email: your_email@zohomail.eu
Telegram Bot Token: 1234567890...
Checking for new emails... 2024-01-01 12:00:00
```

#### Health Check Verification
- Service should show as "Live" in Render dashboard
- Health check endpoint should return 200 OK
- No error messages in logs

### 4. Send Test CryptoCraft Alert

1. **Compose Test Email**
   - **To**: Your monitored email address
   - **Subject**: `Breaking: Test CryptoCraft Deployment Alert`
   - **Body** (HTML):
   ```html
   <html>
   <img src="cc-impact-sm-red.png">
   <div>Breaking: Successful deployment test</div>
   <p>This is a test of the CryptoCraft email forwarding system.</p>
   <a href="https://cryptocraft.com">View Story</a>
   </html>
   ```

2. **Expected Telegram Message**
   ```
   🔴 Breaking: Successful deployment test

   This is a test of the CryptoCraft email forwarding system.

   📖 [Read more](https://cryptocraft.com)
   ```

3. **Timing Verification**
   - Email should be detected within 10 seconds
   - Telegram message should arrive within 30 seconds
   - Check logs for processing confirmation

### 5. Start 24-Hour Monitoring

#### Automated Monitoring (Recommended)
```bash
# Run the monitoring script
python3 monitor_deployment.py

# Or for a quick test:
python3 monitor_deployment.py test
```

#### Manual Monitoring Checklist

**Every Hour (0-24h):**
- [ ] Service shows "Live" status in Render
- [ ] No error messages in runtime logs
- [ ] Bot continues checking emails every 10 seconds
- [ ] Memory usage stable (< 512MB)
- [ ] CPU usage reasonable (< 50%)

**Test Points (at 2h, 8h, 16h, 24h):**
- [ ] Send test CryptoCraft alert
- [ ] Verify Telegram forwarding works
- [ ] Check response times < 30 seconds
- [ ] Confirm proper message formatting

#### Key Log Messages to Monitor

**Healthy Operation:**
```
✅ Email to Telegram Bot started...
✅ Checking for new emails... [timestamp]
✅ No new emails found
✅ Waiting 10 seconds for next check...
```

**Successful Email Processing:**
```
✅ Processed email: Breaking: [subject]
✅ Message sent to Telegram successfully
```

**Warning Signs:**
```
⚠️ Error connecting to email: [error]
⚠️ Error sending to Telegram: [error]
⚠️ Unexpected error: [error]
```

### 6. Performance Tuning (If Needed)

#### Adjust Polling Interval
If 10-second checks are too frequent:
```python
# In app/email_bot.py, line 355
time.sleep(30)  # Change to 30 seconds
```

#### Adjust Log Level
For less verbose logging:
```python
# Reduce print statements or add log levels
if VERBOSE:
    print("Checking for new emails...")
```

#### Memory Optimization
If memory usage is high:
```python
# Limit processed email history
if len(self.processed_emails["processed_ids"]) > 50:
    self.processed_emails["processed_ids"] = self.processed_emails["processed_ids"][-25:]
```

## 🔍 Troubleshooting

### Common Issues

1. **"Error connecting to email"**
   - Check ZOHO_USER and ZOHO_PASS are correct
   - Verify Zoho app password (not regular password)
   - Confirm IMAP is enabled in Zoho settings

2. **"Error sending to Telegram"**
   - Verify TG_TOKEN is correct
   - Check TG_CHAT_ID format (should be numbers)
   - Test bot manually: send `/start` to your bot

3. **"No new emails found" (but emails exist)**
   - Check email folder (should be INBOX)
   - Verify email hasn't been processed already
   - Check `last_check.json` file

4. **High memory usage**
   - Review processed email list size
   - Check for memory leaks in email processing
   - Consider restart if memory > 1GB

### Emergency Actions

1. **Service Down**
   ```bash
   # Restart via Render dashboard
   # Or redeploy with:
   git commit --allow-empty -m "Force redeploy"
   git push
   ```

2. **Email Flooding**
   ```bash
   # Temporarily increase sleep interval
   # Clear processed emails list
   # Filter emails by sender if needed
   ```

3. **Telegram Rate Limiting**
   ```bash
   # Add delay between messages
   # Implement message queuing
   # Check Telegram API limits
   ```

## ✅ Success Criteria

After 24 hours, you should have:

- [ ] **Stable deployment** - Service running continuously
- [ ] **Successful email processing** - Test alerts forwarded correctly
- [ ] **Healthy logs** - No persistent errors
- [ ] **Reasonable resource usage** - Memory < 512MB, CPU < 50%
- [ ] **Responsive Telegram bot** - Messages delivered within 30 seconds
- [ ] **Proper error handling** - Recovers from temporary failures

## 📊 Monitoring Dashboard

Optional: Set up additional monitoring:

1. **Render Dashboard** - Service metrics and logs
2. **Telegram Bot** - Message delivery confirmation
3. **Email Provider** - IMAP connection status
4. **Custom Monitoring** - Use provided monitoring script

## 🎯 Next Steps

Once 24-hour monitoring is complete:

1. **Production Readiness** - Bot is ready for live CryptoCraft alerts
2. **Scaling** - Consider upgraded Render plan if needed
3. **Backup** - Implement email backup/archiving if required
4. **Additional Features** - Email filtering, multi-chat support, etc.

---

**Deployment completed successfully!** 🎉

The CryptoCraft Email-to-Telegram Bot is now running in production and ready to forward breaking news alerts from CryptoCraft directly to your Telegram chat.
