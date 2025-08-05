#!/usr/bin/env python3
"""
Deployment monitoring script for CryptoCraft Email-to-Telegram Bot
Monitors Render deployment health and provides insights for 24h monitoring period
"""

import requests
import time
import json
from datetime import datetime, timedelta
import os
import sys

class DeploymentMonitor:
    def __init__(self):
        self.render_service_id = os.getenv('RENDER_SERVICE_ID', '')
        self.render_api_key = os.getenv('RENDER_API_KEY', '')
        self.telegram_token = os.getenv('TG_TOKEN', '')
        self.chat_id = os.getenv('TG_CHAT_ID', '')
        self.monitor_duration_hours = 24
        self.check_interval_minutes = 5
        
    def send_telegram_message(self, message):
        """Send monitoring message to Telegram"""
        if not self.telegram_token or not self.chat_id:
            print(f"MONITOR: {message}")
            return True
            
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": f"🔍 **DEPLOYMENT MONITOR**\\n\\n{message}",
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send monitoring message: {e}")
            return False
    
    def check_render_service_health(self):
        """Check Render service health via API"""
        if not self.render_service_id or not self.render_api_key:
            return {"status": "unknown", "message": "Render API credentials not configured"}
        
        url = f"https://api.render.com/v1/services/{self.render_service_id}"
        headers = {"Authorization": f"Bearer {self.render_api_key}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                service_data = response.json()
                return {
                    "status": service_data.get("service", {}).get("state", "unknown"),
                    "message": "Service health check successful",
                    "last_deploy": service_data.get("service", {}).get("updatedAt", "unknown")
                }
            else:
                return {"status": "error", "message": f"API error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Health check failed: {e}"}
    
    def check_telegram_bot_connectivity(self):
        """Test Telegram bot connectivity"""
        if not self.telegram_token:
            return {"status": "error", "message": "Telegram token not configured"}
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/getMe"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                bot_info = response.json()
                bot_name = bot_info.get("result", {}).get("username", "unknown")
                return {"status": "healthy", "message": f"Bot @{bot_name} is responsive"}
            else:
                return {"status": "error", "message": f"Bot not responsive: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Bot connectivity failed: {e}"}
    
    def send_test_email_alert(self):
        """Instructions for sending test CryptoCraft alert"""
        test_instructions = """
**TEST EMAIL INSTRUCTIONS:**

To test the CryptoCraft email forwarding:

1. **Send a test email** to your monitored email address with:
   - Subject: "Breaking: Test CryptoCraft Alert"
   - HTML body containing: `<img src='cc-impact-sm-red.png'>`
   - Add some content and a link

2. **Expected behavior:**
   - Bot should detect the email within 10 seconds
   - Should parse the content and extract impact level (🔴)
   - Should forward to Telegram with proper formatting

3. **Check logs** for:
   - "Email to Telegram Bot started..."
   - "Checking for new emails..."
   - "Processed email: Breaking: Test CryptoCraft Alert"
   - "Message sent to Telegram successfully"

4. **If issues occur:**
   - Check environment variables are set correctly
   - Verify email credentials and IMAP access
   - Confirm Telegram bot token and chat ID
        """
        return test_instructions
    
    def generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "render_health": self.check_render_service_health(),
            "telegram_health": self.check_telegram_bot_connectivity(),
            "test_instructions": self.send_test_email_alert()
        }
        
        return report_data
    
    def start_24h_monitoring(self):
        """Start 24-hour monitoring cycle"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=self.monitor_duration_hours)
        
        print(f"🚀 Starting 24-hour deployment monitoring")
        print(f"Start: {start_time}")
        print(f"End: {end_time}")
        print(f"Check interval: {self.check_interval_minutes} minutes")
        
        # Send initial monitoring message
        initial_message = f"""**24-HOUR MONITORING STARTED**
        
🕐 **Start Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}
⏰ **Duration:** {self.monitor_duration_hours} hours
🔄 **Check Interval:** {self.check_interval_minutes} minutes

**Initial Health Check:**
"""
        
        # Perform initial health checks
        report = self.generate_monitoring_report()
        
        render_status = report["render_health"]["status"]
        telegram_status = report["telegram_health"]["status"]
        
        initial_message += f"""
🌐 **Render Service:** {render_status}
🤖 **Telegram Bot:** {telegram_status}

{report["test_instructions"]}
        """
        
        self.send_telegram_message(initial_message)
        
        # Start monitoring loop
        check_count = 0
        while datetime.now() < end_time:
            check_count += 1
            time.sleep(self.check_interval_minutes * 60)
            
            # Generate health report
            report = self.generate_monitoring_report()
            
            # Check for issues
            issues = []
            if report["render_health"]["status"] not in ["healthy", "running", "available"]:
                issues.append(f"⚠️ Render service issue: {report['render_health']['message']}")
            
            if report["telegram_health"]["status"] != "healthy":
                issues.append(f"⚠️ Telegram bot issue: {report['telegram_health']['message']}")
            
            # Send periodic updates (every hour or if issues found)
            if check_count % (60 // self.check_interval_minutes) == 0 or issues:
                elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
                remaining_hours = self.monitor_duration_hours - elapsed_hours
                
                status_message = f"""**MONITORING UPDATE**
                
⏱️ **Elapsed:** {elapsed_hours:.1f}h / **Remaining:** {remaining_hours:.1f}h
📊 **Check #{check_count}**

**Status:**
🌐 Render: {report["render_health"]["status"]}
🤖 Telegram: {report["telegram_health"]["status"]}
"""
                
                if issues:
                    status_message += "\\n**⚠️ ISSUES DETECTED:**\\n" + "\\n".join(issues)
                else:
                    status_message += "\\n✅ **All systems healthy**"
                
                self.send_telegram_message(status_message)
            
            print(f"Health check #{check_count} completed - {datetime.now()}")
        
        # Send completion message
        completion_message = f"""**24-HOUR MONITORING COMPLETED**
        
🏁 **End Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **Total Checks:** {check_count}
⏰ **Duration:** {self.monitor_duration_hours} hours

**Final Status:**
🌐 Render: {report["render_health"]["status"]}
🤖 Telegram: {report["telegram_health"]["status"]}

**Monitoring Summary:**
- Deployment monitored for full 24-hour period
- Health checks performed every {self.check_interval_minutes} minutes
- Ready for production use ✅
        """
        
        self.send_telegram_message(completion_message)
        print("24-hour monitoring completed successfully!")

def main():
    print("CryptoCraft Email-to-Telegram Bot - Deployment Monitor")
    print("=" * 60)
    
    monitor = DeploymentMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Just run a single health check
        print("Running single health check...")
        report = monitor.generate_monitoring_report()
        print(json.dumps(report, indent=2))
    else:
        # Start 24-hour monitoring
        monitor.start_24h_monitoring()

if __name__ == "__main__":
    main()
