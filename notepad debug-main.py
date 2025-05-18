"""
Debug version of main.py with error tracking
"""

import asyncio
import logging
import sys
import os
import time
import traceback
from config import Config
from telegram_client import TelegramCopyTrader

# Configure basic logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ANSI color codes - minimal palette
BOLD = '\033[1m'
NORMAL = '\033[0m'
WHITE = '\033[97m'
GRAY = '\033[90m'
RESET = '\033[0m'

# DEBUG POINTS
def debug_point(msg):
    """Print debug point message and log it"""
    print(f"DEBUG: {msg}")
    logger.info(f"DEBUG POINT: {msg}")

def clear_screen():
    """Clear the terminal screen - simplified version"""
    print("\n" * 5)  # Just print newlines instead of using system commands
    debug_point("Screen cleared")

def display_stratos_logo():
    """Simplified logo for debugging"""
    print("STRATOS LOGO DISPLAYED")
    debug_point("Logo displayed")

def display_simple_message(message):
    """Display a simple message without fancy formatting"""
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")
    debug_point(f"Message displayed: {message}")

def get_user_input(prompt):
    """Get user input with error handling"""
    try:
        debug_point(f"Asking for input: {prompt}")
        value = input(prompt + " ")
        debug_point(f"Received input: {value}")
        return value
    except Exception as e:
        debug_point(f"Error getting input: {str(e)}")
        return None

async def setup_bot():
    """Setup and configure the bot - simplified for debugging"""
    try:
        debug_point("Starting setup_bot function")
        
        # Show simplified welcome message
        clear_screen()
        display_stratos_logo()
        display_simple_message("Welcome to Stratos Trading Bot")
        
        # Ask for disclaimer acceptance
        response = get_user_input("Do you accept the terms? (Y/N):")
        if response.lower() != 'y':
            debug_point("User declined terms")
            return
            
        # Simple channel selection
        display_simple_message("CHANNEL SELECTION")
        choice = get_user_input("Choose channel option (1-2):")
        
        # Get wallet info
        display_simple_message("WALLET CONFIGURATION")
        wallet_address = get_user_input("Wallet Address:")
        private_key = get_user_input("Private Key:")
        
        # Get Telegram API info
        display_simple_message("TELEGRAM API CONFIGURATION")
        api_id = get_user_input("Telegram API ID:")
        api_hash = get_user_input("Telegram API Hash:")
        phone = get_user_input("Phone Number:")
        
        # Display success
        display_simple_message("Configuration complete! Starting bot...")
        
        # Initialize configuration
        debug_point("Creating Config object")
        config = Config()
        
        # Store configuration
        config.api_id = int(api_id) if api_id.isdigit() else 0
        config.api_hash = api_hash
        config.phone = phone
        config.wallet_address = wallet_address
        config.private_key = private_key
        
        # Use premium channels by default
        config.source_channels = [
            "-1002209371269",     # Underdog Calls Private
            "-1002277274250"      # Underdogs Degen
        ]
        
        # Set defaults
        config.dex_name = "PancakeSwap"
        config.chain_name = "BSC"
        
        # Save configuration
        debug_point("Saving configuration")
        config.save()
        
        # Start bot
        debug_point("Creating TelegramCopyTrader instance")
        bot = TelegramCopyTrader(config)
        
        debug_point("Starting bot")
        await bot.start()
        
    except Exception as e:
        debug_point(f"ERROR in setup_bot: {str(e)}")
        traceback.print_exc()

# Main entry point
if __name__ == "__main__":
    print("\n\n==== STARTING STRATOS TRADING BOT - DEBUG MODE ====\n\n")
    debug_point("Main script started")
    
    try:
        debug_point("Running setup_bot via asyncio.run")
        asyncio.run(setup_bot())
    except KeyboardInterrupt:
        debug_point("Bot stopped by user (KeyboardInterrupt)")
        print("\nBot stopped by user")
    except Exception as e:
        debug_point(f"Fatal error in main: {str(e)}")
        traceback.print_exc()
        print(f"\nFatal Error: {str(e)}")