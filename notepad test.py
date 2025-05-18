print("Testing Stratos Bot")

try:
    from config import Config
    print("Config module loaded successfully")
    
    from telegram_client import TelegramCopyTrader
    print("TelegramCopyTrader module loaded successfully")
    
    config = Config()
    print("Config instance created")
    
    print("All modules loaded. Starting simple UI test:")
    
    # Simple UI test
    print("\n" + "="*30)
    print("STRATOS TRADING BOT")
    print("="*30)
    
    choice = input("\nEnter Y to continue: ")
    print(f"You entered: {choice}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("Test completed")