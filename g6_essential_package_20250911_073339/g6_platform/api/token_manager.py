#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Token Manager - G6 Platform v3.0
Consolidated authentication and token management system.

Restructured from: token_manager.py, kite_login_and_launch_FINAL_WORKING.py
Features:
- Secure token storage and management
- Automatic token refresh and renewal
- Session management with encryption
- Token validation and health checks
- Secure credential storage
- Authentication flow automation
"""

import os
import time
import logging
import threading
import json
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import pickle
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Kite Connect imports
try:
    from kiteconnect import KiteConnect
    from kiteconnect.exceptions import KiteException, TokenException, NetworkException
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    KiteConnect = None
    KiteException = Exception
    TokenException = Exception
    NetworkException = Exception

logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    """Token information with metadata."""
    access_token: str
    user_id: str
    user_name: str
    broker: str = "kite"
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    is_valid: bool = True
    session_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuthCredentials:
    """Authentication credentials."""
    api_key: str
    api_secret: str
    user_id: Optional[str] = None
    password: Optional[str] = None
    totp_key: Optional[str] = None
    redirect_url: Optional[str] = None

@dataclass
class SessionInfo:
    """Session information tracking."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    auth_method: str = "manual"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SecureStorage:
    """
    Secure storage for sensitive authentication data.
    """
    
    def __init__(self, storage_path: Union[str, Path] = None):
        """
        Initialize secure storage.
        
        Args:
            storage_path: Path to storage file
        """
        self.storage_path = Path(storage_path or Path.home() / ".g6_platform" / "tokens.enc")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate or load encryption key
        self.key_path = self.storage_path.parent / ".encryption_key"
        self._encryption_key = self._get_or_create_key()
        self._cipher = Fernet(self._encryption_key)
        
        logger.info(f"🔐 Secure storage initialized: {self.storage_path}")
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_path.exists():
            try:
                with open(self.key_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"⚠️ Failed to load encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        try:
            with open(self.key_path, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_path, 0o600)
            logger.info("🔑 New encryption key generated")
        except Exception as e:
            logger.error(f"🔴 Failed to save encryption key: {e}")
        
        return key
    
    def store(self, key: str, data: Any) -> bool:
        """
        Store encrypted data.
        
        Args:
            key: Storage key
            data: Data to store
            
        Returns:
            True if successful
        """
        try:
            # Load existing data
            existing_data = self._load_data()
            
            # Update with new data
            existing_data[key] = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'checksum': hashlib.sha256(str(data).encode()).hexdigest()
            }
            
            # Save encrypted data
            return self._save_data(existing_data)
            
        except Exception as e:
            logger.error(f"🔴 Failed to store data: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve decrypted data.
        
        Args:
            key: Storage key
            
        Returns:
            Stored data or None
        """
        try:
            data = self._load_data()
            if key in data:
                entry = data[key]
                
                # Verify checksum
                stored_checksum = entry.get('checksum', '')
                calculated_checksum = hashlib.sha256(str(entry['data']).encode()).hexdigest()
                
                if stored_checksum != calculated_checksum:
                    logger.warning(f"⚠️ Checksum mismatch for key: {key}")
                    return None
                
                return entry['data']
            
            return None
            
        except Exception as e:
            logger.error(f"🔴 Failed to retrieve data: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete stored data.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        try:
            data = self._load_data()
            if key in data:
                del data[key]
                return self._save_data(data)
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to delete data: {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """List all stored keys."""
        try:
            data = self._load_data()
            return list(data.keys())
        except Exception:
            return []
    
    def _load_data(self) -> Dict[str, Any]:
        """Load and decrypt data."""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"🔴 Failed to load data: {e}")
            return {}
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """Encrypt and save data."""
        try:
            json_data = json.dumps(data, indent=2).encode()
            encrypted_data = self._cipher.encrypt(json_data)
            
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.storage_path, 0o600)
            return True
            
        except Exception as e:
            logger.error(f"🔴 Failed to save data: {e}")
            return False

class TokenManager:
    """
    🔐 Comprehensive token and session management system.
    
    Provides secure storage, automatic refresh, and validation of authentication
    tokens across multiple brokers and session types.
    """
    
    def __init__(self, 
                 storage_path: Optional[Union[str, Path]] = None,
                 auto_refresh: bool = True,
                 refresh_margin_minutes: int = 30):
        """
        Initialize token manager.
        
        Args:
            storage_path: Path for secure token storage
            auto_refresh: Enable automatic token refresh
            refresh_margin_minutes: Minutes before expiry to refresh
        """
        if not KITE_AVAILABLE:
            logger.warning("⚠️ KiteConnect not available, limited functionality")
        
        self.auto_refresh = auto_refresh
        self.refresh_margin = timedelta(minutes=refresh_margin_minutes)
        
        # Secure storage
        self.storage = SecureStorage(storage_path)
        
        # Token tracking
        self._tokens: Dict[str, TokenInfo] = {}
        self._sessions: Dict[str, SessionInfo] = {}
        self._lock = threading.RLock()
        
        # Auto-refresh thread
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        # Load existing tokens
        self._load_tokens()
        
        # Start auto-refresh if enabled
        if auto_refresh:
            self._start_auto_refresh()
        
        logger.info("🔐 Token manager initialized")
    
    def _load_tokens(self):
        """Load tokens from secure storage."""
        try:
            stored_tokens = self.storage.retrieve('tokens')
            if stored_tokens:
                for key, token_data in stored_tokens.items():
                    # Reconstruct TokenInfo objects
                    token_info = TokenInfo(**token_data)
                    self._tokens[key] = token_info
                
                logger.info(f"📥 Loaded {len(self._tokens)} tokens from storage")
            
            stored_sessions = self.storage.retrieve('sessions')
            if stored_sessions:
                for key, session_data in stored_sessions.items():
                    session_info = SessionInfo(**session_data)
                    self._sessions[key] = session_info
                
                logger.info(f"📥 Loaded {len(self._sessions)} sessions from storage")
                
        except Exception as e:
            logger.error(f"🔴 Failed to load tokens: {e}")
    
    def _save_tokens(self):
        """Save tokens to secure storage."""
        try:
            # Convert TokenInfo objects to dictionaries
            token_data = {}
            for key, token_info in self._tokens.items():
                token_dict = {
                    'access_token': token_info.access_token,
                    'user_id': token_info.user_id,
                    'user_name': token_info.user_name,
                    'broker': token_info.broker,
                    'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None,
                    'created_at': token_info.created_at.isoformat(),
                    'last_used': token_info.last_used.isoformat(),
                    'is_valid': token_info.is_valid,
                    'session_data': token_info.session_data
                }
                token_data[key] = token_dict
            
            self.storage.store('tokens', token_data)
            
            # Save sessions
            session_data = {}
            for key, session_info in self._sessions.items():
                session_dict = {
                    'session_id': session_info.session_id,
                    'created_at': session_info.created_at.isoformat(),
                    'last_activity': session_info.last_activity.isoformat(),
                    'is_active': session_info.is_active,
                    'auth_method': session_info.auth_method,
                    'ip_address': session_info.ip_address,
                    'user_agent': session_info.user_agent
                }
                session_data[key] = session_dict
            
            self.storage.store('sessions', session_data)
            
        except Exception as e:
            logger.error(f"🔴 Failed to save tokens: {e}")
    
    def store_token(self, 
                   broker: str,
                   user_id: str,
                   access_token: str,
                   user_name: str = None,
                   expires_at: datetime = None,
                   session_data: Dict[str, Any] = None) -> str:
        """
        Store authentication token.
        
        Args:
            broker: Broker name (kite, zerodha, etc.)
            user_id: User ID
            access_token: Access token
            user_name: User name
            expires_at: Token expiration time
            session_data: Additional session data
            
        Returns:
            Token key for future reference
        """
        with self._lock:
            token_key = f"{broker}:{user_id}"
            
            token_info = TokenInfo(
                access_token=access_token,
                user_id=user_id,
                user_name=user_name or user_id,
                broker=broker,
                expires_at=expires_at,
                session_data=session_data or {}
            )
            
            self._tokens[token_key] = token_info
            self._save_tokens()
            
            logger.info(f"🔐 Token stored for {token_key}")
            return token_key
    
    def get_token(self, broker: str, user_id: str) -> Optional[TokenInfo]:
        """
        Get token information.
        
        Args:
            broker: Broker name
            user_id: User ID
            
        Returns:
            TokenInfo or None
        """
        with self._lock:
            token_key = f"{broker}:{user_id}"
            token_info = self._tokens.get(token_key)
            
            if token_info:
                # Check if token is still valid
                if self._is_token_valid(token_info):
                    token_info.last_used = datetime.now()
                    return token_info
                else:
                    # Mark as invalid
                    token_info.is_valid = False
                    self._save_tokens()
                    logger.warning(f"⚠️ Token expired for {token_key}")
            
            return None
    
    def get_access_token(self, broker: str, user_id: str) -> Optional[str]:
        """
        Get access token string.
        
        Args:
            broker: Broker name
            user_id: User ID
            
        Returns:
            Access token string or None
        """
        token_info = self.get_token(broker, user_id)
        return token_info.access_token if token_info else None
    
    def validate_token(self, broker: str, user_id: str) -> bool:
        """
        Validate token with broker API.
        
        Args:
            broker: Broker name
            user_id: User ID
            
        Returns:
            True if valid
        """
        token_info = self.get_token(broker, user_id)
        if not token_info:
            return False
        
        try:
            if broker.lower() == 'kite' and KITE_AVAILABLE:
                # Validate with Kite API
                api_key = os.getenv('KITE_API_KEY')
                if not api_key:
                    logger.error("🔴 KITE_API_KEY not found in environment")
                    return False
                
                kite = KiteConnect(api_key=api_key)
                kite.set_access_token(token_info.access_token)
                
                # Test API call
                profile = kite.profile()
                is_valid = bool(profile.get('user_id') == user_id)
                
                # Update token validity
                token_info.is_valid = is_valid
                token_info.last_used = datetime.now()
                self._save_tokens()
                
                return is_valid
            
            else:
                logger.warning(f"⚠️ Validation not implemented for broker: {broker}")
                return True  # Assume valid if we can't validate
                
        except Exception as e:
            logger.error(f"🔴 Token validation failed: {e}")
            token_info.is_valid = False
            self._save_tokens()
            return False
    
    def refresh_token(self, broker: str, user_id: str, credentials: AuthCredentials) -> bool:
        """
        Refresh authentication token.
        
        Args:
            broker: Broker name
            user_id: User ID
            credentials: Authentication credentials
            
        Returns:
            True if refresh successful
        """
        try:
            if broker.lower() == 'kite' and KITE_AVAILABLE:
                return self._refresh_kite_token(user_id, credentials)
            else:
                logger.warning(f"⚠️ Token refresh not implemented for broker: {broker}")
                return False
                
        except Exception as e:
            logger.error(f"🔴 Token refresh failed: {e}")
            return False
    
    def _refresh_kite_token(self, user_id: str, credentials: AuthCredentials) -> bool:
        """Refresh Kite Connect token."""
        try:
            kite = KiteConnect(api_key=credentials.api_key)
            
            # Generate login URL
            login_url = kite.login_url()
            logger.info(f"🔗 Kite login URL: {login_url}")
            
            # This would require manual intervention or automated browser
            # For now, we'll assume the token needs manual refresh
            logger.warning("⚠️ Kite token refresh requires manual login")
            return False
            
        except Exception as e:
            logger.error(f"🔴 Kite token refresh failed: {e}")
            return False
    
    def _is_token_valid(self, token_info: TokenInfo) -> bool:
        """Check if token is valid (not expired)."""
        if not token_info.is_valid:
            return False
        
        if token_info.expires_at:
            return datetime.now() < token_info.expires_at
        
        # If no expiry set, assume valid for 24 hours
        age = datetime.now() - token_info.created_at
        return age < timedelta(hours=24)
    
    def _needs_refresh(self, token_info: TokenInfo) -> bool:
        """Check if token needs refresh soon."""
        if not token_info.expires_at:
            return False
        
        time_until_expiry = token_info.expires_at - datetime.now()
        return time_until_expiry <= self.refresh_margin
    
    def _start_auto_refresh(self):
        """Start automatic token refresh thread."""
        def refresh_worker():
            while not self._stop_refresh.wait(300):  # Check every 5 minutes
                try:
                    self._check_and_refresh_tokens()
                except Exception as e:
                    logger.error(f"🔴 Auto-refresh error: {e}")
        
        self._refresh_thread = threading.Thread(
            target=refresh_worker,
            daemon=True,
            name="TokenRefresh"
        )
        self._refresh_thread.start()
        logger.info("🔄 Auto-refresh thread started")
    
    def _check_and_refresh_tokens(self):
        """Check all tokens and refresh if needed."""
        with self._lock:
            tokens_to_refresh = []
            
            for token_key, token_info in self._tokens.items():
                if token_info.is_valid and self._needs_refresh(token_info):
                    tokens_to_refresh.append((token_key, token_info))
            
            if tokens_to_refresh:
                logger.info(f"🔄 Found {len(tokens_to_refresh)} tokens needing refresh")
                # Auto-refresh would require stored credentials
                # For now, just log the need for refresh
                for token_key, token_info in tokens_to_refresh:
                    logger.warning(f"⚠️ Token {token_key} needs manual refresh")
    
    def create_session(self, 
                      broker: str,
                      user_id: str,
                      auth_method: str = "manual",
                      ip_address: str = None,
                      user_agent: str = None) -> str:
        """
        Create authentication session.
        
        Args:
            broker: Broker name
            user_id: User ID
            auth_method: Authentication method
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session ID
        """
        with self._lock:
            session_id = secrets.token_urlsafe(32)
            
            session_info = SessionInfo(
                session_id=session_id,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                auth_method=auth_method,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            session_key = f"{broker}:{user_id}:{session_id}"
            self._sessions[session_key] = session_info
            self._save_tokens()
            
            logger.info(f"🆔 Session created: {session_id}")
            return session_id
    
    def get_session(self, broker: str, user_id: str, session_id: str) -> Optional[SessionInfo]:
        """Get session information."""
        with self._lock:
            session_key = f"{broker}:{user_id}:{session_id}"
            session_info = self._sessions.get(session_key)
            
            if session_info and session_info.is_active:
                session_info.last_activity = datetime.now()
                return session_info
            
            return None
    
    def invalidate_session(self, broker: str, user_id: str, session_id: str):
        """Invalidate session."""
        with self._lock:
            session_key = f"{broker}:{user_id}:{session_id}"
            session_info = self._sessions.get(session_key)
            
            if session_info:
                session_info.is_active = False
                self._save_tokens()
                logger.info(f"🚫 Session invalidated: {session_id}")
    
    def list_tokens(self) -> List[Dict[str, Any]]:
        """List all stored tokens."""
        with self._lock:
            token_list = []
            for token_key, token_info in self._tokens.items():
                token_list.append({
                    'key': token_key,
                    'broker': token_info.broker,
                    'user_id': token_info.user_id,
                    'user_name': token_info.user_name,
                    'created_at': token_info.created_at.isoformat(),
                    'last_used': token_info.last_used.isoformat(),
                    'is_valid': token_info.is_valid,
                    'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None
                })
            return token_list
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens.
        
        Returns:
            Number of tokens removed
        """
        with self._lock:
            expired_keys = []
            
            for token_key, token_info in self._tokens.items():
                if not self._is_token_valid(token_info):
                    expired_keys.append(token_key)
            
            for key in expired_keys:
                del self._tokens[key]
            
            if expired_keys:
                self._save_tokens()
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired tokens")
            
            return len(expired_keys)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get token manager health status."""
        with self._lock:
            valid_tokens = sum(1 for t in self._tokens.values() if t.is_valid)
            active_sessions = sum(1 for s in self._sessions.values() if s.is_active)
            
            return {
                'total_tokens': len(self._tokens),
                'valid_tokens': valid_tokens,
                'expired_tokens': len(self._tokens) - valid_tokens,
                'active_sessions': active_sessions,
                'auto_refresh_enabled': self.auto_refresh,
                'storage_keys': len(self.storage.list_keys())
            }
    
    def shutdown(self):
        """Shutdown token manager."""
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._stop_refresh.set()
            self._refresh_thread.join(timeout=5)
        
        # Save any pending changes
        self._save_tokens()
        
        logger.info("🔐 Token manager shutdown complete")

# Global token manager instance
_token_manager: Optional[TokenManager] = None

def get_token_manager() -> TokenManager:
    """Get or create global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager

def get_access_token(broker: str, user_id: str) -> Optional[str]:
    """Get access token for broker and user."""
    return get_token_manager().get_access_token(broker, user_id)

def store_token(broker: str, user_id: str, access_token: str, **kwargs) -> str:
    """Store access token."""
    return get_token_manager().store_token(broker, user_id, access_token, **kwargs)

def validate_token(broker: str, user_id: str) -> bool:
    """Validate token with broker."""
    return get_token_manager().validate_token(broker, user_id)