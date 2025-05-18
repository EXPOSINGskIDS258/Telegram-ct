"""
Price tracking and stop-loss management module for the Copy Trading Bot
"""

import asyncio
import aiohttp
import time
import logging
import random  # For mock price data - remove in production

logger = logging.getLogger(__name__)

class PriceTracker:
    """Tracks token prices for trailing stop-loss functionality"""
    def __init__(self, telegram_client, config):
        self.telegram_client = telegram_client
        self.config = config
        self.tracking_signals = {}  # token_address -> tracking_info
        
    async def start_tracking(self, token_address, initial_price=None):
        """Start tracking a token's price for trailing stop-loss"""
        if token_address in self.tracking_signals:
            logger.info(f"Already tracking {token_address}")
            return True
            
        if not initial_price:
            initial_price = await self.get_current_price(token_address)
            
        if not initial_price:
            logger.error(f"Failed to get initial price for {token_address}")
            return False
            
        # Calculate initial stop-loss level
        initial_sl_level = initial_price * (1 - self.config.initial_sl_percent / 100)
        
        # Store tracking info
        self.tracking_signals[token_address] = {
            'entry_price': initial_price,
            'current_price': initial_price,
            'highest_price': initial_price,
            'initial_sl_level': initial_sl_level,
            'current_sl_level': initial_sl_level,
            'sl_triggered': False,
            'start_time': time.time()
        }
        
        # Start background task to monitor price
        asyncio.create_task(self.monitor_price(token_address))
        
        logger.info(f"Started tracking {token_address} with initial price {initial_price}")
        
        # Send initial tracking notification
        await self.notify_tracking_started(token_address, initial_price, initial_sl_level)
        
        return True
        
    async def monitor_price(self, token_address):
        """Continuously monitor token price and adjust stop-loss"""
        check_interval = self.config.price_check_interval if hasattr(self.config, 'price_check_interval') else 15
        
        while token_address in self.tracking_signals and not self.tracking_signals[token_address]['sl_triggered']:
            try:
                # Update current price
                current_price = await self.get_current_price(token_address)
                if not current_price:
                    await asyncio.sleep(30)  # Wait before retrying
                    continue
                    
                tracking_info = self.tracking_signals[token_address]
                tracking_info['current_price'] = current_price
                
                # Check if we have a new highest price
                if current_price > tracking_info['highest_price']:
                    tracking_info['highest_price'] = current_price
                    
                    # Adjust trailing stop-loss level
                    new_sl_level = current_price * (1 - self.config.trail_percent / 100)
                    
                    # Only move stop-loss up, never down
                    if new_sl_level > tracking_info['current_sl_level']:
                        tracking_info['current_sl_level'] = new_sl_level
                        logger.info(f"Adjusted trailing SL for {token_address}: {new_sl_level}")
                        
                        # Notify about the adjusted SL
                        await self.notify_sl_adjustment(token_address, new_sl_level)
                
                # Check if stop-loss is triggered
                if current_price <= tracking_info['current_sl_level']:
                    tracking_info['sl_triggered'] = True
                    logger.info(f"Stop-loss triggered for {token_address} at price {current_price}")
                    
                    # Notify about triggered SL
                    await self.notify_sl_triggered(token_address, current_price)
                    
                # Sleep before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in price monitoring for {token_address}: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def get_current_price(self, token_address):
        """
        Get current price of token from an API
        
        IMPORTANT: This method should be customized to use your preferred price API.
        The example below uses a simulated price for testing purposes.
        Replace with your actual API integration code for production.
        """
        try:
            # OPTION 1: PancakeSwap API for BSC tokens
            if hasattr(self.config, 'price_api_type') and self.config.price_api_type == 'pancakeswap':
                return await self._get_pancakeswap_price(token_address)
                
            # OPTION 2: CoinGecko API
            elif hasattr(self.config, 'price_api_type') and self.config.price_api_type == 'coingecko':
                return await self._get_coingecko_price(token_address)
                
            # OPTION 3: Custom API endpoint
            elif hasattr(self.config, 'price_api_url') and self.config.price_api_url:
                return await self._get_custom_api_price(token_address)
                
            # Fallback: Simulated price (for testing only)
            return await self._get_simulated_price(token_address)
            
        except Exception as e:
            logger.error(f"Error getting price for {token_address}: {str(e)}")
            return None
    
    async def _get_pancakeswap_price(self, token_address):
        """Get price from PancakeSwap API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.pancakeswap.info/api/v2/tokens/{token_address}"
                headers = {'accept': 'application/json'}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data.get('data', {}).get('price', 0))
                        return price
                    else:
                        logger.warning(f"PancakeSwap API returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"PancakeSwap API error: {str(e)}")
            return None
    
    async def _get_coingecko_price(self, token_address):
        """Get price from CoinGecko API"""
        try:
            # You'll need to map token addresses to CoinGecko IDs
            # This is a simplistic implementation
            async with aiohttp.ClientSession() as session:
                # First, try to get CoinGecko ID from contract address
                platform = "ethereum"  # Change as needed (ethereum, binance-smart-chain, etc.)
                url = f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{token_address}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        coin_id = data.get('id')
                        price = data.get('market_data', {}).get('current_price', {}).get('usd', 0)
                        return float(price)
                    else:
                        logger.warning(f"CoinGecko API returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"CoinGecko API error: {str(e)}")
            return None
    
    async def _get_custom_api_price(self, token_address):
        """Get price from custom API endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                url = self.config.price_api_url.replace("{token}", token_address)
                headers = {}
                
                if hasattr(self.config, 'price_api_key') and self.config.price_api_key:
                    headers['Authorization'] = f"Bearer {self.config.price_api_key}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract price according to your API's response format
                        # This is just an example - adjust according to your API
                        price = float(data.get('price', 0))
                        return price
                    else:
                        logger.warning(f"Custom API returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Custom API error: {str(e)}")
            return None
    
    async def _get_simulated_price(self, token_address):
        """
        Get simulated price for testing purposes
        REMOVE THIS IN PRODUCTION
        """
        tracking_info = self.tracking_signals.get(token_address)
        if not tracking_info:
            # Initial price for new tokens
            return 0.0001  # Default starting price
            
        # Simulate price movement (up 70% of the time, down 30% of the time)
        # More realistic simulation with small movements
        if random.random() < 0.7:  # 70% chance of price increase
            change = random.uniform(0.001, 0.05)  # 0.1% to 5% increase
        else:
            change = random.uniform(-0.03, -0.001)  # 0.1% to 3% decrease
            
        new_price = tracking_info['current_price'] * (1 + change)
        return new_price
    
    async def notify_tracking_started(self, token_address, price, sl_level):
        """Notify when price tracking starts"""
        message = (
            f"🔍 TRACKING NEW TOKEN 🔍\n\n"
            f"Token: {token_address}\n"
            f"Entry Price: {price:.10f}\n"
            f"Initial Stop-Loss: {sl_level:.10f}\n"
            f"SL Distance: -{self.config.initial_sl_percent}%\n"
            f"Trailing Stop: {self.config.trail_percent}%"
        )
        
        await self.telegram_client.send_message(self.config.destination_channel, message)
        
    async def notify_sl_adjustment(self, token_address, new_sl_level):
        """Notify about stop-loss adjustment"""
        tracking_info = self.tracking_signals.get(token_address)
        if not tracking_info:
            return
            
        message = (
            f"🔄 TRAILING STOP-LOSS UPDATE 🔄\n\n"
            f"Token: {token_address}\n"
            f"New Stop-Loss: {new_sl_level:.10f}\n"
            f"Current Price: {tracking_info['current_price']:.10f}\n"
            f"Highest Price: {tracking_info['highest_price']:.10f}\n"
            f"Price Change: {((tracking_info['current_price'] / tracking_info['entry_price']) - 1) * 100:.2f}%"
        )
        
        await self.telegram_client.send_message(self.config.destination_channel, message)
        
    async def notify_sl_triggered(self, token_address, price):
        """Notify when stop-loss is triggered"""
        tracking_info = self.tracking_signals.get(token_address)
        if not tracking_info:
            return
            
        profit_loss = ((price / tracking_info['entry_price']) - 1) * 100
        time_held = time.time() - tracking_info['start_time']
        hours = time_held // 3600
        minutes = (time_held % 3600) // 60
        seconds = time_held % 60
        
        message = (
            f"⚠️ STOP-LOSS TRIGGERED ⚠️\n\n"
            f"Token: {token_address}\n"
            f"Exit Price: {price:.10f}\n"
            f"Entry Price: {tracking_info['entry_price']:.10f}\n"
            f"P/L: {profit_loss:.2f}%\n"
            f"Highest Price Reached: {tracking_info['highest_price']:.10f}\n"
            f"Max P/L: {((tracking_info['highest_price'] / tracking_info['entry_price']) - 1) * 100:.2f}%\n"
            f"Time Held: {int(hours)}h {int(minutes)}m {int(seconds)}s"
        )
        
        await self.telegram_client.send_message(self.config.destination_channel, message)