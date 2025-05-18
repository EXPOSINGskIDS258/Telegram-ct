"""
Utility functions for the Stratos Trading Bot
"""

import logging
import os
import json
import re
import subprocess
import platform
import sys
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def setup_logging(log_file='bot.log', log_level='INFO', log_to_file=True):
    """Setup logging configuration"""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = []
    if log_to_file:
        handlers.append(logging.FileHandler(log_file))
    handlers.append(logging.StreamHandler())
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger.info("Logging initialized")
    
def clean_channel_id(channel_id):
    """
    Clean and validate channel ID input
    Converts various formats to a consistent format
    """
    # Remove any non-alphanumeric characters except for - and _
    cleaned = re.sub(r'[^\w\-]', '', str(channel_id))
    
    # If it's a numeric ID, return as is
    if cleaned.isdigit():
        return int(cleaned)
    
    # If it's a channel username, ensure it has the @ prefix
    if not cleaned.startswith('@'):
        cleaned = '@' + cleaned
        
    return cleaned

def format_time_elapsed(seconds):
    """Format seconds into a readable time string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

def get_summary_stats(log_file='signal_log.json'):
    """Get summary statistics from the signal log"""
    if not os.path.exists(log_file):
        return {
            'total_signals': 0,
            'oldest_signal': None,
            'newest_signal': None,
            'sources': {}
        }
        
    try:
        signals = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    signal = json.loads(line.strip())
                    signals.append(signal)
                except json.JSONDecodeError:
                    continue
        
        if not signals:
            return {
                'total_signals': 0,
                'oldest_signal': None,
                'newest_signal': None,
                'sources': {}
            }
            
        # Count signals by source
        sources = {}
        for signal in signals:
            source = signal.get('source', 'unknown')
            if source in sources:
                sources[source] += 1
            else:
                sources[source] = 1
                
        # Sort by timestamp
        signals.sort(key=lambda x: x.get('timestamp', ''))
        
        return {
            'total_signals': len(signals),
            'oldest_signal': signals[0].get('timestamp'),
            'newest_signal': signals[-1].get('timestamp'),
            'sources': sources
        }
    except Exception as e:
        logger.error(f"Error getting summary stats: {str(e)}")
        return {
            'total_signals': 0,
            'oldest_signal': None,
            'newest_signal': None,
            'sources': {},
            'error': str(e)
        }

def is_valid_token_address(address):
    """Validate if string looks like a token contract address"""
    # Basic validation - should be 40+ hexadecimal characters
    if not address or not isinstance(address, str):
        return False
        
    # Check if it's a hexadecimal string of the right length
    hex_pattern = re.compile(r'^[a-fA-F0-9]{40,}$')
    return bool(hex_pattern.match(address))

def generate_status_report(bot, stats=None):
    """Generate a detailed status report"""
    if stats is None:
        stats = get_summary_stats()
        
    now = datetime.now()
    
    report = [
        "📊 **TELEGRAM COPY TRADING BOT - STATUS REPORT** 📊",
        "",
        f"📅 Report Time: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "🤖 **Bot Configuration**",
        f"• Monitoring: {len(bot.config.source_channels)} source channels",
        f"• Destination: {bot.config.destination_channel}",
        f"• Initial Stop Loss: {bot.config.initial_sl_percent}%",
        f"• Trailing Stop: {bot.config.trail_percent}%",
        f"• Signal Delay: {bot.config.delay_seconds} seconds",
        "",
        "📈 **Signal Statistics**",
        f"• Total Signals Copied: {stats['total_signals']}",
    ]
    
    # Add time period info if we have signals
    if stats['newest_signal'] and stats['oldest_signal']:
        try:
            newest = datetime.fromisoformat(stats['newest_signal'])
            oldest = datetime.fromisoformat(stats['oldest_signal'])
            time_span = newest - oldest
            
            report.extend([
                f"• First Signal: {oldest.strftime('%Y-%m-%d %H:%M:%S')}",
                f"• Latest Signal: {newest.strftime('%Y-%m-%d %H:%M:%S')}",
                f"• Time Span: {format_time_elapsed(time_span.total_seconds())}",
            ])
        except (ValueError, TypeError):
            pass
    
    # Add source breakdown if available
    if stats['sources']:
        report.append("")
        report.append("📋 **Signal Sources**")
        for source, count in stats['sources'].items():
            report.append(f"• {source}: {count} signals")
    
    # Add active tracking info
    if bot.price_tracker and hasattr(bot.price_tracker, 'tracking_signals'):
        active_tracking = len(bot.price_tracker.tracking_signals)
        report.extend([
            "",
            "🔍 **Active Tracking**",
            f"• Tokens Being Tracked: {active_tracking}"
        ])
        
        # Add some details about actively tracked tokens
        if active_tracking > 0:
            report.append("")
            report.append("🔎 **Currently Tracked Tokens**")
            for token, info in bot.price_tracker.tracking_signals.items():
                if not info['sl_triggered']:
                    entry = info['entry_price']
                    current = info['current_price']
                    highest = info['highest_price']
                    sl = info['current_sl_level']
                    change = ((current / entry) - 1) * 100
                    max_change = ((highest / entry) - 1) * 100
                    
                    report.extend([
                        f"• Token: {token[:8]}...{token[-6:]}",
                        f"  → Current P/L: {change:.2f}%",
                        f"  → Max P/L: {max_change:.2f}%",
                        f"  → Current SL: {((sl / current) - 1) * 100:.2f}% from price"
                    ])
    
    return "\n".join(report)

def open_env_file(env_file='.env'):
    """
    Open the .env file in the system's default text editor
    """
    try:
        # Create .env file with template if it doesn't exist
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write("""# Stratos Trading Bot Configuration
# You can edit this file directly to change settings

# Telegram API Configuration
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=

# Channel Configuration
# Comma-separated list of channel IDs to monitor
SOURCE_CHANNELS=

# Trading Parameters
POSITION_SIZE_PERCENT=3
INITIAL_SL_PERCENT=30
TRAIL_PERCENT=5
TAKE_PROFIT_LEVELS=20,40,100
MAX_SLIPPAGE=15
GAS_PRIORITY=3

# DEX Settings
DEX_NAME=PancakeSwap
CHAIN_NAME=BSC

# Wallet Address (private key is never stored here for security)
WALLET_ADDRESS=

# Paper Trading Mode (true/false)
PAPER_TRADING_MODE=true

# Memecoin Safety Settings
MIN_LIQUIDITY_USD=50000
MAX_BUY_TAX=10
MAX_SELL_TAX=15
HONEYPOT_CHECK=true
""")
            
        # Open the file with system's default application
        if platform.system() == 'Windows':
            os.startfile(os.path.abspath(env_file))
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', env_file], check=True)
        else:  # Linux and other systems
            subprocess.run(['xdg-open', env_file], check=True)
            
        logger.info(f"Opened .env file with system editor: {env_file}")
        return True
    except Exception as e:
        logger.error(f"Error opening .env file: {str(e)}")
        return False