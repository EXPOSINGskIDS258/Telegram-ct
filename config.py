"""
Configuration management for the Stratos Trading Bot with .env support

This file provides Config class for Stratos Trading Bot.
"""

import json
import os
import logging
import base64
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the bot with .env support"""
    def __init__(self, config_file='config.json', env_file='.env'):
        self.config_file = config_file
        self.env_file = env_file
        self._encryption_key = None
        self._private_key = None  # Private key stored only in memory, never in plaintext
        
        # Default values
        self.api_id = None
        self.api_hash = None
        self.phone = None
        self.source_channels = []
        self.destination_channel = None
        self.custom_branding = 'Stratos Signal'
        self.initial_sl_percent = 30
        self.trail_percent = 5
        self.delay_seconds = 0
        self.wallet_address = None
        self.dex_name = None
        self.chain_name = None
        
        # First, load from .env file if it exists
        self._load_env()
        
        # Then load from config.json if it exists (will override .env values)
        if os.path.exists(config_file):
            self._load_config()
        else:
            logger.info("No config file found. Using environment values or defaults.")
        
    def _load_env(self):
        """Load configuration from .env file"""
        try:
            # Create .env file if it doesn't exist
            if not os.path.exists(self.env_file):
                with open(self.env_file, 'w') as f:
                    pass  # Create empty file
                logger.info(f"Created new {self.env_file} file")
            
            # Load environment variables
            load_dotenv(self.env_file)
            
            # Telegram API settings
            self.api_id = os.getenv('TELEGRAM_API_ID')
            if self.api_id and self.api_id.isdigit():
                self.api_id = int(self.api_id)
            self.api_hash = os.getenv('TELEGRAM_API_HASH')
            self.phone = os.getenv('TELEGRAM_PHONE')
            
            # Source channels
            channels_str = os.getenv('SOURCE_CHANNELS')
            if channels_str:
                self.source_channels = channels_str.split(',')
            
            # Trading parameters
            if os.getenv('POSITION_SIZE_PERCENT'):
                self.position_size_percent = float(os.getenv('POSITION_SIZE_PERCENT'))
            if os.getenv('INITIAL_SL_PERCENT'):
                self.initial_sl_percent = float(os.getenv('INITIAL_SL_PERCENT'))
            if os.getenv('TRAIL_PERCENT'):
                self.trail_percent = float(os.getenv('TRAIL_PERCENT'))
            if os.getenv('TAKE_PROFIT_LEVELS'):
                self.take_profit_levels = os.getenv('TAKE_PROFIT_LEVELS')
            
            # DEX settings
            self.dex_name = os.getenv('DEX_NAME', self.dex_name)
            self.chain_name = os.getenv('CHAIN_NAME', self.chain_name)
            
            # Paper trading mode
            if os.getenv('PAPER_TRADING_MODE'):
                self.paper_trading_mode = os.getenv('PAPER_TRADING_MODE').lower() == 'true'
            
            # Other settings
            if os.getenv('MAX_SLIPPAGE'):
                self.max_slippage = float(os.getenv('MAX_SLIPPAGE'))
            if os.getenv('GAS_PRIORITY'):
                self.gas_priority = int(os.getenv('GAS_PRIORITY'))
            
            # Memecoin safety settings
            if os.getenv('MIN_LIQUIDITY_USD'):
                self.min_liquidity_usd = float(os.getenv('MIN_LIQUIDITY_USD'))
            if os.getenv('MAX_BUY_TAX'):
                self.max_buy_tax = float(os.getenv('MAX_BUY_TAX'))
            if os.getenv('MAX_SELL_TAX'):
                self.max_sell_tax = float(os.getenv('MAX_SELL_TAX'))
            if os.getenv('HONEYPOT_CHECK'):
                self.honeypot_check = os.getenv('HONEYPOT_CHECK').lower() == 'true'
            
            logger.info("Environment configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading environment configuration: {str(e)}")
        
    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Load regular settings
            self.api_id = config.get('api_id', self.api_id)
            self.api_hash = config.get('api_hash', self.api_hash)
            self.phone = config.get('phone', self.phone)
            self.source_channels = config.get('source_channels', self.source_channels)
            self.destination_channel = config.get('destination_channel', self.destination_channel)
            self.custom_branding = config.get('custom_branding', self.custom_branding)
            self.initial_sl_percent = config.get('initial_sl_percent', self.initial_sl_percent)
            self.trail_percent = config.get('trail_percent', self.trail_percent)
            self.delay_seconds = config.get('delay_seconds', self.delay_seconds)
            self.wallet_address = config.get('wallet_address', self.wallet_address)
            self.dex_name = config.get('dex_name', self.dex_name)
            self.chain_name = config.get('chain_name', self.chain_name)
            
            # Load trading settings
            self.position_size_percent = config.get('position_size_percent', getattr(self, 'position_size_percent', 3))
            self.max_slippage = config.get('max_slippage', getattr(self, 'max_slippage', 15))
            self.gas_priority = config.get('gas_priority', getattr(self, 'gas_priority', 3))
            self.take_profit_levels = config.get('take_profit_levels', getattr(self, 'take_profit_levels', '20,40,100'))
            
            # Load memecoin settings
            self.min_liquidity_usd = config.get('min_liquidity_usd', getattr(self, 'min_liquidity_usd', 50000))
            self.max_buy_tax = config.get('max_buy_tax', getattr(self, 'max_buy_tax', 10))
            self.max_sell_tax = config.get('max_sell_tax', getattr(self, 'max_sell_tax', 15))
            self.honeypot_check = config.get('honeypot_check', getattr(self, 'honeypot_check', True))
            
            # Load encrypted private key if it exists
            encrypted_key = config.get('encrypted_private_key')
            if encrypted_key:
                # The key will only be decrypted when needed
                self._encrypted_private_key = encrypted_key
                
            logger.info("Configuration file loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
            
    def save(self):
        """Save configuration to file and .env"""
        self._save_env()  # Save to .env file
        
        # Save to config.json
        config = {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'phone': self.phone,
            'source_channels': self.source_channels,
            'destination_channel': self.destination_channel,
            'custom_branding': self.custom_branding,
            'initial_sl_percent': self.initial_sl_percent,
            'trail_percent': self.trail_percent,
            'delay_seconds': self.delay_seconds,
            'wallet_address': self.wallet_address,
            'dex_name': self.dex_name,
            'chain_name': self.chain_name,
            
            # Trading settings
            'position_size_percent': self.position_size_percent,
            'max_slippage': self.max_slippage,
            'gas_priority': self.gas_priority,
            'take_profit_levels': self.take_profit_levels,
            
            # Memecoin settings
            'min_liquidity_usd': self.min_liquidity_usd,
            'max_buy_tax': self.max_buy_tax,
            'max_sell_tax': self.max_sell_tax,
            'honeypot_check': self.honeypot_check,
            
            # Paper trading
            'paper_trading_mode': getattr(self, 'paper_trading_mode', False)
        }
        
        # Encrypt and save private key if it was set
        if self._private_key:
            if not self._encryption_key:
                self._generate_encryption_key()
                
            # Encrypt the private key before saving
            config['encrypted_private_key'] = self._encrypt_private_key()
            
        # Create backup of existing config
        if os.path.exists(self.config_file):
            backup_file = f"{self.config_file}.bak"
            try:
                with open(self.config_file, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
            except Exception as e:
                logger.warning(f"Failed to create config backup: {str(e)}")
        
        # Save configuration
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def _save_env(self):
        """Save configuration to .env file"""
        try:
            # Create .env file if it doesn't exist
            if not os.path.exists(self.env_file):
                with open(self.env_file, 'w') as f:
                    pass
            
            # Save Telegram API settings
            self._set_env('TELEGRAM_API_ID', str(self.api_id) if self.api_id else '')
            self._set_env('TELEGRAM_API_HASH', self.api_hash or '')
            self._set_env('TELEGRAM_PHONE', self.phone or '')
            
            # Save source channels
            self._set_env('SOURCE_CHANNELS', ','.join(self.source_channels) if self.source_channels else '')
            
            # Save trading parameters
            if hasattr(self, 'position_size_percent'):
                self._set_env('POSITION_SIZE_PERCENT', str(self.position_size_percent))
            if hasattr(self, 'initial_sl_percent'):
                self._set_env('INITIAL_SL_PERCENT', str(self.initial_sl_percent))
            if hasattr(self, 'trail_percent'):
                self._set_env('TRAIL_PERCENT', str(self.trail_percent))
            if hasattr(self, 'take_profit_levels'):
                self._set_env('TAKE_PROFIT_LEVELS', self.take_profit_levels)
            
            # Save DEX settings
            self._set_env('DEX_NAME', self.dex_name or '')
            self._set_env('CHAIN_NAME', self.chain_name or '')
            
            # Save wallet address (but not private key for security)
            self._set_env('WALLET_ADDRESS', self.wallet_address or '')
            
            # Save paper trading mode
            if hasattr(self, 'paper_trading_mode'):
                self._set_env('PAPER_TRADING_MODE', str(self.paper_trading_mode).lower())
            
            # Save other settings
            if hasattr(self, 'max_slippage'):
                self._set_env('MAX_SLIPPAGE', str(self.max_slippage))
            if hasattr(self, 'gas_priority'):
                self._set_env('GAS_PRIORITY', str(self.gas_priority))
            
            # Save memecoin settings
            if hasattr(self, 'min_liquidity_usd'):
                self._set_env('MIN_LIQUIDITY_USD', str(self.min_liquidity_usd))
            if hasattr(self, 'max_buy_tax'):
                self._set_env('MAX_BUY_TAX', str(self.max_buy_tax))
            if hasattr(self, 'max_sell_tax'):
                self._set_env('MAX_SELL_TAX', str(self.max_sell_tax))
            if hasattr(self, 'honeypot_check'):
                self._set_env('HONEYPOT_CHECK', str(self.honeypot_check).lower())
            
            logger.info("Environment configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving environment configuration: {str(e)}")
    
    def _set_env(self, key, value):
        """Safely set an environment variable in the .env file"""
        try:
            set_key(self.env_file, key, value)
        except Exception as e:
            logger.error(f"Error setting environment variable {key}: {str(e)}")
            
            # Fallback method if python-dotenv's set_key fails
            try:
                # Read current content
                with open(self.env_file, 'r') as f:
                    lines = f.readlines()
                
                # Check if key exists
                key_exists = False
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}\n"
                        key_exists = True
                        break
                
                # Add key if it doesn't exist
                if not key_exists:
                    lines.append(f"{key}={value}\n")
                
                # Write back
                with open(self.env_file, 'w') as f:
                    f.writelines(lines)
            except Exception as e2:
                logger.error(f"Fallback method also failed for setting {key}: {str(e2)}")
            
    def _generate_encryption_key(self):
        """Generate encryption key for private key protection"""
        # Use device-specific data as salt (better security)
        hostname = os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'unknown')
        salt = hostname.encode() + b'stratos_salt'
        
        # Use PBKDF2 to derive a secure key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Create a deterministic key based on hardware + salt
        # This means the same machine can decrypt the key, but others can't
        base_key = (hostname + 'stratos_secure_key').encode()
        key = base64.urlsafe_b64encode(kdf.derive(base_key))
        self._encryption_key = key
    
    def _encrypt_private_key(self):
        """Encrypt the private key before saving to disk"""
        if not self._private_key:
            return None
            
        if not self._encryption_key:
            self._generate_encryption_key()
            
        # Create Fernet cipher for encryption
        cipher = Fernet(self._encryption_key)
        encrypted_key = cipher.encrypt(self._private_key.encode())
        return encrypted_key.decode()
    
    def _decrypt_private_key(self):
        """Decrypt the private key from storage"""
        if not hasattr(self, '_encrypted_private_key') or not self._encrypted_private_key:
            return None
            
        if not self._encryption_key:
            self._generate_encryption_key()
            
        try:
            # Create Fernet cipher for decryption
            cipher = Fernet(self._encryption_key)
            decrypted_key = cipher.decrypt(self._encrypted_private_key.encode())
            return decrypted_key.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt private key: {str(e)}")
            return None
    
    # Property for secure private key handling
    @property
    def private_key(self):
        """Get the private key (decrypting if necessary)"""
        # If key is already in memory, return it
        if self._private_key:
            return self._private_key
            
        # Otherwise try to decrypt from storage
        return self._decrypt_private_key()
        
    @private_key.setter
    def private_key(self, value):
        """Set the private key (only stored in memory until save() is called)"""
        self._private_key = value
        
    def has_credentials(self):
        """Check if the minimum required credentials are available"""
        return (
            self.api_id is not None and 
            self.api_hash is not None and
            self.phone is not None and
            len(self.source_channels) > 0
        )