"""
Signal handling for the Stratos Trading Bot

This file handles signal detection, parsing, and formatting.
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Signal:
    """Represents a trading signal"""
    def __init__(self, token_address, message_text, source_channel):
        self.token_address = token_address
        self.original_message = message_text
        self.source_channel = source_channel
        self.timestamp = datetime.now()
        self.id = f"{token_address}_{self.timestamp.strftime('%Y%m%d%H%M%S')}"
        
        # Extract parameters from message text
        self.parameters = SignalParser.extract_trade_parameters(message_text)

class SignalParser:
    """Parses incoming messages for signals"""
    
    @staticmethod
    def extract_token_address(message_text):
        """
        Extract token address from message text
        Returns None if no valid address is found
        """
        # Look for wallet/contract address pattern (hex string of 40+ chars)
        token_match = re.search(r'[a-zA-Z0-9]{40,}', message_text)
        
        if token_match:
            return token_match.group(0)
        return None
    
    @staticmethod
    def is_signal_message(message_text):
        """
        Determine if a message likely contains a trading signal
        Based on common patterns in trading signal messages
        """
        # Check for common keywords
        signal_keywords = [
            'buy', 'sell', 'pump', 'ape', 'degen', 'hunt', 'sl', 'stop loss',
            'target', 'entry', 'exit', 'take profit', 'tp', 'contract'
        ]
        
        # Check if message has a token address
        has_token = SignalParser.extract_token_address(message_text) is not None
        
        # Check if message has signal keywords
        keyword_match = any(keyword.lower() in message_text.lower() for keyword in signal_keywords)
        
        # Signal messages typically have at least one keyword and a token address
        return has_token and keyword_match
    
    @staticmethod
    def extract_trade_parameters(message_text):
        """
        Extract trading parameters from the signal message
        Returns a dictionary of parameters
        """
        params = {}
        
        # Extract position size (common formats: "Ape 5%" or "Position 2%" or "Allocate 10%")
        position_match = re.search(r'(ape|position|allocate|buy)\s*(\d+(?:\.\d+)?)\s*%', message_text, re.IGNORECASE)
        if position_match:
            params['position_size'] = float(position_match.group(2))
        
        # Extract stop loss (common formats: "SL -30%" or "Stop Loss 25%" or "stoploss: 20%")
        sl_match = re.search(r'(sl|stop\s*loss|stoploss)[:\s]*-?\s*(\d+(?:\.\d+)?)\s*%', message_text, re.IGNORECASE)
        if sl_match:
            params['stop_loss'] = float(sl_match.group(2))
        
        # Extract take profit levels (common formats: "TP: 20%, 40%, 80%" or "Take Profit: 25% 50% 100%")
        tp_match = re.search(r'(tp|take\s*profit)[:\s]*((?:\d+(?:\.\d+)?%[\s,]*)+)', message_text, re.IGNORECASE)
        if tp_match:
            # Extract all percentages
            tp_str = tp_match.group(2)
            tp_values = re.findall(r'(\d+(?:\.\d+)?)\s*%', tp_str)
            if tp_values:
                params['take_profit'] = [float(val) for val in tp_values]
        
        return params