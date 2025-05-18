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

# Helper function to safely parse numeric inputs
def parse_float(value, default=None):
    """
    Safely parse a string to float, handling commas and percentage signs in the input.
    Returns the default value if parsing fails.
    """
    if not value:
        return default
        
    try:
        # First, remove any percentage sign if it exists
        if "%" in value:
            value = value.replace("%", "")
            
        # Remove commas and any other non-numeric characters except decimal point
        cleaned_value = ''.join(c for c in value if c.isdigit() or c == '.')
        
        return float(cleaned_value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing float value '{value}': {str(e)}")
        return default

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
    initial_balance = parse_float(initial_balance, 10000.0)
    
    # Get simulated fees
    fee_percentage = display_input_field("Simulated Trading Fee (%, default: 0.25%)", width=70)
    fee_percentage = parse_float(fee_percentage, 0.25)
    
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
    parameters['position_size'] = parse_float(position_size, 3.0)
    
    # Risk management
    print("\n" + "─" * 76)
    print("RISK MANAGEMENT".center(76))
    print("─" * 76)
    
    initial_sl = display_input_field("Initial Stop Loss (%, default 30%)", width=70)
    parameters['initial_sl'] = parse_float(initial_sl, 30.0)
    
    trail_percent = display_input_field("Trailing Stop (%, default 5%)", width=70)
    parameters['trail_percent'] = parse_float(trail_percent, 5.0)
    
    take_profit = display_input_field("Take Profit Levels (comma-separated %, default 20,40,100)", width=70)
    parameters['take_profit_levels'] = take_profit if take_profit else "20,40,100"
    
    # Advanced settings
    print("\n" + "─" * 76)
    print("ADVANCED SETTINGS".center(76))
    print("─" * 76)
    
    max_slippage = display_input_field("Maximum Slippage (%, default 15%)", width=70)
    parameters['max_slippage'] = parse_float(max_slippage, 15.0)
    
    gas_priority = display_input_field("Gas Priority (1-5, where 5 is fastest, default 3)", width=70)
    parameters['gas_priority'] = int(parse_float(gas_priority, 3))
    
    # Memecoin-specific settings
    print("\n" + "─" * 76)
    print("MEMECOIN SAFETY SETTINGS".center(76))
    print("─" * 76)
    
    min_liquidity = display_input_field("Minimum Liquidity in USD (default 50000)", width=70)
    parameters['min_liquidity'] = parse_float(min_liquidity, 50000)
    
    max_buy_tax = display_input_field("Maximum Buy Tax (%, default 10%)", width=70)
    parameters['max_buy_tax'] = parse_float(max_buy_tax, 10.0)
    
    max_sell_tax = display_input_field("Maximum Sell Tax (%, default 15%)", width=70)
    parameters['max_sell_tax'] = parse_float(max_sell_tax, 15.0)
    
    honeypot_check = display_input_field("Enable Honeypot Check? (y/n, default y)", width=70)
    parameters['honeypot_check'] = honeypot_check.lower() != 'n'
    
    return parameters

async def display_paper_trading_dashboard(paper_trader, bot_state=None):
    """Display paper trading dashboard with performance metrics and interactive controls"""
    if bot_state is None:
        bot_state = {
            'paused': False,
            'auto_execution': True
        }
    
    while True:
        clear_screen()
        display_stratos_logo()
        
        # Get account summary and open positions
        summary = paper_trader.get_account_summary()
        positions = paper_trader.get_open_positions()
        
        # Display account overview with status indicators
        status = "PAUSED" if bot_state['paused'] else "ACTIVE"
        execution_mode = "AUTO" if bot_state['auto_execution'] else "MANUAL"
        title = f"PAPER TRADING DASHBOARD | STATUS: {status} | MODE: {execution_mode}"
        display_premium_frame(title, width=76)
        
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
            print(f"  {'ID':<4} {'Symbol':<8} {'Entry':<10} {'Current':<10} {'Amount':<12} {'Value':<10} {'P/L %':<8}")
            print("  " + "-" * 70)
            
            # List positions
            for i, pos in enumerate(positions, 1):
                pnl_str = f"{pos['pnl_percentage']:.2f}%"
                if pos['pnl_percentage'] > 0:
                    pnl_str = "+" + pnl_str
                    
                print(f"  {i:<4} {pos['symbol']:<8} ${pos['entry_price']:<9.6f} ${pos['current_price']:<9.6f} " + 
                    f"{pos['amount']:<12.4f} ${pos['value_usd']:<9.2f} {pnl_str:<8}")
        else:
            print("  No open positions")
        
        # Interactive Controls
        print("\n" + "─" * 76)
        print("INTERACTIVE CONTROLS".center(76))
        print("─" * 76 + "\n")
        
        # Primary Controls - First Row
        print("  [1] Close All Positions     [2] " + ("Resume Bot" if bot_state['paused'] else "Pause Bot") + 
              "     [3] " + ("Enable Auto-Execution" if not bot_state['auto_execution'] else "Disable Auto-Execution"))
        
        # Secondary Controls - Second Row
        print("  [4] Reset Virtual Account   [5] Reset Stats             [6] Modify Trading Parameters")
        
        # Additional Controls - Third Row
        print("  [7] View Trade History      [8] Close Specific Position [9] View Signal Log")
        
        # Exit option
        print("\n  [0] Refresh Dashboard        [Q] Exit Dashboard")
        
        # Get user command
        print("\n  Enter command:")
        command = input("  ⮞ ").strip()
        
        # Process command
        if command.lower() == 'q':
            return
        
        await process_dashboard_command(command, paper_trader, bot_state)


async def process_dashboard_command(command, paper_trader, bot_state):
    """Process dashboard command entered by the user"""
    try:
        # Convert to lowercase for case-insensitive comparison
        cmd = command.lower().strip()
        
        if cmd == '1':  # Close All Positions
            if not paper_trader.get_open_positions():
                await display_command_result("No open positions to close.")
                return
                
            # Ask for confirmation
            confirm = input("  ⚠️ Confirm closing ALL positions (y/n): ").lower()
            if confirm == 'y':
                for pos in paper_trader.get_open_positions():
                    await paper_trader.close_paper_position(pos['symbol'], 'manual_close')
                await display_command_result("✅ All positions closed successfully.")
            else:
                await display_command_result("Operation cancelled.")
                
        elif cmd == '2':  # Pause/Resume Bot
            bot_state['paused'] = not bot_state['paused']
            status = "paused" if bot_state['paused'] else "resumed"
            await display_command_result(f"✅ Bot {status} successfully.")
            
        elif cmd == '3':  # Toggle Auto-Execution
            bot_state['auto_execution'] = not bot_state['auto_execution']
            mode = "AUTO" if bot_state['auto_execution'] else "MANUAL"
            await display_command_result(f"✅ Execution mode set to {mode}.")
            
        elif cmd == '4':  # Reset Virtual Account
            # Ask for confirmation
            confirm = input("  ⚠️ This will reset your account balance and positions. Confirm (y/n): ").lower()
            if confirm == 'y':
                initial_balance = input("  Enter new initial balance (default: 10000): ")
                initial_balance = parse_float(initial_balance, 10000.0)
                paper_trader.reset_account(initial_balance)
                await display_command_result(f"✅ Account reset with ${initial_balance:.2f} balance.")
            else:
                await display_command_result("Operation cancelled.")
                
        elif cmd == '5':  # Reset Stats
            # Ask for confirmation
            confirm = input("  ⚠️ This will reset your trading statistics. Confirm (y/n): ").lower()
            if confirm == 'y':
                # Reset stats while keeping positions and balance
                paper_trader.reset_stats()
                await display_command_result("✅ Trading statistics reset successfully.")
            else:
                await display_command_result("Operation cancelled.")
                
        elif cmd == '6':  # Modify Trading Parameters
            await modify_trading_parameters(paper_trader)
            
        elif cmd == '7':  # View Trade History
            await view_trade_history(paper_trader)
            
        elif cmd == '8':  # Close Specific Position
            await close_specific_position(paper_trader)
            
        elif cmd == '9':  # View Signal Log
            await view_signal_log(paper_trader)
            
        elif cmd == '0':  # Refresh Dashboard
            # Just return to refresh
            return
            
        else:
            await display_command_result("Invalid command. Please try again.")
            
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        await display_command_result(f"❌ Error: {str(e)}")

async def display_command_result(message, wait_time=1.5):
    """Display the result of a command with a styled message"""
    print("\n  " + "─" * 74)
    print(f"  {message}")
    print("  " + "─" * 74)
    await asyncio.sleep(wait_time)  # Short pause to show the message

async def modify_trading_parameters(paper_trader):
    """Allow users to modify trading parameters"""
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("MODIFY TRADING PARAMETERS", width=76)
    
    print("""
  Update your trading parameters. Press Enter to keep current values.
    """)
    
    # Get current parameters
    params = paper_trader.get_trading_parameters()
    
    # Position size
    print("\n" + "─" * 76)
    print("POSITION SIZING".center(76))
    print("─" * 76)
    position_size = display_input_field(f"Position Size (% of portfolio per trade, current: {params['position_size']}%)", width=70)
    if position_size:
        params['position_size'] = parse_float(position_size, params['position_size'])
    
    # Risk management
    print("\n" + "─" * 76)
    print("RISK MANAGEMENT".center(76))
    print("─" * 76)
    
    initial_sl = display_input_field(f"Initial Stop Loss (%, current: {params['initial_sl']}%)", width=70)
    if initial_sl:
        params['initial_sl'] = parse_float(initial_sl, params['initial_sl'])
    
    trail_percent = display_input_field(f"Trailing Stop (%, current: {params['trail_percent']}%)", width=70)
    if trail_percent:
        params['trail_percent'] = parse_float(trail_percent, params['trail_percent'])
    
    take_profit = display_input_field(f"Take Profit Levels (comma-separated %, current: {params['take_profit_levels']})", width=70)
    if take_profit:
        params['take_profit_levels'] = take_profit
        
    # Save parameters
    paper_trader.update_trading_parameters(params)
    
    display_notification("Trading parameters updated successfully", "success")
    await asyncio.sleep(1.5)  # Short pause to show the message

async def view_trade_history(paper_trader):
    """Display trade history in a paginated view"""
    page = 0
    page_size = 10
    
    while True:
        clear_screen()
        display_stratos_logo()
        
        # Get trade history with pagination
        history = paper_trader.get_trade_history(limit=page_size, offset=page*page_size)
        total_pages = (history['total'] + page_size - 1) // page_size
        
        display_premium_frame(f"TRADE HISTORY (Page {page+1}/{max(1, total_pages)})", width=76)
        
        if not history['trades']:
            print("\n  No trade history found.")
        else:
            # Header
            print(f"\n  {'Type':<6} {'Symbol':<8} {'Entry':<10} {'Exit':<10} {'Amount':<10} {'P/L':<10} {'Date':<16}")
            print("  " + "-" * 70)
            
            # List trades
            for trade in history['trades']:
                trade_type = trade.get('type', 'buy').upper()
                symbol = trade.get('token_name', '')[:8]
                entry_price = trade.get('entry_price', 0)
                exit_price = trade.get('exit_price', 0)
                amount = trade.get('amount', 0)
                
                # Calculate P/L
                pnl = "N/A"
                if 'realized_pnl' in trade:
                    pnl = f"{trade['pnl_percentage']:.2f}%"
                    if trade['realized_pnl'] > 0:
                        pnl = "+" + pnl
                
                # Format date
                date = "N/A"
                if 'entry_time' in trade:
                    entry_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(trade['entry_time']))
                    date = entry_date
                
                print(f"  {trade_type:<6} {symbol:<8} ${entry_price:<9.6f} ${exit_price:<9.6f} " + 
                      f"{amount:<10.2f} {pnl:<10} {date:<16}")
        
        # Pagination controls
        print("\n" + "─" * 76)
        print("NAVIGATION".center(76))
        print("─" * 76 + "\n")
        
        print("  [P] Previous Page    [N] Next Page    [Q] Back to Dashboard")
        print("\n  Enter command:")
        
        cmd = input("  ⮞ ").lower().strip()
        
        if cmd == 'p' and page > 0:
            page -= 1
        elif cmd == 'n' and page < total_pages - 1:
            page += 1
        elif cmd == 'q':
            break

async def close_specific_position(paper_trader):
    """Allow user to close a specific position"""
    positions = paper_trader.get_open_positions()
    
    if not positions:
        await display_command_result("No open positions to close.")
        return
    
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("CLOSE SPECIFIC POSITION", width=76)
    
    # List positions
    print(f"\n  {'ID':<4} {'Symbol':<8} {'Entry':<10} {'Current':<10} {'Amount':<12} {'Value':<10} {'P/L %':<8}")
    print("  " + "-" * 70)
    
    for i, pos in enumerate(positions, 1):
        pnl_str = f"{pos['pnl_percentage']:.2f}%"
        if pos['pnl_percentage'] > 0:
            pnl_str = "+" + pnl_str
            
        print(f"  {i:<4} {pos['symbol']:<8} ${pos['entry_price']:<9.6f} ${pos['current_price']:<9.6f} " + 
              f"{pos['amount']:<12.4f} ${pos['value_usd']:<9.2f} {pnl_str:<8}")
    
    # Get position ID to close
    print("\n  Enter position ID to close (or 'Q' to cancel):")
    pos_id = input("  ⮞ ").strip()
    
    if pos_id.lower() == 'q':
        return
    
    try:
        pos_idx = int(pos_id) - 1
        if 0 <= pos_idx < len(positions):
            # Confirm closure
            symbol = positions[pos_idx]['symbol']
            confirm = input(f"  ⚠️ Confirm closing position for {symbol} (y/n): ").lower()
            
            if confirm == 'y':
                result = await paper_trader.close_paper_position(symbol, 'manual_close')
                if result['success']:
                    await display_command_result(f"✅ Position for {symbol} closed successfully.")
                else:
                    await display_command_result(f"❌ Failed to close position: {result['error']}")
            else:
                await display_command_result("Operation cancelled.")
        else:
            await display_command_result("Invalid position ID.")
    except (ValueError, IndexError):
        await display_command_result("Invalid input. Please enter a valid position ID.")

async def view_signal_log(paper_trader):
    """Display recent trading signals"""
    # This would need to be implemented based on your signal logging system
    # For now, just show a placeholder
    
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("SIGNAL LOG", width=76)
    
    print("""
  Signal log functionality will show recent signals detected from Telegram channels.
  This feature is planned for a future update.
    """)
    
    print("\n  Press any key to return to dashboard...")
    input("  ⮞ ")


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
    # Create Config instance first to check for existing settings
    config = Config()
    
    # Show logo and welcome message
    clear_screen()
    display_stratos_logo()
    
    # Check if we have saved credentials
    has_saved_settings = config.has_credentials()
    
    # Display main menu
    display_premium_frame("STRATOS TRADING BOT", width=76)
    
    print("""
  Welcome to Stratos Trading Bot!
  
  Please select an option to continue:
    """)
    
    print("\n" + "─" * 76)
    
    # Build menu options based on whether we have saved settings
    menu_options = []
    
    if has_saved_settings:
        menu_options.append(("Start Bot with Saved Settings", "continue"))
    
    menu_options.extend([
        ("Configure New Settings", "configure"),
        ("Edit Settings File Directly", "edit_env"),
        ("Exit", "exit")
    ])
    
    # Display menu options
    for i, (option_text, _) in enumerate(menu_options, 1):
        display_button(f"{i}. {option_text}", selected=(i == 1), width=70)
        print()
    
    print("\n" + "─" * 76)
    print("  Enter your choice (1-" + str(len(menu_options)) + "):")
    
    try:
        choice = int(input("  ⮞ ").strip())
        if choice < 1 or choice > len(menu_options):
            raise ValueError("Invalid choice")
        selected_action = menu_options[choice-1][1]
    except ValueError:
        display_notification("Invalid choice. Exiting...", "error")
        return
    
    # Handle the selected action
    if selected_action == "exit":
        clear_screen()
        display_notification("Exiting Stratos Trading Bot. Goodbye!", "info")
        return
    elif selected_action == "edit_env":
        # Open the .env file in the default text editor
        from utils import open_env_file
        
        clear_screen()
        display_stratos_logo()
        display_premium_frame("EDIT SETTINGS FILE", width=76)
        
        print("""
  Opening the settings file in your default text editor.
  
  You can directly edit the configuration values in this file.
  Save the file when you're done, then restart the bot.
        """)
        
        success = open_env_file()
        
        if success:
            print("\n  Settings file opened successfully. Press Enter to exit.")
        else:
            print("\n  Error opening settings file. Press Enter to exit.")
            
        input("\n  ⮞ ")
        return
    elif selected_action == "continue":
        # Always ask for trading mode, even with saved settings
        trading_mode = display_trade_mode_selection()
        is_paper_trading = (trading_mode == 1)
        
        # Update the config with the selected mode
        config.paper_trading_mode = is_paper_trading
        
        # For live trading, we MUST verify wallet info
        if not is_paper_trading:
            # Check if we have a saved wallet address
            has_wallet = bool(getattr(config, 'wallet_address', None))
            
            # Always get wallet information for live trading
            wallet_info = get_wallet_private_key()
            
            if not wallet_info or not wallet_info['private_key']:
                clear_screen()
                display_notification("Wallet information is required for live trading. Setup cancelled.", "error")
                return
                
            # Update wallet info
            config.wallet_address = wallet_info['wallet_address']
            config.private_key = wallet_info['private_key']
            
            # Save the updated config
            config.save()
            display_notification("Live trading settings updated successfully", "success")
        
        # Initialize paper trader if in paper trading mode
        paper_trader = None
        if is_paper_trading:
            paper_trader = PaperTrader(config)
            
        # Initialize system
        await system_initialization(is_paper_trading)
        
        # In paper trading mode, show the dashboard
        if is_paper_trading:
            # Create and start the bot (for signal monitoring)
            bot = TelegramCopyTrader(config)
            
            # Start bot in background task
            bot_task = asyncio.create_task(bot.start())
            
            # Show dashboard (this will block until user exits)
            await display_paper_trading_dashboard(paper_trader)
            
            # When dashboard is closed, stop the bot
            if bot.running:
                await bot.stop()
        else:
            # Create and start the bot in live trading mode
            bot = TelegramCopyTrader(config)
            await bot.start()
            
        return
    
    # If we get here, user selected "configure" or we have no saved settings
    
    # Show disclaimer first
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
    
    # Get Telegram API credentials - use existing values as defaults if available
    clear_screen()
    display_stratos_logo()
    
    display_premium_frame("TELEGRAM API CONFIGURATION", width=76)
    
    print("""
  Stratos needs your Telegram API credentials to monitor signal channels.
  You can get these from https://my.telegram.org/apps
    """)
    
    # Show existing values as defaults if available
    default_api_id = str(config.api_id) if config.api_id else ""
    default_api_hash = config.api_hash or ""
    default_phone = config.phone or ""
    
    api_id_prompt = f"Telegram API ID (default: {default_api_id})" if default_api_id else "Telegram API ID"
    api_hash_prompt = f"Telegram API Hash (default: {default_api_hash})" if default_api_hash else "Telegram API Hash"
    phone_prompt = f"Phone Number (with country code) (default: {default_phone})" if default_phone else "Phone Number (with country code)"
    
    api_id_input = display_input_field(api_id_prompt, width=70)
    api_hash_input = display_input_field(api_hash_prompt, width=70)
    phone_input = display_input_field(phone_prompt, width=70)
    
    # Use input values or defaults
    api_id = api_id_input or default_api_id
    api_hash = api_hash_input or default_api_hash
    phone = phone_input or default_phone
    
    if not api_id or not api_hash or not phone:
        clear_screen()
        display_notification("Telegram API credentials are required. Setup cancelled.", "error")
        return
    
    # Configure trading parameters (both modes need this)
    trading_params = await configure_trading_parameters()
    
    # Update config with new values
    try:
        config.api_id = int(api_id)
    except ValueError:
        display_notification("API ID must be a number. Setup cancelled.", "error")
        return
    
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
    
    # Save configuration (to both config.json and .env)
    config.save()
    display_notification("Configuration saved successfully. Settings will be remembered for next time.", "success")
    
    # Initialize paper trader if in paper trading mode
    paper_trader = None
    if is_paper_trading:
        paper_trader = PaperTrader(config)
        
        # Reset paper trading data if requested
        if paper_trading_config and paper_trading_config.get('reset_existing'):
            paper_trader.reset_account(paper_trading_config['initial_balance'])
    
    # Initialize system
    await system_initialization(is_paper_trading)
    
    # In paper trading mode, show the dashboard
    if is_paper_trading:
        # Create and start the bot (for signal monitoring)
        bot = TelegramCopyTrader(config)
        
        # Start bot in background task
        bot_task = asyncio.create_task(bot.start())
        
        # Show dashboard (this will block until user exits)
        await display_paper_trading_dashboard(paper_trader)
        
        # When dashboard is closed, stop the bot
        if bot.running:
            await bot.stop()
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