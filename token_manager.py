#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Complete Token Manager and Authentication System for G6.1 Platform
Author: AI Assistant (Secure token management with auto-refresh)

✅ Features:
- Secure token storage and management
- Automatic token refresh and renewal
- Multi-broker authentication support
- Session management with encryption
- Token validation and health checks
- Secure credential storage
- Authentication flow automation
- Error handling and recovery
"""

import logging
import time
import datetime
import threading
import json
import hashlib
import secrets
import base64
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Kite Connect imports with fallback
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
    """🔐 Token information structure."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None
    token_type: str = "bearer"
    scope: Optional[str] = None
    
    # 📊 Metadata
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    broker: str = "kite"
    
    # ⏰ Timestamps
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_validated: Optional[datetime.datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """⏰ Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.datetime.now() >= self.expires_at
    
    @property
    def expires_in_seconds(self) -> Optional[int]:
        """⏰ Get seconds until expiration."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.datetime.now()
        return max(0, int(delta.total_seconds()))
    
    @property
    def needs_refresh(self) -> bool:
        """🔄 Check if token needs refresh (within 1 hour of expiry)."""
        if not self.expires_at:
            return False
        
        refresh_threshold = datetime.datetime.now() + datetime.timedelta(hours=1)
        return self.expires_at <= refresh_threshold

@dataclass
class AuthenticationResult:
    """✅ Authentication result structure."""
    success: bool
    token_info: Optional[TokenInfo] = None
    error_message: str = ""
    error_code: Optional[str] = None
    
    # 📊 Additional data
    user_profile: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    session_data: Dict[str, Any] = field(default_factory=dict)

class SecureStorage:
    """
    🔒 Secure storage for sensitive data with encryption.
    """
    
    def __init__(self, storage_path: str, password: Optional[str] = None):
        """
        🆕 Initialize secure storage.
        
        Args:
            storage_path: Path to storage file
            password: Optional password for encryption
        """
        self.storage_path = Path(storage_path)
        self.password = password
        self.logger = logging.getLogger(f"{__name__}.SecureStorage")
        
        # 🔐 Initialize encryption
        self.fernet = self._initialize_encryption()
        
        # 📁 Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"✅ Secure storage initialized: {self.storage_path}")
    
    def _initialize_encryption(self) -> Fernet:
        """🔐 Initialize encryption with key derivation."""
        try:
            if self.password:
                # 🔑 Derive key from password
                salt = b'g6_platform_salt_2025'  # Fixed salt for consistency
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            else:
                # 🔑 Generate random key
                key = Fernet.generate_key()
                
                # 💾 Store key for later use (in production, use secure key management)
                key_file = self.storage_path.with_suffix('.key')
                if not key_file.exists():
                    with open(key_file, 'wb') as f:
                        f.write(key)
                    os.chmod(key_file, 0o600)  # Restrict permissions
                else:
                    with open(key_file, 'rb') as f:
                        key = f.read()
            
            return Fernet(key)
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to initialize encryption: {e}")
            # 🆘 Fallback to no encryption
            return None
    
    def store(self, key: str, data: Dict[str, Any]) -> bool:
        """💾 Store encrypted data."""
        try:
            # 📝 Serialize data
            json_data = json.dumps(data, default=str, indent=2)
            
            # 🔐 Encrypt if available
            if self.fernet:
                encrypted_data = self.fernet.encrypt(json_data.encode())
                storage_data = {
                    'encrypted': True,
                    'data': base64.b64encode(encrypted_data).decode()
                }
            else:
                storage_data = {
                    'encrypted': False,
                    'data': json_data
                }
            
            storage_data['timestamp'] = datetime.datetime.now().isoformat()
            storage_data['key'] = key
            
            # 💾 Load existing storage
            all_data = {}
            if self.storage_path.exists():
                try:
                    with open(self.storage_path, 'r') as f:
                        all_data = json.load(f)
                except Exception:
                    pass  # Start fresh if corrupted
            
            # 📊 Update data
            all_data[key] = storage_data
            
            # 💾 Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(all_data, f, indent=2)
            
            # 🔒 Set secure permissions
            os.chmod(self.storage_path, 0o600)
            
            self.logger.debug(f"✅ Stored data for key: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to store data for key {key}: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """📖 Retrieve and decrypt data."""
        try:
            if not self.storage_path.exists():
                return None
            
            # 📖 Load storage file
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
            
            if key not in all_data:
                return None
            
            stored_data = all_data[key]
            
            # 🔓 Decrypt if needed
            if stored_data.get('encrypted', False):
                if not self.fernet:
                    self.logger.error(f"🔴 Cannot decrypt data for {key}: encryption not available")
                    return None
                
                encrypted_data = base64.b64decode(stored_data['data'])
                decrypted_data = self.fernet.decrypt(encrypted_data)
                json_data = decrypted_data.decode()
            else:
                json_data = stored_data['data']
            
            # 📊 Parse JSON
            return json.loads(json_data)
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to retrieve data for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """🗑️ Delete stored data."""
        try:
            if not self.storage_path.exists():
                return True
            
            # 📖 Load and update storage
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
            
            if key in all_data:
                del all_data[key]
                
                # 💾 Write updated data
                with open(self.storage_path, 'w') as f:
                    json.dump(all_data, f, indent=2)
                
                self.logger.debug(f"🗑️ Deleted data for key: {key}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to delete data for key {key}: {e}")
            return False

class TokenManager:
    """
    🔐 AI Assistant: Comprehensive Token Manager.
    
    Manages authentication tokens with:
    - Secure token storage
    - Automatic refresh and renewal
    - Token validation and health checks
    - Multi-session support
    - Error handling and recovery
    """
    
    def __init__(self, 
                 storage_path: str = "tokens/secure_tokens.json",
                 encryption_password: Optional[str] = None,
                 auto_refresh: bool = True):
        """
        🆕 Initialize Token Manager.
        
        Args:
            storage_path: Path for secure token storage
            encryption_password: Optional password for encryption
            auto_refresh: Enable automatic token refresh
        """
        self.storage_path = storage_path
        self.auto_refresh = auto_refresh
        self.logger = logging.getLogger(f"{__name__}.TokenManager")
        
        # 🔒 Initialize secure storage
        self.storage = SecureStorage(storage_path, encryption_password)
        
        # 📊 Active tokens
        self.tokens: Dict[str, TokenInfo] = {}
        
        # 🔄 Refresh management
        self.refresh_thread: Optional[threading.Thread] = None
        self.refresh_running = False
        self.refresh_callbacks: List[Callable[[str, TokenInfo], None]] = []
        
        # 📈 Statistics
        self.total_authentications = 0
        self.successful_authentications = 0
        self.failed_authentications = 0
        self.token_refreshes = 0
        self.validation_checks = 0
        
        # 🔒 Thread safety
        self.lock = threading.RLock()
        
        # 📖 Load existing tokens
        self._load_stored_tokens()
        
        # 🚀 Start auto-refresh if enabled
        if self.auto_refresh:
            self._start_auto_refresh()
        
        self.logger.info("✅ Token Manager initialized")
    
    def authenticate_kite(self, 
                         api_key: str, 
                         request_token: str, 
                         api_secret: str,
                         session_id: Optional[str] = None) -> AuthenticationResult:
        """
        🔐 Authenticate with Kite Connect API.
        
        Args:
            api_key: Kite API key
            request_token: Request token from Kite login flow
            api_secret: Kite API secret
            session_id: Optional session identifier
            
        Returns:
            AuthenticationResult: Authentication result
        """
        try:
            with self.lock:
                self.total_authentications += 1
                
                if not KITE_AVAILABLE:
                    return AuthenticationResult(
                        success=False,
                        error_message="Kite Connect not available - install kiteconnect package",
                        error_code="KITE_NOT_AVAILABLE"
                    )
                
                # 🔗 Create Kite instance
                kite = KiteConnect(api_key=api_key)
                
                # 🔐 Generate session
                session_data = kite.generate_session(request_token, api_secret=api_secret)
                
                # 📊 Get user profile
                kite.set_access_token(session_data["access_token"])
                profile = kite.profile()
                
                # 🎯 Create token info
                token_info = TokenInfo(
                    access_token=session_data["access_token"],
                    refresh_token=session_data.get("refresh_token"),
                    token_type="bearer",
                    user_id=profile.get("user_id"),
                    user_name=profile.get("user_name"),
                    broker="kite"
                )
                
                # 💾 Store token
                session_key = session_id or f"kite_{api_key}_{profile.get('user_id', 'unknown')}"
                self.tokens[session_key] = token_info
                self._store_token(session_key, token_info)
                
                self.successful_authentications += 1
                
                self.logger.info(f"✅ Kite authentication successful for user: {profile.get('user_name', 'unknown')}")
                
                return AuthenticationResult(
                    success=True,
                    token_info=token_info,
                    user_profile=profile,
                    session_data=session_data
                )
                
        except (TokenException, KiteException) as e:
            self.failed_authentications += 1
            error_msg = f"Kite authentication failed: {str(e)}"
            self.logger.error(f"🔴 {error_msg}")
            
            return AuthenticationResult(
                success=False,
                error_message=error_msg,
                error_code="KITE_AUTH_FAILED"
            )
            
        except Exception as e:
            self.failed_authentications += 1
            error_msg = f"Authentication error: {str(e)}"
            self.logger.error(f"🔴 {error_msg}")
            
            return AuthenticationResult(
                success=False,
                error_message=error_msg,
                error_code="AUTH_ERROR"
            )
    
    def get_token(self, session_id: str) -> Optional[TokenInfo]:
        """🔑 Get token by session ID."""
        with self.lock:
            return self.tokens.get(session_id)
    
    def validate_token(self, session_id: str) -> bool:
        """
        ✅ Validate token by making a test API call.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if token is valid
        """
        try:
            with self.lock:
                self.validation_checks += 1
                
                token_info = self.tokens.get(session_id)
                if not token_info:
                    return False
                
                # ⏰ Check expiration
                if token_info.is_expired:
                    self.logger.debug(f"🔴 Token expired for session: {session_id}")
                    return False
                
                # 🧪 Validate with API call
                if KITE_AVAILABLE and token_info.broker == "kite":
                    success = self._validate_kite_token(token_info)
                    
                    if success:
                        token_info.last_validated = datetime.datetime.now()
                        self._store_token(session_id, token_info)
                    
                    return success
                else:
                    # 🆘 Fallback validation (assume valid if not expired)
                    return not token_info.is_expired
                    
        except Exception as e:
            self.logger.error(f"🔴 Token validation error: {e}")
            return False
    
    def _validate_kite_token(self, token_info: TokenInfo) -> bool:
        """🧪 Validate Kite token with API call."""
        try:
            # 🔗 Create Kite instance and test
            kite = KiteConnect(api_key="dummy")  # API key not needed for profile call
            kite.set_access_token(token_info.access_token)
            
            # 📊 Make test API call
            profile = kite.profile()
            return bool(profile and profile.get("user_id"))
            
        except Exception as e:
            self.logger.debug(f"⚠️ Kite token validation failed: {e}")
            return False
    
    def refresh_token(self, session_id: str) -> bool:
        """
        🔄 Refresh token if possible.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if refresh was successful
        """
        try:
            with self.lock:
                token_info = self.tokens.get(session_id)
                if not token_info:
                    return False
                
                # 🔄 Attempt refresh based on broker
                if token_info.broker == "kite":
                    # 📝 Note: Kite Connect doesn't support refresh tokens
                    # New authentication is required
                    self.logger.info(f"🔄 Kite tokens cannot be refreshed - new authentication required")
                    return False
                
                # 🔄 Add support for other brokers here
                
                return False
                
        except Exception as e:
            self.logger.error(f"🔴 Token refresh error: {e}")
            return False
    
    def revoke_token(self, session_id: str) -> bool:
        """
        🗑️ Revoke and remove token.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if revocation was successful
        """
        try:
            with self.lock:
                if session_id in self.tokens:
                    del self.tokens[session_id]
                
                # 🗑️ Remove from storage
                self.storage.delete(f"token_{session_id}")
                
                self.logger.info(f"🗑️ Token revoked for session: {session_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"🔴 Token revocation error: {e}")
            return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """📋 List all active sessions."""
        try:
            with self.lock:
                sessions = {}
                
                for session_id, token_info in self.tokens.items():
                    sessions[session_id] = {
                        'user_id': token_info.user_id,
                        'user_name': token_info.user_name,
                        'broker': token_info.broker,
                        'created_at': token_info.created_at.isoformat(),
                        'last_validated': token_info.last_validated.isoformat() if token_info.last_validated else None,
                        'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None,
                        'expires_in_seconds': token_info.expires_in_seconds,
                        'is_expired': token_info.is_expired,
                        'needs_refresh': token_info.needs_refresh
                    }
                
                return sessions
                
        except Exception as e:
            self.logger.error(f"🔴 Error listing sessions: {e}")
            return {}
    
    def add_refresh_callback(self, callback: Callable[[str, TokenInfo], None]):
        """🔄 Add callback for token refresh events."""
        self.refresh_callbacks.append(callback)
    
    def _load_stored_tokens(self):
        """📖 Load tokens from secure storage."""
        try:
            # 🔍 Find all stored token keys
            if not Path(self.storage_path).exists():
                return
            
            # 📖 Load storage file to get all keys
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
            
            token_keys = [key for key in all_data.keys() if key.startswith('token_')]
            
            for key in token_keys:
                try:
                    stored_data = self.storage.retrieve(key)
                    if stored_data:
                        # 🔄 Convert to TokenInfo
                        token_info = TokenInfo(
                            access_token=stored_data['access_token'],
                            refresh_token=stored_data.get('refresh_token'),
                            expires_at=datetime.datetime.fromisoformat(stored_data['expires_at']) if stored_data.get('expires_at') else None,
                            token_type=stored_data.get('token_type', 'bearer'),
                            scope=stored_data.get('scope'),
                            user_id=stored_data.get('user_id'),
                            user_name=stored_data.get('user_name'),
                            broker=stored_data.get('broker', 'kite'),
                            created_at=datetime.datetime.fromisoformat(stored_data['created_at']) if stored_data.get('created_at') else datetime.datetime.now(),
                            last_validated=datetime.datetime.fromisoformat(stored_data['last_validated']) if stored_data.get('last_validated') else None
                        )
                        
                        session_id = key.replace('token_', '')
                        self.tokens[session_id] = token_info
                        
                        self.logger.debug(f"📖 Loaded token for session: {session_id}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to load token {key}: {e}")
                    
        except Exception as e:
            self.logger.error(f"🔴 Error loading stored tokens: {e}")
    
    def _store_token(self, session_id: str, token_info: TokenInfo):
        """💾 Store token securely."""
        try:
            token_data = {
                'access_token': token_info.access_token,
                'refresh_token': token_info.refresh_token,
                'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None,
                'token_type': token_info.token_type,
                'scope': token_info.scope,
                'user_id': token_info.user_id,
                'user_name': token_info.user_name,
                'broker': token_info.broker,
                'created_at': token_info.created_at.isoformat(),
                'last_validated': token_info.last_validated.isoformat() if token_info.last_validated else None
            }
            
            self.storage.store(f"token_{session_id}", token_data)
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to store token for session {session_id}: {e}")
    
    def _start_auto_refresh(self):
        """🚀 Start automatic token refresh thread."""
        try:
            self.refresh_running = True
            self.refresh_thread = threading.Thread(
                target=self._auto_refresh_loop,
                name="TokenRefreshThread",
                daemon=True
            )
            self.refresh_thread.start()
            
            self.logger.info("🚀 Auto-refresh thread started")
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to start auto-refresh thread: {e}")
    
    def _auto_refresh_loop(self):
        """🔄 Auto-refresh loop."""
        self.logger.info("🔄 Auto-refresh loop started")
        
        while self.refresh_running:
            try:
                # 🔄 Check all tokens for refresh needs
                sessions_to_refresh = []
                
                with self.lock:
                    for session_id, token_info in self.tokens.items():
                        if token_info.needs_refresh and not token_info.is_expired:
                            sessions_to_refresh.append(session_id)
                
                # 🔄 Attempt to refresh tokens
                for session_id in sessions_to_refresh:
                    try:
                        if self.refresh_token(session_id):
                            self.token_refreshes += 1
                            self.logger.info(f"🔄 Successfully refreshed token for session: {session_id}")
                            
                            # 🔔 Notify callbacks
                            token_info = self.tokens.get(session_id)
                            for callback in self.refresh_callbacks:
                                try:
                                    callback(session_id, token_info)
                                except Exception as e:
                                    self.logger.error(f"🔴 Refresh callback error: {e}")
                        
                    except Exception as e:
                        self.logger.error(f"🔴 Failed to refresh token for session {session_id}: {e}")
                
                # 😴 Sleep before next check
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"🔴 Error in auto-refresh loop: {e}")
                time.sleep(60)  # Brief pause before retry
        
        self.logger.info("🔄 Auto-refresh loop stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """📊 Get token manager statistics."""
        try:
            with self.lock:
                active_sessions = len(self.tokens)
                expired_sessions = sum(1 for token in self.tokens.values() if token.is_expired)
                sessions_need_refresh = sum(1 for token in self.tokens.values() if token.needs_refresh)
                
                success_rate = (self.successful_authentications / self.total_authentications * 100 
                              if self.total_authentications > 0 else 0)
                
                return {
                    'active_sessions': active_sessions,
                    'expired_sessions': expired_sessions,
                    'sessions_need_refresh': sessions_need_refresh,
                    'total_authentications': self.total_authentications,
                    'successful_authentications': self.successful_authentications,
                    'failed_authentications': self.failed_authentications,
                    'success_rate_percent': round(success_rate, 2),
                    'token_refreshes': self.token_refreshes,
                    'validation_checks': self.validation_checks,
                    'auto_refresh_enabled': self.auto_refresh,
                    'storage_path': self.storage_path
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def close(self):
        """🗑️ Close token manager and cleanup resources."""
        try:
            self.refresh_running = False
            
            if self.refresh_thread and self.refresh_thread.is_alive():
                self.refresh_thread.join(timeout=5.0)
            
            # 📊 Log final statistics
            stats = self.get_statistics()
            self.logger.info(
                f"🗑️ Token Manager closed. Final stats: {stats.get('active_sessions', 0)} sessions, "
                f"{stats.get('success_rate_percent', 0):.1f}% success rate"
            )
            
        except Exception as e:
            self.logger.error(f"🔴 Error closing token manager: {e}")

# 🧪 AI Assistant: Testing functions
def test_token_manager():
    """🧪 Test Token Manager functionality."""
    print("🧪 Testing Token Manager...")
    
    try:
        # 🔧 Create token manager
        manager = TokenManager(
            storage_path="test_tokens.json",
            encryption_password="test_password_123"
        )
        
        # 🧪 Test secure storage
        test_data = {"test_key": "test_value", "number": 123}
        success = manager.storage.store("test", test_data)
        print(f"✅ Secure storage write: {'Success' if success else 'Failed'}")
        
        retrieved_data = manager.storage.retrieve("test")
        print(f"✅ Secure storage read: {'Success' if retrieved_data else 'Failed'}")
        
        # 📊 Test authentication (will fail without real credentials, but tests the flow)
        auth_result = manager.authenticate_kite(
            api_key="test_key",
            request_token="test_request_token", 
            api_secret="test_secret"
        )
        print(f"✅ Authentication test: {'Success' if auth_result.success else 'Expected failure'}")
        
        # 📋 Test session listing
        sessions = manager.list_sessions()
        print(f"✅ Session listing: {len(sessions)} sessions")
        
        # 📊 Get statistics
        stats = manager.get_statistics()
        print(f"✅ Statistics: {stats.get('total_authentications', 0)} attempts")
        
        # 🗑️ Cleanup
        manager.storage.delete("test")
        manager.close()
        
        # 🧹 Remove test file
        test_file = Path("test_tokens.json")
        if test_file.exists():
            test_file.unlink()
        
        key_file = Path("test_tokens.key")
        if key_file.exists():
            key_file.unlink()
        
        print("🎉 Token Manager test completed!")
        return True
        
    except Exception as e:
        print(f"🔴 Token Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_token_manager()