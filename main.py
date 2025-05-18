"""
Enhanced main.py with Paper Trading Mode added to Stratos Trading Bot
"""

import asyncio
import logging
import sys
import os
import time
import random
from config import Config
from telegram_client import TelegramCopyTrader
from paper_trader import PaperTrader  # Import the new paper trading module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PREMIUM CHANNELS
DEFAULT_SOURCE_CHANNELS = [
    "-1002209371269",     # Underdog Calls Private
    "-1002277274250"      # Underdogs Degen
]

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def center_text(text, width=80):
    """Center a block of text"""
    lines = text.split('\n')
    centered_lines = [line.center(width) for line in lines]
    return '\n'.join(centered_lines)

def display_stratos_logo():
    """Display an elaborate ASCII art logo for Stratos"""
    logo = """
         ██████╗████████╗██████╗  █████╗ ████████╗ ██████╗  ██████╗
        ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝
        ╚█████╗    ██║   ██████╔╝███████║   ██║   ██║   ██║╚█████╗ 
         ╚═══██╗   ██║   ██╔══██╗██╔══██║   ██║   ██║   ██║ ╚═══██╗
        ██████╔╝   ██║   ██║  ██║██║  ██║   ██║   ╚██████╔╝██████╔╝
        ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═════╝ 
    """
    
    triangle = """
                                   ▲
                                 ◢◣◤◥
                               ◢███◤◥███◣
                             ◢███████████◣
                           ◢█████████████◣
                         ◢███████████████◣
                       ◢█████████████████◣
                     ◢███████████████████◣
                   ◢█████████████████████◣
                 ◢███████████████████████◣
               ◢█████████████████████████◣
             ◤▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼◥
    """
    
    tagline = """
    ╭──────────────── AUTOMATED TRADING SYSTEM ────────────────╮
    │                                                          │
    │         MEMECOIN SIGNALS · AUTOMATED EXECUTION           │
    │                                                          │
    ╰──────────────────────────────────────────────────────────╯
    """
    
    print(center_text(logo))
    print(center_text(triangle))
    print(center_text(tagline))

def display_premium_frame(title="", content="", width=80, title_align="center"):
    """Display content in a premium decorative frame"""
    horizontal_border = "═" * (width - 2)
    empty_line = "║" + " " * (width - 2) + "║"
    
    # Print top border with title if provided
    print("╔" + horizontal_border + "╗")
    
    if title:
        if title_align == "center":
            title_line = "║" + title.center(width - 2) + "║"
        elif title_align == "left":
            title_line = "║ " + title + " " * (width - 3 - len(title)) + "║"
        print(title_line)
        print("║" + "─" * (width - 2) + "║")  # Separator line
    
    # Print empty line for padding
    print(empty_line)
    
    # Print content
    if content:
        lines = content.split('\n')
        for line in lines:
            # Handle lines longer than width
            while len(line) > width - 4:
                print("║  " + line[:width-6] + "  ║")
                line = line[width-6:]
            print("║  " + line.ljust(width - 4) + "║")
    
    # Print empty line for padding
    print(empty_line)
    
    # Print bottom border
    print("╚" + horizontal_border + "╝")

def display_button(text, selected=False, width=30):
    """Display a button-like element"""
    if selected:
        border_top = "┏" + "━" * (width - 2) + "┓"
        border_bottom = "┗" + "━" * (width - 2) + "┛"
        button_text = "┃" + ("▶ " + text).center(width - 2) + "┃"
    else:
        border_top = "┌" + "─" * (width - 2) + "┐"
        border_bottom = "└" + "─" * (width - 2) + "┘"
        button_text = "│" + text.center(width - 2) + "│"
    
    print(border_top)
    print(button_text)
    print(border_bottom)

def display_input_field(label, width=40):
    """Display a stylish input field"""
    print("┌" + "─" * (width - 2) + "┐")
    print("│ " + label.ljust(width - 3) + "│")
    print("└" + "─" * (width - 2) + "┘")
    return input("  ⮞ ")

def display_progress_bar(progress, width=50):
    """Display a progress bar with percentage"""
    bar_width = width - 10  # Leave room for percentage
    filled_width = int(bar_width * progress / 100)
    bar = '█' * filled_width + '░' * (bar_width - filled_width)
    percentage = f"{progress}%".rjust(4)
    print(f"[{bar}] {percentage}")

def display_loading_animation(text, duration=2, width=40):
    """Display a loading animation"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    steps = int(duration * 10)  # 10 frames per second
    
    for i in range(steps):
        char = chars[i % len(chars)]
        spaces = width - len(text) - 1
        print(f"\r{char} {text}{' ' * spaces}", end='', flush=True)
        time.sleep(0.1)
    print()

def display_notification(message, message_type="info"):
    """Display a notification message with appropriate styling"""
    width = 80
    if message_type == "success":
        prefix = "✓ "
        style = "━"
    elif message_type == "error":
        prefix = "✗ "
        style = "━"
    elif message_type == "warning":
        prefix = "⚠ "
        style = "─"
    else:  # info
        prefix = "ℹ "
        style = "─"
    
    print("\n" + style * width)
    print(f"{prefix}{message}")
    print(style * width + "\n")

def display_disclaimer():
    """Display the disclaimer screen"""
    clear_screen()
    display_stratos_logo()
    
    disclaimer_title = "IMPORTANT RISK DISCLOSURE"
    
    disclaimer_content = """
• Stratos is not liable for any financial losses.

• All transactions and trades are conducted at your own risk.

• We do not provide financial advice.

• Past performance is not indicative of future results.

• Trading involves substantial risk of loss.

• Only risk capital you can afford to lose.

• Seek independent financial advice if needed.

• You are solely responsible for your trading decisions.

By using Stratos services, you acknowledge and accept these risks.
"""
    
    display_premium_frame(disclaimer_title, disclaimer_content, width=76)
    
    print("\n" + "═" * 76)
    print("Do you accept these terms and wish to continue?".center(76))
    print("═" * 76 + "\n")
    
    display_button("YES (Y)", selected=True, width=36)
    print()
    display_button("NO (N)", selected=False, width=36)
    print()
    
    while True:
        response = input("  ⮞ ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            display_notification("Please enter Y or N to continue.", "warning")

def display_trade_mode_selection():
    """Display trading mode selection screen (Live or Paper Trading)"""
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("TRADING MODE SELECTION", width=76)
    
    print("""
  Select your preferred trading mode:
    """)
    
    # Paper Trading Button
    print("1)")
    display_premium_frame("PAPER TRADING MODE", """
Paper trading allows you to test the bot with virtual funds. 
No real money is at risk, and trades are simulated based on real market data.

• Start with $10,000 virtual balance
• Test trading strategies risk-free
• Analyze performance before going live
• Perfect for learning and testing

Recommended for new users or testing new strategies.
""", width=70)
    
    # Live Trading Button
    print("\n2)")
    display_premium_frame("LIVE TRADING MODE", """
Live trading executes real trades with your actual funds.
All transactions will be performed on-chain using your connected wallet.

• Trade with real funds
• Execute actual blockchain transactions
• Full access to all trading features
• Monitor real-time performance

Only use live trading when you are confident in your strategy.
""", width=70)
    
    print("\nEnter your selection (1-2):")
    
    while True:
        try:
            choice = int(input("  ⮞ ").strip())
            if choice in [1, 2]:
                return choice
            else:
                display_notification("Please enter 1 or 2 to continue.", "warning")
        except ValueError:
            display_notification("Please enter 1 or 2 to continue.", "warning")

def display_channel_selection():
    """Display the channel selection screen"""
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("SIGNAL CHANNEL CONFIGURATION", width=76)
    
    premium_channel_content = """
• Underdog Calls Private
  Professional signal provider with proven track record

• Underdogs Degen
  Early memecoin signals with high profit potential

Our team has selected the best memecoin signal channels with proven track records.
All signals will be automatically analyzed and traded according to your parameters.
"""
    
    custom_channel_content = """
Specify your own channel IDs to monitor for trading signals.
This option requires you to know which channels provide reliable signals.
You'll need the channel IDs for the channels you want to monitor.
"""
    
    print("\nSelect your preferred signal source:\n")
    
    # Option 1 - Premium Channels
    print("1)")
    display_premium_frame("PREMIUM CHANNELS", premium_channel_content, width=70)
    
    # Option 2 - Custom Channels
    print("\n2)")
    display_premium_frame("CUSTOM CHANNELS", custom_channel_content, width=70)
    
    print("\nEnter your selection (1-2):")
    
    while True:
        try:
            choice = int(input("  ⮞ ").strip())
            if choice in [1, 2]:
                return choice
            else:
                display_notification("Please enter 1 or 2 to continue.", "warning")
        except ValueError:
            display_notification("Please enter 1 or 2 to continue.", "warning")

def get_wallet_private_key():
    """Get the user's wallet private key"""
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("WALLET CONFIGURATION", width=76)
    
    print("""
  To enable automated trading, Stratos needs access to your wallet.
  Your private key is only stored in memory and never saved to disk.
  
  ┌───────────────────────────────────────────────────────────────┐
  │ SECURITY NOTE: Your private key will be encrypted in memory   │
  │ and is never stored in plain text or transmitted anywhere.    │
  └───────────────────────────────────────────────────────────────┘
    """)
    
    wallet_address = display_input_field("Enter Your Wallet Address", width=70)
    private_key = display_input_field("Enter Your Private Key", width=70)
    
    if not wallet_address or not private_key:
        display_notification("Wallet information is required for trading.", "warning")
    
    return {
        'wallet_address': wallet_address,
        'private_key': private_key
    }

def configure_paper_trading():
    """Configure paper trading settings"""
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("PAPER TRADING CONFIGURATION", width=76)
    
    print("""
  Configure your paper trading account settings.
  These settings will be used to simulate trading without real funds.
    """)
    
    # Get initial balance
    initial_balance = display_input_field("Initial Virtual Balance (USD, default: $10,000)", width=70)
    initial_balance = float(initial_balance) if initial_balance else 10000.0
    
    # Get simulated fees
    fee_percentage = display_input_field("Simulated Trading Fee (%, default: 0.25%)", width=70)
    fee_percentage = float(fee_percentage) if fee_percentage else 0.25
    
    # Get simulated slippage range
    slippage_range = display_input_field("Simulated Slippage Range (%, default: 0.1-3%)", width=70)
    slippage_range = slippage_range if slippage_range else "0.1-3"
    
    # Ask if they want to reset existing paper trading data
    reset_existing = display_input_field("Reset Existing Paper Trading Data? (y/n, default: n)", width=70)
    reset_existing = reset_existing.lower() == 'y'
    
    return {
        'initial_balance': initial_balance,
        'fee_percentage': fee_percentage,
        'slippage_range': slippage_range,
        'reset_existing': reset_existing
    }

async def configure_trading_parameters():
    """Configure trading parameters with sophisticated UI"""
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("TRADING PARAMETERS", width=76)
    
    print("""
  Configure how Stratos will execute trades on your behalf.
  These parameters determine position sizes, stop losses, and take profits.
  
  ┌───────────────────────────────────────────────────────────────┐
  │ RECOMMENDED: Use conservative values when starting            │
  │ You can always adjust these parameters later                  │
  └───────────────────────────────────────────────────────────────┘
    """)
    
    parameters = {}
    
    # Position size
    print("\n" + "─" * 76)
    print("POSITION SIZING".center(76))
    print("─" * 76)
    position_size = display_input_field("Position Size (% of portfolio per trade, default 3%)", width=70)
    parameters['position_size'] = float(position_size) if position_size else 3.0
    
    # Risk management
    print("\n" + "─" * 76)
    print("RISK MANAGEMENT".center(76))
    print("─" * 76)
    
    initial_sl = display_input_field("Initial Stop Loss (%, default 30%)", width=70)
    parameters['initial_sl'] = float(initial_sl) if initial_sl else 30.0
    
    trail_percent = display_input_field("Trailing Stop (%, default 5%)", width=70)
    parameters['trail_percent'] = float(trail_percent) if trail_percent else 5.0
    
    take_profit = display_input_field("Take Profit Levels (comma-separated %, default 20,40,100)", width=70)
    parameters['take_profit_levels'] = take_profit if take_profit else "20,40,100"
    
    # Advanced settings
    print("\n" + "─" * 76)
    print("ADVANCED SETTINGS".center(76))
    print("─" * 76)
    
    max_slippage = display_input_field("Maximum Slippage (%, default 15%)", width=70)
    parameters['max_slippage'] = float(max_slippage) if max_slippage else 15.0
    
    gas_priority = display_input_field("Gas Priority (1-5, where 5 is fastest, default 3)", width=70)
    parameters['gas_priority'] = int(gas_priority) if gas_priority else 3
    
    # Memecoin-specific settings
    print("\n" + "─" * 76)
    print("MEMECOIN SAFETY SETTINGS".center(76))
    print("─" * 76)
    
    min_liquidity = display_input_field("Minimum Liquidity in USD (default 50000)", width=70)
    parameters['min_liquidity'] = float(min_liquidity) if min_liquidity else 50000
    
    max_buy_tax = display_input_field("Maximum Buy Tax (%, default 10%)", width=70)
    parameters['max_buy_tax'] = float(max_buy_tax) if max_buy_tax else 10.0
    
    max_sell_tax = display_input_field("Maximum Sell Tax (%, default 15%)", width=70)
    parameters['max_sell_tax'] = float(max_sell_tax) if max_sell_tax else 15.0
    
    honeypot_check = display_input_field("Enable Honeypot Check? (y/n, default y)", width=70)
    parameters['honeypot_check'] = honeypot_check.lower() != 'n'
    
    return parameters

async def display_paper_trading_dashboard(paper_trader):
    """Display paper trading dashboard with performance metrics"""
    clear_screen()
    display_stratos_logo()
    
    # Get account summary and open positions
    summary = paper_trader.get_account_summary()
    positions = paper_trader.get_open_positions()
    
    # Display account overview
    display_premium_frame("PAPER TRADING DASHBOARD", width=76)
    
    # Account balance section
    print("\n" + "─" * 76)
    print("ACCOUNT OVERVIEW".center(76))
    print("─" * 76 + "\n")
    
    print(f"  Virtual Balance:      ${summary['virtual_balance']:.2f}")
    print(f"  Open Positions Value: ${summary['open_positions_value']:.2f}")
    print(f"  Total Account Value:  ${summary['total_value']:.2f}")
    print(f"  Total Profit/Loss:    ${summary['total_profit_loss']:.2f}")
    
    # Performance metrics
    print("\n" + "─" * 76)
    print("PERFORMANCE METRICS".center(76))
    print("─" * 76 + "\n")
    
    print(f"  Win Rate:             {summary['win_rate']:.2f}%")
    print(f"  Total Trades:         {summary['total_trades']}")
    print(f"  Winning Trades:       {summary['win_trades']}")
    print(f"  Losing Trades:        {summary['loss_trades']}")
    print(f"  Days Trading:         {summary['days_running']:.1f}")
    
    # Open positions
    print("\n" + "─" * 76)
    print(f"OPEN POSITIONS ({len(positions)})".center(76))
    print("─" * 76 + "\n")
    
    if positions:
        # Header
        print(f"  {'Symbol':<8} {'Entry':<10} {'Current':<10} {'Amount':<12} {'Value':<10} {'P/L %':<8}")
        print("  " + "-" * 70)
        
        # List positions
        for pos in positions:
            pnl_str = f"{pos['pnl_percentage']:.2f}%"
            if pos['pnl_percentage'] > 0:
                pnl_str = "+" + pnl_str
                
            print(f"  {pos['symbol']:<8} ${pos['entry_price']:<9.6f} ${pos['current_price']:<9.6f} " + 
                  f"{pos['amount']:<12.4f} ${pos['value_usd']:<9.2f} {pnl_str:<8}")
    else:
        print("  No open positions")
    
    # Controls
    print("\n" + "─" * 76)
    print("CONTROLS".center(76))
    print("─" * 76 + "\n")
    
    print("  Bot is now monitoring channels for trading signals.")
    print("  All signals will be traded using your paper trading account.")
    print("  Press Ctrl+C to exit.")
    
    # Wait for user input or Ctrl+C
    try:
        while True:
            await asyncio.sleep(60)  # Refresh every 60 seconds
            await display_paper_trading_dashboard(paper_trader)
    except KeyboardInterrupt:
        return

async def system_initialization(is_paper_trading=False):
    """Display an impressive system initialization sequence"""
    clear_screen()
    display_stratos_logo()
    
    mode_text = "PAPER TRADING" if is_paper_trading else "LIVE TRADING"
    display_premium_frame(f"SYSTEM INITIALIZATION ({mode_text})", width=76)
    
    # Initialize core systems
    print("\n▶ Initializing Core Systems")
    display_loading_animation("Loading configuration manager", 1.5)
    display_progress_bar(20)
    
    display_loading_animation("Initializing trading engine", 2)
    display_progress_bar(40)
    
    # Connect to networks
    print("\n▶ Establishing Network Connections")
    display_loading_animation("Connecting to Telegram API", 1.5)
    display_progress_bar(60)
    
    if not is_paper_trading:
        display_loading_animation("Connecting to blockchain network", 2)
    else:
        display_loading_animation("Initializing paper trading system", 2)
    display_progress_bar(80)
    
    # Load trading module
    print("\n▶ Loading Trading Modules")
    display_loading_animation("Initializing memecoin analyzer", 1)
    display_loading_animation("Loading risk management system", 1)
    
    if not is_paper_trading:
        display_loading_animation("Configuring automated trading system", 1.5)
    else:
        display_loading_animation("Configuring paper trading simulator", 1.5)
    display_progress_bar(100)
    
    display_notification("All systems initialized successfully", "success")
    
    time.sleep(1)
    clear_screen()
    display_stratos_logo()
    
    status_message = f"""
  ▶ Telegram Connection:    ACTIVE
  ▶ {"Blockchain Connection:  ACTIVE" if not is_paper_trading else "Paper Trading System:  ACTIVE"}
  ▶ Signal Monitoring:      ACTIVE
  ▶ Trading Engine:         ACTIVE
  ▶ Risk Management:        ACTIVE
  
  Stratos Trading Bot is now monitoring channels for trading signals.
  All detected signals will be {"analyzed and traded automatically" if not is_paper_trading else "simulated in paper trading mode"}.
  """
    
    display_premium_frame(f"SYSTEM OPERATIONAL ({mode_text})", status_message, width=76)
    
    print("\nPress Ctrl+C at any time to stop the bot.")

async def setup_bot():
    """Setup and configure the bot with premium UI and paper trading support"""
    # Show logo and disclaimer
    if not display_disclaimer():
        clear_screen()
        display_notification("Setup cancelled by user. Exiting...", "error")
        return
    
    # Let the user choose between paper trading and live trading
    trading_mode = display_trade_mode_selection()
    is_paper_trading = (trading_mode == 1)
    
    # Get channel configuration preference
    channel_choice = display_channel_selection()
    
    # Paper trading doesn't require a wallet, but live trading does
    wallet_info = None
    if not is_paper_trading:
        # Get wallet information directly (only for live trading)
        wallet_info = get_wallet_private_key()
        
        if not wallet_info or not wallet_info['private_key']:
            clear_screen()
            display_notification("Wallet information incomplete. Setup cancelled.", "error")
            return
    
    # Configure paper trading if selected
    paper_trading_config = None
    if is_paper_trading:
        paper_trading_config = configure_paper_trading()
    
    # Get Telegram API credentials
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("TELEGRAM API CONFIGURATION", width=76)
    
    print("""
  Stratos needs your Telegram API credentials to monitor signal channels.
  You can get these from https://my.telegram.org/apps
    """)
    
    api_id = display_input_field("Telegram API ID", width=70)
    api_hash = display_input_field("Telegram API Hash", width=70)
    phone = display_input_field("Phone Number (with country code)", width=70)
    
    if not api_id or not api_hash or not phone:
        clear_screen()
        display_notification("Telegram API credentials are required. Setup cancelled.", "error")
        return
    
    # Configure trading parameters (both modes need this)
    trading_params = await configure_trading_parameters()
    
    # Create and configure the bot
    config = Config()
    
    # Save API credentials
    config.api_id = int(api_id)
    config.api_hash = api_hash
    config.phone = phone
    
    # Configure channels based on user choice
    if channel_choice == 1:  # Premium channels
        config.source_channels = DEFAULT_SOURCE_CHANNELS
    else:  # Custom channels
        clear_screen()
        display_stratos_logo()
        
        display_premium_frame("CUSTOM CHANNEL CONFIGURATION", width=76)
        
        source_channel1 = display_input_field("Source Channel ID 1", width=70)
        source_channel2 = display_input_field("Source Channel ID 2 (optional)", width=70)
        
        # Build source channels list
        if source_channel2.strip():
            config.source_channels = [source_channel1, source_channel2]
        else:
            config.source_channels = [source_channel1]
    
    # Set default DEX and chain (we'll use PancakeSwap/BSC for both modes)
    config.dex_name = "PancakeSwap"
    config.chain_name = "BSC"
    
    # Store wallet information (for live trading only)
    if not is_paper_trading and wallet_info:
        config.wallet_address = wallet_info['wallet_address']
        config.private_key = wallet_info['private_key']
    
    # Configure trading parameters (for both modes)
    config.position_size_percent = trading_params['position_size']
    config.max_slippage = trading_params['max_slippage']
    config.gas_priority = trading_params['gas_priority']
    config.initial_sl_percent = trading_params['initial_sl']
    config.trail_percent = trading_params['trail_percent']
    config.take_profit_levels = trading_params['take_profit_levels']
    
    # Memecoin settings
    config.min_liquidity_usd = trading_params['min_liquidity']
    config.max_buy_tax = trading_params['max_buy_tax']
    config.max_sell_tax = trading_params['max_sell_tax']
    config.honeypot_check = trading_params['honeypot_check']
    
    # Save paper trading mode in config
    config.paper_trading_mode = is_paper_trading
    
    # Save configuration
    config.save()
    display_notification("Configuration saved successfully", "success")
    
    # Initialize paper trader if in paper trading mode
    paper_trader = None
    if is_paper_trading:
        paper_trader = PaperTrader(config)
        
        # Reset paper trading data if requested
        if paper_trading_config and paper_trading_config['reset_existing']:
            paper_trader.reset_account(paper_trading_config['initial_balance'])
    
    # Initialize system
    await system_initialization(is_paper_trading)
    
    # In paper trading mode, show the dashboard
    if is_paper_trading:
        await display_paper_trading_dashboard(paper_trader)
    else:
        # Create and start the bot in live trading mode
        bot = TelegramCopyTrader(config)
        await bot.start()

# Main entry point
if __name__ == "__main__":
    try:
        clear_screen()  # Start with a clean screen
        asyncio.run(setup_bot())
    except KeyboardInterrupt:
        clear_screen()
        display_stratos_logo()
        display_notification("Stratos Trading Bot stopped by user", "info")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        clear_screen()
        display_stratos_logo()
        display_notification(f"Error: {str(e)}", "error")
        print("Check bot.log for details.")