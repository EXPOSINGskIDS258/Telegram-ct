Telegram Copy Trading Bot
A high-speed Python bot that monitors Telegram channels for memecoin trading signals, copies them to your channel with custom branding, and implements a trailing stop-loss system.
Features

Real-time Monitoring: Watches multiple Telegram channels simultaneously
Fast Signal Copying: Minimal delay between source and destination
Memecoin Detection: Automatically detects token addresses in messages
Custom Branding: Replaces original branding with your own
Trailing Stop-Loss: Automatically adjusts stop-loss levels as price increases
Duplicate Prevention: Prevents the same signal from being copied multiple times
Comprehensive Logging: Tracks all signals with timestamps for later analysis

Requirements

Python 3.7+
telethon library for Telegram API access
aiohttp library for asynchronous HTTP requests
Telegram API credentials (API ID and API hash)

Installation

Clone this repository or download the source code
Install required dependencies:
pip install telethon aiohttp

Run the bot:
python main.py


First-Time Setup
On first run, the bot will prompt you to enter the following information:

Telegram API ID and API hash (obtain from https://my.telegram.org/apps)
Your phone number (for Telegram authentication)
Source channel IDs (the channels you want to monitor)
Destination channel ID (where signals will be copied)
Custom branding text
Stop-loss settings (initial percentage and trailing percentage)
Optional delay in seconds

This information will be saved in config.json for future use.
Project Structure
telegram_copytrader/
│
├── main.py                # Entry point
├── config.py              # Configuration management
├── signal_handler.py      # Signal detection and processing
├── price_tracker.py       # Price monitoring and stop-loss
├── telegram_client.py     # Telegram client operations
├── utils.py               # Utility functions
└── README.md              # Instructions
Customization
Price API Integration
The price tracking functionality uses a simulated price feed by default for testing. For production use, you should modify the get_current_price() method in price_tracker.py to use your preferred price data source:

PancakeSwap API (for BSC tokens)
CoinGecko API
Custom price data API

Message Formatting
You can customize how copied messages appear by modifying the format_message() method in signal_handler.py.
Packaging as an Executable
To create an executable for distribution:

Install PyInstaller:
pip install pyinstaller

Create the executable:
pyinstaller --onefile --name TelegramCopyTrader main.py

Find the executable in the dist folder

Best Practices

Run the bot on a VPS or reliable server with 24/7 uptime
Use a dedicated Telegram account for the bot
Be careful with sharing your API credentials
Test thoroughly with simulated price data before using real price tracking

License
This software is provided for educational purposes only. Use at your own risk.
Disclaimer
Trading cryptocurrencies involves significant risk. This bot is a tool and does not guarantee profits. Always do your own research before trading.