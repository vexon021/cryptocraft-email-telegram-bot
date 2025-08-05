#!/usr/bin/env python3
"""
Emergency Cache Cleanup Script for Email Bot

This script can be run manually to clean up bot caches and free disk space.
Use this if the bot is experiencing disk space issues or if caches have grown too large.
"""

import json
import shutil
from pathlib import Path
import os

def cleanup_processed_emails():
    """Clean up processed email IDs file"""
    data_dir = Path("data")
    last_check_file = data_dir / "last_check.json"
    
    if last_check_file.exists():
        try:
            with open(last_check_file, 'r') as f:
                data = json.load(f)
            
            old_count = len(data.get("processed_ids", []))
            if old_count > 100:
                # Keep only last 50 emails
                data["processed_ids"] = data["processed_ids"][-50:]
                
                with open(last_check_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"✅ Cleaned processed emails: {old_count} -> {len(data['processed_ids'])}")
            else:
                print(f"ℹ️  Processed emails already clean: {old_count} entries")
                
        except Exception as e:
            print(f"❌ Error cleaning processed emails: {e}")
    else:
        print("ℹ️  No processed emails file found")

def cleanup_log_files():
    """Clean up old log files"""
    logs_dir = Path("data/logs")
    
    if logs_dir.exists():
        log_files = list(logs_dir.glob("bot.log*"))
        if len(log_files) > 3:
            # Sort by modification time, keep newest 3
            log_files.sort(key=lambda x: x.stat().st_mtime)
            removed_count = 0
            
            for old_log in log_files[:-3]:
                try:
                    old_log.unlink()
                    removed_count += 1
                    print(f"🗑️  Removed old log file: {old_log}")
                except Exception as e:
                    print(f"❌ Error removing {old_log}: {e}")
            
            print(f"✅ Cleaned up {removed_count} old log files")
        else:
            print(f"ℹ️  Log files already clean: {len(log_files)} files")
    else:
        print("ℹ️  No logs directory found")

def check_disk_space():
    """Check and report disk space usage"""
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        disk_usage = shutil.disk_usage(data_dir)
        free_space_mb = disk_usage.free / (1024 * 1024)
        total_space_mb = disk_usage.total / (1024 * 1024)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        print(f"💾 Disk Space Report:")
        print(f"   Total: {total_space_mb:.1f}MB")
        print(f"   Free: {free_space_mb:.1f}MB")
        print(f"   Used: {used_percent:.1f}%")
        
        if used_percent > 95:
            print("🚨 CRITICAL: Disk almost full!")
        elif used_percent > 90:
            print("⚠️  WARNING: Disk getting full")
        else:
            print("✅ Disk space looks good")
            
    except Exception as e:
        print(f"❌ Error checking disk space: {e}")

def get_cache_sizes():
    """Report cache file sizes"""
    data_dir = Path("data")
    
    print(f"\n📊 Cache Size Report:")
    
    # Check processed emails file
    last_check_file = data_dir / "last_check.json"
    if last_check_file.exists():
        size_kb = last_check_file.stat().st_size / 1024
        print(f"   📝 Processed emails: {size_kb:.1f}KB")
    
    # Check log files
    logs_dir = data_dir / "logs"
    if logs_dir.exists():
        total_log_size = sum(f.stat().st_size for f in logs_dir.glob("bot.log*"))
        total_log_mb = total_log_size / (1024 * 1024)
        log_count = len(list(logs_dir.glob("bot.log*")))
        print(f"   📋 Log files: {total_log_mb:.1f}MB ({log_count} files)")
    
    # Check total data directory size
    if data_dir.exists():
        total_size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
        total_mb = total_size / (1024 * 1024)
        print(f"   📁 Total data directory: {total_mb:.1f}MB")

def main():
    print("🧹 Email Bot Cache Cleanup Tool")
    print("=" * 40)
    
    # Report current state
    get_cache_sizes()
    check_disk_space()
    
    print("\n🔧 Running cleanup...")
    
    # Perform cleanup
    cleanup_processed_emails()
    cleanup_log_files()
    
    print("\n📊 After cleanup:")
    get_cache_sizes()
    check_disk_space()
    
    print("\n✅ Cleanup complete!")
    print("\nNote: The bot will automatically clean up caches every hour during normal operation.")

if __name__ == "__main__":
    main()
