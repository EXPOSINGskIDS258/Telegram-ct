"""
Telegram monitoring module for the Stratos Trading Bot

This file handles Telegram client operations and trading signal detection.
"""

import asyncio
import logging
import re
import time
import traceback
from telethon import TelegramClient, events
from signal_handler import Signal, SignalParser
from trader import Trader
from paper_trader import PaperTrader  # Import PaperTrader

logger = logging.getLogger(__name__)

class TelegramCopyTrader:
    """
    Signal detection and trading module
    
    Instead of just copying messages, this class now detects signals
    and executes trades based on them.
    """
    def __init__(self, config):
        self.config = config
        self.session_name = config.session_name if hasattr(config, 'session_name') else 'stratos_session'
        self.client = TelegramClient(self.session_name, config.api_id, config.api_hash)
        
        # Initialize appropriate trader based on mode
        self.is_paper_trading = getattr(config, 'paper_trading_mode', False)
        
        # Safety check for live trading
        if not self.is_paper_trading and not getattr(config, 'private_key', None):
            logger.error("Attempted to initialize LIVE trading without a private key!")
            raise ValueError("Private key is required for live trading but was not provided!")
            
        if self.is_paper_trading:
            logger.info("Initializing in PAPER TRADING mode")
            self.trader = None  # Not needed for paper trading
            self.paper_trader = PaperTrader(config)
            logger.info(f"Paper trader initialized: {self.paper_trader is not None}")
        else:
            # Safety check already performed above
            logger.info("Initializing in LIVE TRADING mode")
            self.trader = Trader(config)
            self.paper_trader = None
            logger.info(f"Live trader initialized: {self.trader is not None}")
            
        self.running = False
        self.processed_signals = set()
        
    async def send_admin_message(self, message):
        """Send a notification to the admin (user)"""
        try:
            # Send message to the user's "Saved Messages" chat
            await self.client.send_message('me', message)
            return True
        except Exception as e:
            logger.error(f"Failed to send admin message: {str(e)}")
            return False
        
    async def start(self):
        """Start the bot"""
        if self.running:
            logger.warning("Bot is already running")
            return
            
        # Validate configuration
        if not self.config.api_id or not self.config.api_hash:
            logger.error("API credentials not configured")
            raise ValueError("API credentials missing in configuration")
            
        if not self.config.source_channels:
            logger.error("No source channels configured")
            raise ValueError("Source channels missing in configuration")
            
        # Double-check for live trading requirements
        if not self.is_paper_trading and not self.config.private_key:
            logger.error("Cannot start live trading without private key")
            raise ValueError("Private key is required for live trading")
        
        try:
            # Start the client
            await self.client.start(phone=self.config.phone)
            logger.info("Telegram client started")
            self.running = True
            
            # Initialize appropriate trader
            if self.is_paper_trading:
                # Paper trading doesn't need trader initialization
                logger.info("Running in paper trading mode")
                if self.paper_trader is None:
                    logger.error("Paper trader is not initialized - recreating it")
                    self.paper_trader = PaperTrader(self.config)
            else:
                # Initialize live trader
                logger.info("Running in live trading mode")
                await self.trader.initialize()
            
            # Send startup notification
            trading_mode = "PAPER TRADING" if self.is_paper_trading else "LIVE TRADING"
            await self.send_admin_message(
                f"🚀 **STRATOS TRADING BOT ACTIVATED** 🚀\n\n"
                f"System is now monitoring channels for trading signals.\n\n"
                f"Mode: {trading_mode}\n"
                f"Exchange: {self.config.dex_name if hasattr(self.config, 'dex_name') else 'Unknown'}\n"
                f"Position size: {self.config.position_size_percent}% of portfolio\n"
                f"Initial SL: {self.config.initial_sl_percent}%\n"
                f"Trailing stop: {self.config.trail_percent}%\n"
            )
            
            # Register event handler for new messages
            @self.client.on(events.NewMessage(chats=self.config.source_channels))
            async def handle_new_message(event):
                await self.process_message(event)
                
            # Keep the bot running
            logger.info("Bot is now running and monitoring channels")
            logger.info(f"Monitoring channels: {self.config.source_channels}")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            self.running = False
            raise
            
    async def stop(self):
        """Stop the bot"""
        if not self.running:
            logger.warning("Bot is not running")
            return
            
        try:
            # Close trader connections if in live mode
            if not self.is_paper_trading and self.trader:
                await self.trader.close()
            
            # Disconnect Telegram client
            await self.client.disconnect()
            self.running = False
            logger.info("Bot stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
        
    async def process_message(self, event):
        """Process incoming messages for trading signals"""
        try:
            # Get message content
            message_text = event.message.text if event.message.text else ''
            source_channel = event.chat_id
            
            # Skip empty messages
            if not message_text.strip():
                return
                
            logger.info(f"Received message from {source_channel}: {message_text[:100]}...")
            
            # Preliminary check if this is likely a signal message
            if not SignalParser.is_signal_message(message_text):
                logger.debug("Message doesn't appear to be a trading signal")
                return
                
            # Try to extract token address
            token_address = SignalParser.extract_token_address(message_text)
            
            if not token_address:
                logger.debug("No token address found in message")
                return
                
            logger.info(f"Detected potential trading signal for token: {token_address}")
            
            # Generate signal ID to prevent duplicates
            signal_id = f"{token_address}_{int(time.time())}"
            
            # Check if we've already processed this signal
            if signal_id in self.processed_signals:
                logger.info(f"Skipping duplicate signal: {signal_id}")
                return
                
            # Mark as processed to avoid duplicates
            self.processed_signals.add(signal_id)
            if len(self.processed_signals) > 1000:  # Limit the size
                self.processed_signals = set(list(self.processed_signals)[-500:])
                
            # Parse trade parameters from message
            trade_params = SignalParser.extract_trade_parameters(message_text)
            logger.info(f"Parsed trade parameters: {trade_params}")
            
            # Send notification about detected signal
            chat_title = event.chat.title if hasattr(event.chat, 'title') else 'Unknown'
            await self.send_admin_message(
                f"🔍 **SIGNAL DETECTED**\n\n"
                f"Token: `{token_address}`\n"
                f"Source: {chat_title}\n"
                f"Position size: {trade_params.get('position_size', self.config.position_size_percent)}%\n"
                f"Stop loss: {trade_params.get('stop_loss', self.config.initial_sl_percent)}%\n\n"
                f"Executing trade in {'PAPER mode' if self.is_paper_trading else 'LIVE mode'}..."
            )
            
            # Execute the trade based on trading mode
            if self.is_paper_trading:
                # Check if paper trader is properly initialized
                if self.paper_trader is None:
                    logger.error("Paper trader is None - cannot execute trade!")
                    await self.send_admin_message("❌ **PAPER TRADING ERROR**: Trading module not initialized properly.")
                    return
                
                # Execute paper trade
                logger.info(f"Executing paper trade for token: {token_address}")
                try:
                    trade_result = await self.paper_trader.execute_paper_trade(token_address, trade_params)
                    logger.info(f"Paper trade execution result: {trade_result}")
                except Exception as e:
                    logger.error(f"Error executing paper trade: {str(e)}")
                    logger.error(traceback.format_exc())  # Log full stack trace
                    trade_result = {'success': False, 'error': str(e)}
            else:
                # Execute live trade
                logger.info(f"Executing live trade for token: {token_address}")
                trade_result = await self.trader.execute_trade(token_address, trade_params)
            
            # Send trade result notification
            if trade_result['success']:
                await self.send_admin_message(
                    f"✅ **TRADE EXECUTED {'(PAPER)' if self.is_paper_trading else ''}**\n\n"
                    f"Token: `{token_address}`\n"
                    f"Token Name: {trade_result.get('token_name', 'Unknown')}\n"
                    f"Amount: {trade_result.get('amount', 0)}\n"
                    f"Entry price: {trade_result.get('price', 0)}\n"
                    f"Value: ${trade_result.get('value_usd', 0):.2f}\n"
                    f"Transaction ID: `{trade_result.get('tx_id', trade_result.get('trade_id', 'N/A'))[:10]}...`\n\n"
                    f"Stop loss set at: {trade_result.get('stop_loss_price', 0)}\n"
                    f"Take profit levels: {', '.join([f'{level}%' for level in trade_result.get('take_profit_levels', [])])}"
                )
                
                # Start monitoring trade for stop loss and take profit (for live trading)
                if not self.is_paper_trading and self.trader:
                    asyncio.create_task(self.trader.monitor_trade(trade_result['trade_id']))
            else:
                await self.send_admin_message(
                    f"❌ **TRADE FAILED {'(PAPER)' if self.is_paper_trading else ''}**\n\n"
                    f"Token: `{token_address}`\n"
                    f"Error: {trade_result['error']}\n\n"
                    f"Please check your {'paper trading settings' if self.is_paper_trading else 'exchange connection and wallet balance'}."
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(traceback.format_exc())  # Log full stack trace
            await self.send_admin_message(f"⚠️ Error processing signal: {str(e)}")