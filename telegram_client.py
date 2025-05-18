"""
Telegram monitoring module for the Stratos Trading Bot

This file handles Telegram client operations and trading signal detection.
"""

import asyncio
import logging
import re
import time
from telethon import TelegramClient, events
from signal_handler import Signal, SignalParser
from trader import Trader

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
        self.trader = Trader(config)
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
        
        try:
            # Start the client
            await self.client.start(phone=self.config.phone)
            logger.info("Telegram client started")
            self.running = True
            
            # Initialize trader
            await self.trader.initialize()
            
            # Send startup notification
            await self.send_admin_message(
                "🚀 **STRATOS TRADING BOT ACTIVATED** 🚀\n\n"
                "System is now monitoring channels for trading signals.\n\n"
                f"Exchange: {self.config.exchange_name}\n"
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
            # Close trader connections
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
                
            logger.debug(f"Received message from {source_channel}: {message_text[:50]}...")
            
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
            
            # Send notification about detected signal
            await self.send_admin_message(
                f"🔍 **SIGNAL DETECTED**\n\n"
                f"Token: `{token_address}`\n"
                f"Source: {event.chat.title if hasattr(event.chat, 'title') else 'Unknown'}\n"
                f"Position size: {trade_params.get('position_size', self.config.position_size_percent)}%\n"
                f"Stop loss: {trade_params.get('stop_loss', self.config.initial_sl_percent)}%\n\n"
                f"Executing trade..."
            )
            
            # Execute the trade
            trade_result = await self.trader.execute_trade(token_address, trade_params)
            
            # Send trade result notification
            if trade_result['success']:
                await self.send_admin_message(
                    f"✅ **TRADE EXECUTED**\n\n"
                    f"Token: `{token_address}`\n"
                    f"Amount: {trade_result['amount']}\n"
                    f"Entry price: {trade_result['price']}\n"
                    f"Transaction ID: `{trade_result['tx_id'][:10]}...`\n\n"
                    f"Stop loss set at: {trade_result['stop_loss_price']}\n"
                    f"Take profit levels: {', '.join([f'{level}%' for level in trade_result['take_profit_levels']])}"
                )
                
                # Start monitoring trade for stop loss and take profit
                asyncio.create_task(self.trader.monitor_trade(trade_result['trade_id']))
            else:
                await self.send_admin_message(
                    f"❌ **TRADE FAILED**\n\n"
                    f"Token: `{token_address}`\n"
                    f"Error: {trade_result['error']}\n\n"
                    f"Please check your exchange connection and wallet balance."
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_admin_message(f"⚠️ Error processing signal: {str(e)}")
