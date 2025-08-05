import imaplib
import email
import time
import requests
from datetime import datetime, timedelta
import json
import os
import html
import logging
import sys
from pathlib import Path
import traceback
import gc
import signal

class EmailToTelegramBot:
    def __init__(self, email_user, email_password, telegram_token, chat_id):
        self.email_user = email_user
        self.email_password = email_password
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        
        # Use data directory for file storage
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        self.last_check_file = data_dir / "last_check.json"
        self.processed_emails = self.load_processed_emails()

        self.imap_server = "imap.zoho.eu"  
        self.imap_port = 993
        
        # Production stability settings
        self.max_retries = 5
        self.retry_delay = 30  # seconds
        self.connection_timeout = 120  # seconds
        self.telegram_rate_limit_delay = 1  # seconds between messages
        self.last_telegram_send = 0
        self.check_interval = 15  # seconds between email checks
        
        # Setup logging
        self.setup_logging()
        
        # Health tracking
        self.start_time = datetime.now()
        self.total_emails_processed = 0
        self.last_successful_check = datetime.now()
        self.consecutive_failures = 0
        self.max_consecutive_failures = 10
        self.running = True
        
        # Setup graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("data/logs")
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "bot.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Setup log rotation to prevent disk space issues
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_dir / "bot.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
        
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logging.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
        
    def load_processed_emails(self):
        """Load list of already processed email IDs"""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    # Ensure we have the right structure
                    if "processed_ids" not in data:
                        return {"processed_ids": [], "last_check": datetime.now().isoformat()}
                    return data
        except Exception as e:
            logging.error(f"Error loading processed emails: {e}")
        
        return {"processed_ids": [], "last_check": datetime.now().isoformat()}
    
    def save_processed_emails(self):
        """Save list of processed email IDs"""
        try:
            self.processed_emails["last_check"] = datetime.now().isoformat()
            with open(self.last_check_file, 'w') as f:
                json.dump(self.processed_emails, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving processed emails: {e}")
    
    def connect_to_email(self):
        """Connect to email server with retry logic"""
        retries = 0
        while retries < self.max_retries:
            try:
                logging.info(f"Connecting to email server (attempt {retries + 1})")
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                mail.login(self.email_user, self.email_password)
                mail.select('inbox')
                logging.info("Successfully connected to email server")
                return mail
            except Exception as e:
                retries += 1
                logging.warning(f"Failed to connect to email server: {e}. Attempt {retries} of {self.max_retries}")
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
        
        logging.error("Max retries reached. Could not connect to email server")
        return None
    
    def send_to_telegram(self, message):
        """Send message to Telegram with rate limiting and retry logic"""
        # Handle Telegram rate limiting
        sleep_time = max(0, self.telegram_rate_limit_delay - (time.time() - self.last_telegram_send))
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # Split long messages if needed (Telegram has 4096 character limit)
        if len(message) > 4000:
            message = message[:4000] + "... (truncated)"
        
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(url, data=data, timeout=30)
                self.last_telegram_send = time.time()
                
                if response.status_code == 200:
                    logging.info("Message sent to Telegram successfully")
                    return True
                elif response.status_code == 429:  # Rate limited
                    # Extract retry_after from response if available
                    try:
                        error_data = response.json()
                        retry_after = error_data.get('parameters', {}).get('retry_after', 60)
                        logging.warning(f"Telegram rate limit hit. Waiting {retry_after} seconds")
                        time.sleep(retry_after)
                        retries += 1
                        continue
                    except:
                        logging.warning("Rate limited, waiting 60 seconds")
                        time.sleep(60)
                        retries += 1
                        continue
                else:
                    logging.error(f"Error sending to Telegram: {response.text}")
                    # Try without markdown parsing if it's a parse error
                    if "can't parse entities" in response.text.lower():
                        data["parse_mode"] = None
                        retries += 1
                        continue
                    return False
                    
            except Exception as e:
                retries += 1
                logging.error(f"Exception sending to Telegram: {e}")
                if retries < self.max_retries:
                    time.sleep(10)
        
        logging.error("Failed to send message to Telegram after all retries")
        return False
    
    def clean_email_address(self, email_addr):
        """Clean email address to remove problematic characters"""
        if not email_addr:
            return "Unknown"
        
        # Remove angle brackets and escape HTML entities
        cleaned = email_addr.replace('<', '').replace('>', '')
        return html.escape(cleaned)
    
    def format_email_for_telegram(self, subject, sender, body):
        """Format email content for Telegram"""
        try:
            # For CryptoCraft emails, check if parsing worked
            if "Breaking:" in body and any(emoji in body for emoji in ['🔴', '🟠', '🟡', '🚨']):
                # The body is already formatted correctly with impact emoji
                return body
            elif "cryptocraft" in sender.lower() or "Breaking:" in subject:
                # This is a CryptoCraft email but parsing may have failed
                # Try to create a simple format with default emoji
                clean_subject = subject.replace('Breaking:', '').strip()
                return f"🚨 Breaking: {clean_subject}\n\n📖 [Read more](https://cryptocraft.com)"
            
            # For other emails, use simple format
            clean_sender = self.clean_email_address(sender)
            return f"📧 **New Email**\n\n**From:** {clean_sender}\n**Subject:** {subject}\n\n{body[:300]}..."
        except Exception as e:
            logging.error(f"Error formatting email for Telegram: {e}")
            return f"📧 New email from {sender}: {subject}"
    
    def extract_email_content(self, email_message):
        """Extract readable content from email"""
        try:
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
        except Exception as e:
            logging.error(f"Error extracting email content: {e}")
            return "Content extraction failed"
    
    def get_impact_emoji(self, html_content):
        """Extract impact level from email and return appropriate emoji"""
        import re
        
        try:
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
        except Exception as e:
            logging.error(f"Error extracting impact emoji: {e}")
        
        # Fallback to default alert emoji
        return '🚨'
        
    def parse_crypto_craft_email(self, html_content):
        """Parse CryptoCraft email to extract alert content and view story link"""
        import re
        
        try:
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
            
            # Extract View Story link
            view_story_link = ""
            link_patterns = [
                r'<a[^>]*href=["\'](https?://[^"\']*)["\'][^>]*>[\s\S]*?View Story',
                r'href=["\'](https?://[^"\']*)["\'][^>]*>[\s\S]*?View Story',
                r'View Story[^h]*href=["\'](https?://[^"\']*)["\']',
            ]
            
            for pattern in link_patterns:
                link_match = re.search(pattern, html_content, re.IGNORECASE)
                if link_match:
                    view_story_link = link_match.group(1)
                    break
            
            # Format the result with impact emoji
            if title:
                result = f"{impact_emoji} Breaking: {title}"
                if view_story_link:
                    result += f"\n\n📖 [Read more]({view_story_link})"
                return result
            
            # Fallback: try to extract any breaking news content
            clean_content = re.sub(r'<[^>]+>', '', html_content)
            clean_content = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # Look for Breaking: content
            breaking_match = re.search(r'Breaking:\s*([^\n\r]{10,200})', clean_content, re.IGNORECASE)
            if breaking_match:
                result = f"{impact_emoji} Breaking: {breaking_match.group(1).strip()}"
                if view_story_link:
                    result += f"\n\n📖 [Read more]({view_story_link})"
                return result
            
            return f"{impact_emoji} New CryptoCraft Alert"
            
        except Exception as e:
            logging.error(f"Error parsing CryptoCraft email: {e}")
            return "🚨 New CryptoCraft Alert (parsing failed)"
    
    def parse_crypto_craft_text(self, text_content):
        """Parse plain text version of CryptoCraft email"""
        import re
        
        try:
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
            
        except Exception as e:
            logging.error(f"Error parsing text content: {e}")
            return "Content parsing failed"
    
    def check_new_emails(self):
        """Check for new emails and send to Telegram"""
        mail = self.connect_to_email()
        if not mail:
            self.consecutive_failures += 1
            return False
        
        try:
            # Search for all emails
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                logging.error(f"Email search failed with status: {status}")
                return False
                
            email_ids = messages[0].split()
            new_emails_found = False
            
            # Only process emails we haven't seen before
            for email_id in email_ids:
                email_id_str = email_id.decode()
                
                # Skip if already processed
                if email_id_str in self.processed_emails["processed_ids"]:
                    continue
                
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        logging.error(f"Failed to fetch email {email_id_str}")
                        continue
                        
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
                        self.total_emails_processed += 1
                        logging.info(f"Processed email: {subject[:100]}...")
                    else:
                        logging.error(f"Failed to send email to Telegram: {subject}")
                    
                except Exception as e:
                    logging.error(f"Error processing email {email_id_str}: {e}")
                    continue
            
            # Clean up old processed emails to prevent memory issues
            if len(self.processed_emails["processed_ids"]) > 1000:
                self.processed_emails["processed_ids"] = self.processed_emails["processed_ids"][-500:]
                logging.info("Cleaned up old processed email IDs")
            
            if new_emails_found:
                self.save_processed_emails()
                logging.info(f"Found and processed {len([x for x in email_ids if x.decode() not in self.processed_emails['processed_ids']])} new emails")
            else:
                logging.info("No new emails found")
            
            self.consecutive_failures = 0
            return True
                
        except Exception as e:
            self.consecutive_failures += 1
            logging.error(f"Error checking emails: {traceback.format_exc()}")
            return False
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
    
    def cleanup_cache_and_files(self):
        """Comprehensive cache cleanup to prevent disk space issues"""
        import shutil
        import os
        
        try:
            data_dir = Path("data")
            logs_dir = data_dir / "logs"
            
            # 1. Clean up processed email IDs (more aggressive)
            if len(self.processed_emails.get("processed_ids", [])) > 500:
                old_count = len(self.processed_emails["processed_ids"])
                # Keep only last 200 emails to be more conservative
                self.processed_emails["processed_ids"] = self.processed_emails["processed_ids"][-200:]
                self.save_processed_emails()
                logging.info(f"Cleaned processed emails: {old_count} -> {len(self.processed_emails['processed_ids'])}")
            
            # 2. Clean up old log files beyond rotation
            if logs_dir.exists():
                log_files = list(logs_dir.glob("bot.log*"))
                if len(log_files) > 7:  # Keep only 7 files (1 current + 6 backups)
                    # Sort by modification time, keep newest 7
                    log_files.sort(key=lambda x: x.stat().st_mtime)
                    for old_log in log_files[:-7]:
                        try:
                            old_log.unlink()
                            logging.info(f"Removed old log file: {old_log}")
                        except:
                            pass
            
            # 3. Check disk space and warn if low
            try:
                disk_usage = shutil.disk_usage(data_dir)
                free_space_mb = disk_usage.free / (1024 * 1024)
                total_space_mb = disk_usage.total / (1024 * 1024)
                used_percent = (disk_usage.used / disk_usage.total) * 100
                
                logging.info(f"Disk space: {free_space_mb:.1f}MB free ({used_percent:.1f}% used)")
                
                # Send warning if disk is getting full
                if used_percent > 90:
                    warning_msg = f"⚠️ Disk Space Warning\n\nDisk usage: {used_percent:.1f}%\nFree space: {free_space_mb:.1f}MB\n\nConsider cleaning up files."
                    self.send_to_telegram(warning_msg)
                elif used_percent > 95:
                    critical_msg = f"🚨 CRITICAL: Disk Almost Full\n\nDisk usage: {used_percent:.1f}%\nFree space: {free_space_mb:.1f}MB\n\nImmediate cleanup required!"
                    self.send_to_telegram(critical_msg)
                    
            except Exception as e:
                logging.warning(f"Could not check disk space: {e}")
            
            # 4. Force garbage collection
            gc.collect()
            
        except Exception as e:
            logging.error(f"Error during cache cleanup: {e}")
    
    def log_health_status(self):
        """Log current health status with enhanced monitoring"""
        uptime = datetime.now() - self.start_time
        time_since_last_check = datetime.now() - self.last_successful_check
        
        # Get memory usage info
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        logging.info(f"=== HEALTH STATUS ===")
        logging.info(f"Uptime: {uptime}")
        logging.info(f"Total emails processed: {self.total_emails_processed}")
        logging.info(f"Consecutive failures: {self.consecutive_failures}")
        logging.info(f"Time since last successful check: {time_since_last_check}")
        logging.info(f"Processed email IDs count: {len(self.processed_emails.get('processed_ids', []))}")
        logging.info(f"Memory usage: {memory_mb:.1f}MB")
        logging.info(f"CPU usage: {cpu_percent:.1f}%")
        logging.info(f"===================")
        
        # Health reports are kept in console logs only (no Telegram notifications)
        # Periodic health reports to Telegram are disabled to reduce chat noise
        if not hasattr(self, 'last_health_report'):
            self.last_health_report = datetime.now()
    
    def send_health_report_to_telegram(self, uptime, memory_mb, cpu_percent):
        """Send periodic health report to Telegram"""
        try:
            health_msg = f"🤖 Bot Health Report\n\n"
            health_msg += f"⏰ Uptime: {uptime}\n"
            health_msg += f"📧 Emails processed: {self.total_emails_processed}\n"
            health_msg += f"💾 Memory: {memory_mb:.1f}MB\n"
            health_msg += f"⚡ CPU: {cpu_percent:.1f}%\n"
            health_msg += f"📊 Tracked emails: {len(self.processed_emails.get('processed_ids', []))}\n"
            health_msg += f"❌ Consecutive failures: {self.consecutive_failures}\n\n"
            health_msg += f"✅ Status: {'Healthy' if self.consecutive_failures < 3 else 'Warning'}"
            
            self.send_to_telegram(health_msg)
            self.last_health_report = datetime.now()
        except Exception as e:
            logging.error(f"Error sending health report: {e}")
    
    def run(self):
        """Main loop to check emails continuously"""
        logging.info("=== EMAIL TO TELEGRAM BOT STARTED ===")
        logging.info(f"Email: {self.email_user}")
        logging.info(f"Telegram Bot Token: {self.telegram_token[:10]}...")
        logging.info(f"Chat ID: {self.chat_id}")
        logging.info(f"Check interval: {self.check_interval} seconds")
        logging.info("====================================")
        
        # Send startup notification to Telegram
        startup_msg = f"🤖 Email Bot Started\n\n📧 Monitoring: {self.email_user}\n⏱️ Check interval: {self.check_interval}s\n🕐 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        self.send_to_telegram(startup_msg)
        
        health_check_counter = 0
        cleanup_counter = 0
        
        while self.running:
            try:
                logging.info(f"Checking for new emails... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                if self.check_new_emails():
                    self.last_successful_check = datetime.now()
                    
                # Log health status every 10 checks (roughly every 2.5 minutes)
                health_check_counter += 1
                if health_check_counter >= 10:
                    self.log_health_status()
                    health_check_counter = 0
                
                # Run comprehensive cleanup every 240 checks (roughly every hour)
                cleanup_counter += 1
                if cleanup_counter >= 240:
                    logging.info("Running periodic cache cleanup...")
                    self.cleanup_cache_and_files()
                    cleanup_counter = 0
                
                # Check if we've had too many consecutive failures
                if self.consecutive_failures >= self.max_consecutive_failures:
                    error_msg = f"🚨 Bot Error\n\nMax consecutive failures reached: {self.consecutive_failures}\nBot needs restart."
                    self.send_to_telegram(error_msg)
                    logging.error("Max consecutive failures reached. Exiting...")
                    break
                
                # Force garbage collection to prevent memory leaks
                gc.collect()
                
                logging.info(f"Waiting {self.check_interval} seconds for next check...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logging.info("Bot stopped by user (Ctrl+C)")
                break
            except Exception as e:
                self.consecutive_failures += 1
                logging.error(f"Unexpected error in main loop: {traceback.format_exc()}")
                
                # Send error notification if it's a recurring issue
                if self.consecutive_failures % 5 == 0:
                    error_msg = f"🚨 Bot Warning\n\nConsecutive failures: {self.consecutive_failures}\nLast error: {str(e)[:200]}"
                    self.send_to_telegram(error_msg)
                
                time.sleep(60)  # Wait 1 minute before retry
        
        # Send shutdown notification
        uptime = datetime.now() - self.start_time
        shutdown_msg = f"🤖 Email Bot Stopped\n\n⏱️ Uptime: {uptime}\n📧 Emails processed: {self.total_emails_processed}\n🕐 Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self.send_to_telegram(shutdown_msg)
        logging.info("Bot shutdown complete")

def main():
    """Main function with comprehensive error handling"""
    try:
        # Load environment variables from .env file if it exists (for local development)
        if Path(".env").exists():
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print("Loaded environment variables from .env file")
            except ImportError:
                print("Note: python-dotenv not installed, skipping .env file loading")
        
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
            return
        
        if CHAT_ID == "YOUR_CHAT_ID_HERE":
            print("Please set your CHAT_ID first!")
            return
        
        # Create and run bot
        bot = EmailToTelegramBot(EMAIL_USER, EMAIL_PASSWORD, TELEGRAM_TOKEN, CHAT_ID)
        bot.run()
        
    except Exception as e:
        print(f"Critical error starting bot: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
