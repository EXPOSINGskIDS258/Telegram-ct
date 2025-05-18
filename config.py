"""
Configuration management for the Stratos Trading Bot

This file provides Config class for Stratos Trading Bot.
"""

import json
import os
import logging
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the bot"""
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
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
        
        # Load configuration if exists
        if os.path.exists(config_file):
            self._load_config()
        else:
            logger.info("No config file found. Using default values.")
        
    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Load regular settings
            self.api_id = config.get('api_id')
            self.api_hash = config.get('api_hash')
            self.phone = config.get('phone')
            self.source_channels = config.get('source_channels', [])
            self.destination_channel = config.get('destination_channel')
            self.custom_branding = config.get('custom_branding', 'Stratos Signal')
            self.initial_sl_percent = config.get('initial_sl_percent', 30)
            self.trail_percent = config.get('trail_percent', 5)
            self.delay_seconds = config.get('delay_seconds', 0)
            self.wallet_address = config.get('wallet_address')
            self.dex_name = config.get('dex_name')
            self.chain_name = config.get('chain_name')
            
            # Load trading settings
            self.position_size_percent = config.get('position_size_percent', 3)
            self.max_slippage = config.get('max_slippage', 15)
            self.gas_priority = config.get('gas_priority', 3)
            self.take_profit_levels = config.get('take_profit_levels', '20,40,100')
            
            # Load memecoin settings
            self.min_liquidity_usd = config.get('min_liquidity_usd', 50000)
            self.max_buy_tax = config.get('max_buy_tax', 10)
            self.max_sell_tax = config.get('max_sell_tax', 15)
            self.honeypot_check = config.get('honeypot_check', True)
            
            # Load encrypted private key if it exists
            encrypted_key = config.get('encrypted_private_key')
            if encrypted_key:
                # The key will only be decrypted when needed
                self._encrypted_private_key = encrypted_key
                
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            
    def save(self):
        """Save configuration to file"""
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
            'honeypot_check': self.honeypot_check
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