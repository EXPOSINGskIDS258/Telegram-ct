"""
Paper trading module for Stratos Trading Bot
Allows users to simulate trades without risking real funds
"""

import json
import os
import time
import logging
import random
from decimal import Decimal
import uuid
import traceback

logger = logging.getLogger(__name__)

class PaperTrader:
    """
    Paper trading system for simulating trades without using real funds
    Tracks virtual balance, positions, and trading history
    """
    
    def __init__(self, config):
        self.config = config
        self.paper_trading_file = 'paper_trading.json'
        self.virtual_balance = 10000.0  # Default starting balance in USD
        self.positions = {}  # Current open positions
        self.trade_history = []  # History of all paper trades
        self.started_at = time.time()
        
        # Trading parameters
        self.trading_parameters = {
            'position_size': getattr(self.config, 'position_size_percent', 3.0),
            'initial_sl': getattr(self.config, 'initial_sl_percent', 30.0),
            'trail_percent': getattr(self.config, 'trail_percent', 5.0),
            'take_profit_levels': getattr(self.config, 'take_profit_levels', "20,40,100"),
            'max_slippage': getattr(self.config, 'max_slippage', 15.0)
        }
        
        # Bot state
        self.paused = False
        self.auto_execution = True
        
        # Load existing paper trading data if available
        self._load_data()
        
        logger.info(f"PaperTrader initialized with balance: ${self.virtual_balance:.2f}")
    
    def _load_data(self):
        """Load paper trading data from file"""
        if os.path.exists(self.paper_trading_file):
            try:
                with open(self.paper_trading_file, 'r') as f:
                    data = json.load(f)
                    self.virtual_balance = data.get('virtual_balance', self.virtual_balance)
                    self.positions = data.get('positions', {})
                    self.trade_history = data.get('trade_history', [])
                    self.started_at = data.get('started_at', time.time())
                    self.trading_parameters = data.get('trading_parameters', self.trading_parameters)
                    self.paused = data.get('paused', False)
                    self.auto_execution = data.get('auto_execution', True)
                logger.info(f"Loaded paper trading data - Balance: ${self.virtual_balance:.2f}")
            except Exception as e:
                logger.error(f"Error loading paper trading data: {str(e)}")
    
    def _save_data(self):
        """Save paper trading data to file"""
        try:
            data = {
                'virtual_balance': self.virtual_balance,
                'positions': self.positions,
                'trade_history': self.trade_history,
                'started_at': self.started_at,
                'trading_parameters': self.trading_parameters,
                'paused': self.paused,
                'auto_execution': self.auto_execution
            }
            with open(self.paper_trading_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved paper trading data - Balance: ${self.virtual_balance:.2f}")
        except Exception as e:
            logger.error(f"Error saving paper trading data: {str(e)}")
    
    def reset_account(self, initial_balance=10000.0):
        """Reset paper trading account to initial state"""
        self.virtual_balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.started_at = time.time()
        self._save_data()
        logger.info(f"Paper trading account reset with ${initial_balance:.2f}")
        return True
    
    def reset_stats(self):
        """Reset trading statistics while keeping current positions and balance"""
        # Keep positions and balance but reset history and start time
        self.trade_history = []
        self.started_at = time.time()
        self._save_data()
        logger.info("Paper trading statistics reset")
        return True
    
    def get_account_summary(self):
        """Get summary of paper trading account"""
        # Calculate total value (balance + open positions)
        open_positions_value = 0
        for symbol, position in self.positions.items():
            current_price = self._get_current_price(position['token_address'])
            position_value = position['amount'] * current_price
            open_positions_value += position_value
        
        total_value = self.virtual_balance + open_positions_value
        
        # Calculate performance metrics
        profit_loss = 0
        if self.trade_history:
            profit_loss = sum(trade['realized_pnl'] for trade in self.trade_history if 'realized_pnl' in trade)
        
        win_trades = len([t for t in self.trade_history if t.get('realized_pnl', 0) > 0])
        loss_trades = len([t for t in self.trade_history if t.get('realized_pnl', 0) < 0])
        total_trades = len(self.trade_history)
        win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate time-based metrics
        days_running = (time.time() - self.started_at) / (60 * 60 * 24)
        
        return {
            'virtual_balance': self.virtual_balance,
            'open_positions_value': open_positions_value,
            'total_value': total_value,
            'total_profit_loss': profit_loss,
            'win_trades': win_trades,
            'loss_trades': loss_trades,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'days_running': days_running,
            'open_positions': len(self.positions)
        }
    
    async def execute_paper_trade(self, token_address, trade_params):
        """
        Execute a paper trade based on the detected signal
        
        Args:
            token_address: The address of the token to trade
            trade_params: Dictionary of trading parameters
            
        Returns:
            Dict with paper trade result information
        """
        logger.info(f"PaperTrader.execute_paper_trade called for token: {token_address}")
        logger.info(f"Trade params: {trade_params}")
        logger.info(f"Bot state - paused: {self.paused}, auto_execution: {self.auto_execution}")
        
        # Check if bot is paused
        if self.paused:
            logger.info(f"Signal for {token_address} ignored: bot is paused")
            return {
                'success': False,
                'error': 'Bot is paused. Enable auto-trading to execute this signal.'
            }
            
        # Check if auto-execution is enabled
        if not self.auto_execution:
            logger.info(f"Signal for {token_address} ignored: auto-execution disabled")
            return {
                'success': False,
                'error': 'Auto-execution is disabled. Enable it to automatically execute signals.'
            }
            
        trade_id = str(uuid.uuid4())
        
        try:
            # Extract trade parameters
            position_size = trade_params.get('position_size', self.trading_parameters['position_size'])
            stop_loss = trade_params.get('stop_loss', self.trading_parameters['initial_sl'])
            
            logger.info(f"Using position size: {position_size}%, stop loss: {stop_loss}%")
            
            # Parse take profit levels
            take_profit_levels = [20, 40, 100]  # Default values
            take_profit_str = self.trading_parameters['take_profit_levels']
            if take_profit_str:
                try:
                    take_profit_levels = [float(level) for level in take_profit_str.split(',')]
                    logger.info(f"Using take profit levels: {take_profit_levels}")
                except Exception as e:
                    logger.warning(f"Could not parse take profit levels: {take_profit_str}. Error: {str(e)}")
                    
            # Calculate simulated price and transaction details
            current_price = self._get_current_price(token_address)
            logger.info(f"Current simulated price: {current_price}")
            
            # Calculate position size based on account balance and parameter
            trade_amount_usd = self.virtual_balance * (position_size / 100)
            token_amount = trade_amount_usd / current_price
            
            logger.info(f"Calculated trade amount: ${trade_amount_usd:.2f}, token amount: {token_amount}")
            
            # Simulate slippage
            slippage = min(random.uniform(0.1, self.trading_parameters['max_slippage']), self.trading_parameters['max_slippage']) / 100
            execution_price = current_price * (1 + slippage)
            
            # Simulate fees
            fee_percentage = 0.25  # 0.25% fee
            fee_amount = trade_amount_usd * (fee_percentage / 100)
            
            # Adjust amounts for fees
            actual_trade_amount = trade_amount_usd - fee_amount
            actual_token_amount = actual_trade_amount / execution_price
            
            logger.info(f"After slippage ({slippage*100:.2f}%) and fees (${fee_amount:.2f}):")
            logger.info(f"Execution price: {execution_price}, actual token amount: {actual_token_amount}")
            
            # Check if we have enough balance
            if trade_amount_usd > self.virtual_balance:
                logger.warning(f"Insufficient balance: Required ${trade_amount_usd:.2f}, Available ${self.virtual_balance:.2f}")
                return {
                    'success': False,
                    'error': f"Insufficient virtual balance. Required: ${trade_amount_usd:.2f}, Available: ${self.virtual_balance:.2f}"
                }
            
            # Create paper trade record
            paper_trade = {
                'trade_id': trade_id,
                'token_address': token_address,
                'token_name': self._get_token_name(token_address),
                'entry_time': time.time(),
                'entry_price': execution_price,
                'amount': actual_token_amount,
                'value_usd': actual_trade_amount,
                'fee_usd': fee_amount,
                'stop_loss_price': execution_price * (1 - (stop_loss / 100)),
                'take_profit_levels': take_profit_levels,
                'status': 'open',
                'slippage': slippage * 100,  # Store as percentage
                'type': 'buy'
            }
            
            # Update virtual balance
            self.virtual_balance -= trade_amount_usd
            
            # Add to positions
            symbol = self._get_token_symbol(token_address)
            self.positions[symbol] = paper_trade
            
            # Add to history
            self.trade_history.append(paper_trade.copy())
            
            # Save data
            self._save_data()
            
            # Return trade details
            result = {
                'success': True,
                'trade_id': trade_id,
                'token_address': token_address,
                'token_name': paper_trade['token_name'],
                'price': execution_price,
                'amount': actual_token_amount,
                'value_usd': actual_trade_amount,
                'fee_usd': fee_amount,
                'stop_loss_price': paper_trade['stop_loss_price'],
                'take_profit_levels': take_profit_levels,
                'slippage': slippage * 100
            }
            
            # Start monitoring this position
            # In a real implementation, we would start a background task here
            
            logger.info(f"Paper trade successfully executed: {symbol} for ${actual_trade_amount:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing paper trade: {str(e)}")
            logger.error(traceback.format_exc())  # Log full stack trace for debugging
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_paper_position(self, symbol_or_trade_id, close_reason="manual", current_price=None):
        """Close a paper trading position"""
        try:
            # Find the position
            position = None
            if symbol_or_trade_id in self.positions:
                position = self.positions[symbol_or_trade_id]
                symbol = symbol_or_trade_id
            else:
                # Try to find by trade_id
                for sym, pos in self.positions.items():
                    if pos['trade_id'] == symbol_or_trade_id:
                        position = pos
                        symbol = sym
                        break
            
            if not position:
                logger.warning(f"Position not found: {symbol_or_trade_id}")
                return {
                    'success': False,
                    'error': f"Position not found: {symbol_or_trade_id}"
                }
            
            # Get current price if not provided
            if current_price is None:
                current_price = self._get_current_price(position['token_address'])
            
            # Simulate slippage
            slippage = min(random.uniform(0.1, self.trading_parameters['max_slippage']), self.trading_parameters['max_slippage']) / 100
            execution_price = current_price * (1 - slippage)  # Negative slippage for selling
            
            # Calculate value
            token_amount = position['amount']
            position_value = token_amount * execution_price
            
            # Simulate fees
            fee_percentage = 0.25  # 0.25% fee
            fee_amount = position_value * (fee_percentage / 100)
            
            # Adjust for fees
            actual_position_value = position_value - fee_amount
            
            # Calculate profit/loss
            entry_value = token_amount * position['entry_price']
            realized_pnl = actual_position_value - entry_value
            pnl_percentage = (realized_pnl / entry_value) * 100 if entry_value > 0 else 0
            
            # Create closing trade record
            closing_trade = {
                'trade_id': str(uuid.uuid4()),
                'related_trade_id': position['trade_id'],
                'token_address': position['token_address'],
                'token_name': position['token_name'],
                'exit_time': time.time(),
                'entry_price': position['entry_price'],
                'exit_price': execution_price,
                'amount': token_amount,
                'value_usd': actual_position_value,
                'fee_usd': fee_amount,
                'realized_pnl': realized_pnl,
                'pnl_percentage': pnl_percentage,
                'holding_time': time.time() - position['entry_time'],
                'close_reason': close_reason,
                'status': 'closed',
                'slippage': slippage * 100,  # Store as percentage
                'type': 'sell'
            }
            
            # Update virtual balance
            self.virtual_balance += actual_position_value
            
            # Update position's status in history
            for trade in self.trade_history:
                if trade['trade_id'] == position['trade_id']:
                    trade['status'] = 'closed'
                    trade['exit_price'] = execution_price
                    trade['exit_time'] = time.time()
                    trade['realized_pnl'] = realized_pnl
                    trade['pnl_percentage'] = pnl_percentage
                    trade['close_reason'] = close_reason
                    break
            
            # Add closing trade to history
            self.trade_history.append(closing_trade)
            
            # Remove from open positions
            del self.positions[symbol]
            
            # Save data
            self._save_data()
            
            # Return trade details
            result = {
                'success': True,
                'trade_id': closing_trade['trade_id'],
                'token_address': position['token_address'],
                'token_name': position['token_name'],
                'entry_price': position['entry_price'],
                'exit_price': execution_price,
                'amount': token_amount,
                'value_usd': actual_position_value,
                'fee_usd': fee_amount,
                'realized_pnl': realized_pnl,
                'pnl_percentage': pnl_percentage,
                'close_reason': close_reason
            }
            
            logger.info(f"Paper position closed: {symbol} for ${actual_position_value:.2f} ({pnl_percentage:.2f}% P/L)")
            return result
            
        except Exception as e:
            logger.error(f"Error closing paper position: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_open_positions(self):
        """Get all open paper trading positions"""
        result = []
        for symbol, position in self.positions.items():
            current_price = self._get_current_price(position['token_address'])
            
            # Calculate unrealized P/L
            position_value = position['amount'] * current_price
            entry_value = position['amount'] * position['entry_price']
            unrealized_pnl = position_value - entry_value
            pnl_percentage = (unrealized_pnl / entry_value) * 100 if entry_value > 0 else 0
            
            position_info = {
                'symbol': symbol,
                'trade_id': position['trade_id'],
                'token_address': position['token_address'],
                'token_name': position['token_name'],
                'entry_price': position['entry_price'],
                'current_price': current_price,
                'amount': position['amount'],
                'value_usd': position_value,
                'unrealized_pnl': unrealized_pnl,
                'pnl_percentage': pnl_percentage,
                'entry_time': position['entry_time'],
                'holding_time': time.time() - position['entry_time']
            }
            result.append(position_info)
        
        return result
    
    def get_trade_history(self, limit=50, offset=0):
        """Get paper trading history"""
        # Sort by time, newest first
        sorted_trades = sorted(self.trade_history, key=lambda x: x.get('entry_time', 0), reverse=True)
        
        # Apply pagination
        paginated = sorted_trades[offset:offset+limit] if offset < len(sorted_trades) else []
        
        return {
            'trades': paginated,
            'total': len(sorted_trades),
            'offset': offset,
            'limit': limit
        }
    
    def get_trading_parameters(self):
        """Get current trading parameters"""
        return self.trading_parameters
    
    def update_trading_parameters(self, params):
        """Update trading parameters"""
        for key, value in params.items():
            if key in self.trading_parameters:
                self.trading_parameters[key] = value
        
        # Update config as well for persistence
        if hasattr(self.config, 'position_size_percent'):
            self.config.position_size_percent = self.trading_parameters['position_size']
        if hasattr(self.config, 'initial_sl_percent'):
            self.config.initial_sl_percent = self.trading_parameters['initial_sl']
        if hasattr(self.config, 'trail_percent'):
            self.config.trail_percent = self.trading_parameters['trail_percent']
        if hasattr(self.config, 'take_profit_levels'):
            self.config.take_profit_levels = self.trading_parameters['take_profit_levels']
        if hasattr(self.config, 'max_slippage'):
            self.config.max_slippage = self.trading_parameters['max_slippage']
            
        # Save data
        self._save_data()
        
        logger.info("Trading parameters updated")
        return True
    
    def set_trading_mode(self, paused=None, auto_execution=None):
        """Update trading mode settings"""
        if paused is not None:
            self.paused = paused
        if auto_execution is not None:
            self.auto_execution = auto_execution
            
        # Save data
        self._save_data()
        
        logger.info(f"Trading mode updated: paused={self.paused}, auto_execution={self.auto_execution}")
        return True
    
    def _get_current_price(self, token_address):
        """
        Get simulated current price for a token
        
        This is a simplified simulation for paper trading
        In a real implementation, this would get actual prices from an API
        """
        try:
            # For demonstration purposes, we generate a price based on the token address
            # In a real implementation, this would call an API to get the current price
            
            # Seed based on token address to get a consistent base price
            price_seed = int(token_address[-8:], 16) / 10**10 if token_address else 0.0001
            base_price = max(0.000001, price_seed)  # Ensure price is positive
            
            # Add some random fluctuation
            fluctuation = random.uniform(-0.05, 0.05)  # -5% to +5%
            
            # Check if we need to simulate price increases or crashes for demo purposes
            time_based_trend = 0
            current_hour = time.localtime().tm_hour
            if current_hour % 4 == 0:  # Every 4 hours, simulate a pump
                time_based_trend = random.uniform(0.05, 0.15)  # +5% to +15%
            elif current_hour % 6 == 0:  # Every 6 hours, simulate a dump
                time_based_trend = random.uniform(-0.15, -0.05)  # -15% to -5%
            
            # Calculate final price
            current_price = base_price * (1 + fluctuation + time_based_trend)
            
            return current_price
        except Exception as e:
            logger.error(f"Error generating price for {token_address}: {str(e)}")
            return 0.0001  # Return a default price on error
    
    def _get_token_name(self, token_address):
        """Get a token name for display purposes"""
        try:
            # In a real implementation, this would look up the actual token name
            # For simulation, we generate a name based on the address
            if not token_address:
                return "Unknown Token"
                
            prefix = "".join([chr(ord('A') + int(c, 16) % 26) for c in token_address[:4] if c.isalnum()])
            return f"{prefix} Token"
        except Exception as e:
            logger.error(f"Error generating token name: {str(e)}")
            return "Unknown Token"
    
    def _get_token_symbol(self, token_address):
        """Get a token symbol for display purposes"""
        try:
            # In a real implementation, this would look up the actual token symbol
            # For simulation, we generate a symbol based on the address
            if not token_address:
                return "UNK"
                
            return "".join([chr(ord('A') + int(c, 16) % 26) for c in token_address[:3] if c.isalnum()])
        except Exception as e:
            logger.error(f"Error generating token symbol: {str(e)}")
            return "UNK"