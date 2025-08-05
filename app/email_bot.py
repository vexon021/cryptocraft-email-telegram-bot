import imaplib
import email
import time
import requests
from datetime import datetime
import json
import os
import html
from pathlib import Path

class EmailToTelegramBot:
    def __init__(self, email_user, email_password, telegram_token, chat_id):
        self.email_user = email_user
        self.email_password = email_password
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.last_check_file = "last_check.json"
        self.processed_emails = self.load_processed_emails()

        self.imap_server = "imap.zoho.eu"  
        self.imap_port = 993
        
    def load_processed_emails(self):
        """Load list of already processed email IDs"""
        if os.path.exists(self.last_check_file):
            with open(self.last_check_file, 'r') as f:
                return json.load(f)
        return {"processed_ids": []}
    
    def save_processed_emails(self):
        """Save list of processed email IDs"""
        with open(self.last_check_file, 'w') as f:
            json.dump(self.processed_emails, f)
    
    def connect_to_email(self):
        """Connect to email server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_user, self.email_password)
            mail.select('inbox')
            return mail
        except Exception as e:
            print(f"Error connecting to email: {e}")
            return None
    
    def send_to_telegram(self, message):
        """Send message to Telegram"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # Split long messages if needed (Telegram has 4096 character limit)
        if len(message) > 4000:
            message = message[:4000] + "... (truncated)"
        
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",  # Changed to Markdown for better link handling
            "disable_web_page_preview": False
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("Message sent to Telegram successfully")
                return True
            else:
                print(f"Error sending to Telegram: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
            return False
    
    def clean_email_address(self, email_addr):
        """Clean email address to remove problematic characters for HTML parsing"""
        if not email_addr:
            return "Unknown"
        
        # Remove angle brackets and escape HTML entities
        cleaned = email_addr.replace('<', '').replace('>', '')
        return html.escape(cleaned)
    
    def format_email_for_telegram(self, subject, sender, body):
        """Format email content for Telegram"""
        # For CryptoCraft emails, check if parsing worked
        if "Breaking:" in body and any(emoji in body for emoji in ['🔴', '🟠', '🟡', '🚨']):
            # The body is already formatted correctly with impact emoji
            return body
        elif "cryptocraft" in sender.lower() or "Breaking:" in subject:
            # This is a CryptoCraft email but parsing may have failed
            # Try to create a simple format with default emoji
            return f"🚨 Breaking: {subject.replace('Breaking:', '').strip()}\n\n📖 [Read more](https://cryptocraft.com)"
        
        # For other emails, use simple format
        return f"📧 **New Email**\n\n**From:** {sender}\n**Subject:** {subject}\n\n{body[:300]}..."
    
    def extract_email_content(self, email_message):
        """Extract readable content from email"""
        import re
        from urllib.parse import urljoin
        
        html_body = ""
        text_body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/html":
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/plain":
                    text_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            content_type = email_message.get_content_type()
            payload = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            if content_type == "text/html":
                html_body = payload
            else:
                text_body = payload
        
        # Try to parse HTML first for better extraction
        if html_body:
            return self.parse_crypto_craft_email(html_body)
        else:
            return self.parse_crypto_craft_text(text_body)
    
    def get_impact_emoji(self, html_content):
        """Extract impact level from email and return appropriate emoji"""
        import re
        
        # Look for the impact image
        impact_pattern = r'cc-impact-sm-(yel|red|ora)\.png'
        impact_match = re.search(impact_pattern, html_content, re.IGNORECASE)
        
        if impact_match:
            impact_color = impact_match.group(1).lower()
            if impact_color == 'red':
                return '🔴'  # High impact - red circle
            elif impact_color == 'ora':
                return '🟠'  # Medium impact - orange circle
            elif impact_color == 'yel':
                return '🟡'  # Low impact - yellow circle
        
        # Fallback to default alert emoji
        return '🚨'
    def parse_crypto_craft_email(self, html_content):
        """Parse CryptoCraft email to extract alert content and view story link"""
        import re
        
        # Get the appropriate impact emoji
        impact_emoji = self.get_impact_emoji(html_content)
        
        # First, remove all CSS styles and scripts
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract the alert title (Breaking: ...)
        title_patterns = [
            r'Breaking:\s*([^<\n\r]+)',
            r'🚨\s*Breaking:\s*([^<\n\r]+)',
            r'Alert[^:]*:\s*([^<\n\r]+)',
        ]
        
        title = ""
        for pattern in title_patterns:
            title_match = re.search(pattern, html_content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                break
        
        # Extract main content - look for text between common HTML patterns
        content_patterns = [
            # Look for content in table cells or divs after "Breaking:"
            r'Breaking:[^<]*?</[^>]*>[\s\S]*?<[^>]*[^>]*>(.*?)(?=<[^>]*>[\s\S]*?(?:View Story|Unsubscribe|Contact|You\'ve opted))',
            # Look for paragraph content
            r'<p[^>]*>(.*?)(?=</p>[\s\S]*?(?:View Story|Unsubscribe))',
            # Look for content in td elements
            r'<td[^>]*>(.*?)(?=</td>[\s\S]*?(?:View Story|Unsubscribe))',
            # More general pattern
            r'Breaking:[^<]*?(?:</[^>]*>)?\s*(.*?)(?=(?:View Story|Unsubscribe|Contact|You\'ve opted))',
        ]
        
        content = ""
        for pattern in content_patterns:
            content_match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if content_match:
                content = content_match.group(1)
                # Clean HTML tags
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'&[a-zA-Z0-9#]+;', '', content)  # Remove HTML entities
                content = re.sub(r'\s+', ' ', content).strip()
                
                # If content is too long or seems to contain CSS/HTML, try next pattern
                if len(content) > 50 and len(content) < 1000 and not any(x in content.lower() for x in ['font-family', 'margin', 'padding', 'css', 'style']):
                    break
                content = ""
        
        # Extract View Story link
        view_story_link = ""
        link_patterns = [
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>[\s\S]*?View Story',
            r'href=["\']([^"\']*)["\'][^>]*>[\s\S]*?View Story',
            r'View Story[^h]*href=["\']([^"\']*)["\']',
        ]
        
        for pattern in link_patterns:
            link_match = re.search(pattern, html_content, re.IGNORECASE)
            if link_match:
                view_story_link = link_match.group(1)
                break
        
        # Format the result with impact emoji
        if title and content:
            result = f"{impact_emoji} Breaking: {title}\n\n{content}"
            if view_story_link:
                result += f"\n\n📖 [Read more]({view_story_link})"
            return result
        elif title:
            result = f"{impact_emoji} Breaking: {title}"
            if view_story_link:
                result += f"\n\n📖 [Read more]({view_story_link})"
            return result
        
        # Fallback: extract all text and clean it
        clean_content = re.sub(r'<[^>]+>', '', html_content)
        clean_content = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        # Try to find the actual alert content in the cleaned text
        lines = clean_content.split('\n')
        alert_lines = []
        found_breaking = False
        
        for line in lines:
            line = line.strip()
            if 'Breaking:' in line:
                found_breaking = True
                alert_lines.append(f"{impact_emoji} {line}")
            elif found_breaking and line and len(line) > 10 and not any(x in line.lower() for x in ['unsubscribe', 'contact', 'opted', 'font-family', 'margin', 'css']):
                alert_lines.append(line)
            elif found_breaking and ('View Story' in line or 'Read more' in line):
                break
        
        if alert_lines:
            result = '\n'.join(alert_lines[:3])  # Limit to first 3 relevant lines
            if view_story_link:
                result += f"\n\n📖 [Read more]({view_story_link})"
            return result
        
        return f"{impact_emoji} New CryptoCraft Alert (Content parsing failed)"
    
    def parse_crypto_craft_text(self, text_content):
        """Parse plain text version of CryptoCraft email"""
        import re
        
        # For text version, we can't detect impact, so use default
        impact_emoji = '🚨'
        
        lines = text_content.split('\n')
        alert_content = []
        found_breaking = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip CSS/HTML related lines
            if any(x in line.lower() for x in ['font-family', 'margin', 'padding', 'css', 'style', 'mso-', 'webkit']):
                continue
                
            if 'Breaking:' in line:
                found_breaking = True
                alert_content.append(f"{impact_emoji} {line}")
            elif found_breaking and line and len(line) > 10:
                # Stop at footer content
                if any(x in line.lower() for x in ['unsubscribe', 'contact', 'opted', 'view story']):
                    break
                alert_content.append(line)
        
        # Look for URL in the text for "Read more"
        url_match = re.search(r'https?://[^\s]+', text_content)
        read_more_link = ""
        if url_match:
            read_more_link = f"\n\n📖 [Read more]({url_match.group(0)})"
        
        if alert_content:
            result = '\n'.join(alert_content[:5])  # Limit to first 5 relevant lines
            result += read_more_link
            return result
        
        return text_content[:500] + "..." if len(text_content) > 500 else text_content
    
    def check_new_emails(self):
        """Check for new emails and send to Telegram"""
        mail = self.connect_to_email()
        if not mail:
            return
        
        try:
            # Search for all emails
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()
            
            new_emails_found = False
            
            for email_id in email_ids:
                email_id_str = email_id.decode()
                
                # Skip if already processed
                if email_id_str in self.processed_emails["processed_ids"]:
                    continue
                
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                email_message = email.message_from_bytes(msg_data[0][1])
                
                # Extract email details
                subject = email_message.get('Subject', 'No Subject')
                sender = email_message.get('From', 'Unknown Sender')
                body = self.extract_email_content(email_message)
                
                # Format and send to Telegram
                telegram_message = self.format_email_for_telegram(subject, sender, body)
                
                if self.send_to_telegram(telegram_message):
                    # Mark as processed
                    self.processed_emails["processed_ids"].append(email_id_str)
                    new_emails_found = True
                    print(f"Processed email: {subject}")
                
                # Limit to avoid spam (only process last 5 new emails at once)
                if len(self.processed_emails["processed_ids"]) > 100:
                    self.processed_emails["processed_ids"] = self.processed_emails["processed_ids"][-50:]
            
            if new_emails_found:
                self.save_processed_emails()
            else:
                print("No new emails found")
                
        except Exception as e:
            print(f"Error checking emails: {e}")
        finally:
            mail.close()
            mail.logout()
    
    def run(self):
        """Main loop to check emails every 10 seconds"""
        print("Email to Telegram Bot started...")
        print(f"Checking email: {self.email_user}")
        print(f"Telegram Bot Token: {self.telegram_token[:10]}...")
        
        while True:
            try:
                print(f"Checking for new emails... {datetime.now()}")
                self.check_new_emails()
                print("Waiting 10 seconds for next check...")
                time.sleep(10)  # 10 seconds
            except KeyboardInterrupt:
                print("Bot stopped by user")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def main():
    # Load environment variables from .env file if it exists (for local development)
    if Path(".env").exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("Loaded environment variables from .env file")
        except ImportError:
            print("Note: python-dotenv not installed, skipping .env file loading")
            print("Install with: pip install python-dotenv")
    
    # Configuration from environment variables
    EMAIL_USER = os.getenv("ZOHO_USER")
    EMAIL_PASSWORD = os.getenv("ZOHO_PASS")
    TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
    CHAT_ID = os.getenv("TG_CHAT_ID")
    
    # Validate all required environment variables are set
    required_vars = {
        "ZOHO_USER": EMAIL_USER,
        "ZOHO_PASS": EMAIL_PASSWORD,
        "TG_TOKEN": TELEGRAM_TOKEN,
        "TG_CHAT_ID": CHAT_ID
    }
    
    missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]
    
    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables before running the bot.")
        print("\nOption 1 - Export environment variables:")
        print("  export ZOHO_USER='your_email@zohomail.eu'")
        print("  export ZOHO_PASS='your_password'")
        print("  export TG_TOKEN='your_telegram_bot_token'")
        print("  export TG_CHAT_ID='your_chat_id'")
        print("\nOption 2 - Create a .env file with the following content:")
        print("  ZOHO_USER=your_email@zohomail.eu")
        print("  ZOHO_PASS=your_password")
        print("  TG_TOKEN=your_telegram_bot_token")
        print("  TG_CHAT_ID=your_chat_id")
        print("  (Note: Install python-dotenv with: pip install python-dotenv)")
        return
    
    if CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("Please set your CHAT_ID first!")
        print("1. Send a message to your bot")
        print(f"2. Visit: https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates")
        print("3. Find your chat ID in the response")
        return
    
    # Create and run bot
    bot = EmailToTelegramBot(EMAIL_USER, EMAIL_PASSWORD, TELEGRAM_TOKEN, CHAT_ID)
    bot.run()

if __name__ == "__main__":
    main()