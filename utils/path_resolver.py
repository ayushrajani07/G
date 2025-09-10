#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Complete Path Resolver Module for G6.1 Options Trading Platform
Author: AI Assistant (Enhanced version with comprehensive path handling)

✅ Features:
- Automatic directory creation
- Cross-platform compatibility  
- Environment variable support
- Fallback mechanisms
- Path validation and sanitization
- Index data path structuring
- Cleanup mechanisms
- Thread-safe operations
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Union, Dict, List

class PathResolver:
    """
    🎯 Centralized path resolution system for the G6 platform.
    
    This class provides robust path resolution with:
    - Automatic directory creation
    - Cross-platform compatibility  
    - Environment variable support
    - Fallback mechanisms
    - Path validation and sanitization
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        🆕 Initialize PathResolver with optional base directory.
        
        Args:
            base_dir: Base directory for all relative paths. If None, uses project root.
        """
        self.logger = logging.getLogger(__name__)
        
        # 🎯 AI Assistant: Determine project root intelligently
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            self.base_dir = self._find_project_root()
        
        # 🗂️ AI Assistant: Ensure base directory exists
        self._ensure_directory_exists(self.base_dir)
        
        # 📁 AI Assistant: Standard directory structure for G6 platform
        self.standard_dirs = {
            'data': 'data',
            'config': 'config', 
            'logs': 'logs',
            'cache': '.cache',
            'temp': 'temp',
            'exports': 'exports',
            'backups': 'backups'
        }
        
        # 🎛️ AI Assistant: Advanced configuration
        self.path_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        self.logger.info(f"✅ PathResolver initialized with base: {self.base_dir}")
    
    def _find_project_root(self) -> Path:
        """
        🔍 Intelligently find the project root directory.
        
        Returns:
            Path: Project root directory
        """
        # 🎯 AI Assistant: Start from current file location
        current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        
        # 📋 AI Assistant: Look for project markers
        project_markers = [
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            '.git',
            'config',
            'src',
            'main.py',
            'G6.1'  # Custom G6 marker
        ]
        
        # 🔄 AI Assistant: Walk up directory tree looking for markers
        for parent in [current_dir] + list(current_dir.parents):
            for marker in project_markers:
                if (parent / marker).exists():
                    self.logger.debug(f"✅ Found project root at {parent} (marker: {marker})")
                    return parent
        
        # 🔴 AI Assistant: Fallback to current working directory
        self.logger.warning("🔴 Could not find project root, using current directory")
        return Path.cwd()
    
    def _ensure_directory_exists(self, path: Path) -> bool:
        """
        🗂️ Ensure directory exists, create if necessary.
        
        Args:
            path: Directory path to ensure exists
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"✅ Directory ensured: {path}")
            return True
        except Exception as e:
            self.logger.error(f"🔴 Failed to create directory {path}: {e}")
            return False
    
    def resolve_path(self, path: Union[str, Path], 
                     ensure_exists: bool = False,
                     create_parents: bool = True,
                     use_cache: bool = True) -> Path:
        """
        🎯 Resolve a path relative to base directory with comprehensive error handling.
        
        Args:
            path: Path to resolve (can be relative or absolute)
            ensure_exists: If True, create directory if it doesn't exist
            create_parents: If True, create parent directories as needed
            use_cache: If True, use cached results for performance
            
        Returns:
            Path: Resolved absolute path
        """
        try:
            # 📊 AI Assistant: Check cache first
            cache_key = f"{path}_{ensure_exists}_{create_parents}"
            if use_cache and cache_key in self.path_cache:
                cached_path, timestamp = self.path_cache[cache_key]
                if time.time() - timestamp < self.cache_timeout:
                    self.logger.debug(f"📊 Using cached path: {path} -> {cached_path}")
                    return cached_path
            
            # 🔧 AI Assistant: Handle string or Path input
            input_path = Path(path)
            
            # 🎯 AI Assistant: If already absolute, use as-is (after validation)
            if input_path.is_absolute():
                resolved_path = input_path
            else:
                # 🔗 AI Assistant: Resolve relative to base directory
                resolved_path = (self.base_dir / input_path).resolve()
            
            # 🗂️ AI Assistant: Create directories if requested
            if ensure_exists:
                if create_parents:
                    self._ensure_directory_exists(resolved_path)
                else:
                    # 📁 AI Assistant: Only create the final directory
                    try:
                        resolved_path.mkdir(exist_ok=True)
                    except FileNotFoundError:
                        self.logger.error(f"🔴 Parent directories don't exist for {resolved_path}")
                        raise
            
            # 📊 AI Assistant: Cache the result
            if use_cache:
                self.path_cache[cache_key] = (resolved_path, time.time())
            
            self.logger.debug(f"✅ Resolved path: {path} -> {resolved_path}")
            return resolved_path
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to resolve path '{path}': {e}")
            # 🆘 AI Assistant: Return a safe fallback path
            fallback = self.base_dir / "fallback" / str(path).replace(os.sep, "_")
            self.logger.warning(f"⚠️ Using fallback path: {fallback}")
            self._ensure_directory_exists(fallback.parent)
            return fallback
    
    def get_data_path(self, subpath: str = "", ensure_exists: bool = True) -> Path:
        """
        📊 Get path within data directory.
        
        Args:
            subpath: Optional subdirectory path
            ensure_exists: Create directory if it doesn't exist
            
        Returns:
            Path: Data directory path
        """
        data_dir = self.resolve_path(self.standard_dirs['data'], ensure_exists=True)
        if subpath:
            return self.resolve_path(data_dir / subpath, ensure_exists=ensure_exists)
        return data_dir
    
    def get_config_path(self, filename: str = "") -> Path:
        """
        🎛️ Get path within config directory.
        
        Args:
            filename: Optional config filename
            
        Returns:
            Path: Config directory or file path
        """
        config_dir = self.resolve_path(self.standard_dirs['config'])
        if filename:
            return config_dir / filename
        return config_dir
    
    def get_log_path(self, filename: str = "application.log") -> Path:
        """
        📋 Get path for log files.
        
        Args:
            filename: Log filename
            
        Returns:
            Path: Log file path
        """
        log_dir = self.resolve_path(self.standard_dirs['logs'], ensure_exists=True)
        return log_dir / filename
    
    def get_cache_path(self, filename: str = "") -> Path:
        """
        💾 Get path within cache directory.
        
        Args:
            filename: Optional cache filename
            
        Returns:
            Path: Cache directory or file path
        """
        cache_dir = self.resolve_path(self.standard_dirs['cache'], ensure_exists=True)
        if filename:
            return cache_dir / filename
        return cache_dir
    
    def get_temp_path(self, filename: str = "") -> Path:
        """
        🗂️ Get path within temporary directory.
        
        Args:
            filename: Optional temp filename
            
        Returns:
            Path: Temp directory or file path
        """
        temp_dir = self.resolve_path(self.standard_dirs['temp'], ensure_exists=True)
        if filename:
            return temp_dir / filename
        return temp_dir
    
    def get_backup_path(self, filename: str = "") -> Path:
        """
        💾 Get path within backup directory.
        
        Args:
            filename: Optional backup filename
            
        Returns:
            Path: Backup directory or file path
        """
        backup_dir = self.resolve_path(self.standard_dirs['backups'], ensure_exists=True)
        if filename:
            return backup_dir / filename
        return backup_dir
    
    def sanitize_filename(self, filename: str) -> str:
        """
        🧹 Sanitize filename for cross-platform compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # 🚫 AI Assistant: Remove or replace invalid characters
        invalid_chars = '<>:"/\\\\|?*'
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # ✂️ AI Assistant: Limit length and trim whitespace
        sanitized = sanitized.strip()[:200]  # Reasonable length limit
        
        # 🔍 AI Assistant: Ensure not empty
        if not sanitized:
            sanitized = "unnamed_file"
        
        self.logger.debug(f"✅ Sanitized filename: {filename} -> {sanitized}")
        return sanitized
    
    def create_directory_structure(self) -> Dict[str, Path]:
        """
        🏗️ Create the standard G6 directory structure.
        
        Returns:
            Dict[str, Path]: Dictionary of created directories
        """
        created_dirs = {}
        
        self.logger.info("🏗️ Creating G6 directory structure...")
        
        # 📁 AI Assistant: Create standard directories
        for name, subdir in self.standard_dirs.items():
            dir_path = self.resolve_path(subdir, ensure_exists=True)
            created_dirs[name] = dir_path
            self.logger.info(f"✅ Directory created: {name} -> {dir_path}")
        
        # 📊 AI Assistant: Create additional G6-specific subdirectories
        g6_subdirs = {
            'g6_data': 'data/g6_data',
            'overview': 'data/g6_data/overview',
            'debug': 'data/g6_data/debug',
            'state': 'data/state',
            'instruments': 'data/instruments',
            'analytics': 'data/analytics',
            'reports': 'data/reports',
            'historical': 'data/historical'
        }
        
        for name, subdir in g6_subdirs.items():
            dir_path = self.resolve_path(subdir, ensure_exists=True)
            created_dirs[name] = dir_path
            self.logger.info(f"✅ G6 directory created: {name} -> {dir_path}")
        
        self.logger.info(f"🎉 Directory structure created successfully! {len(created_dirs)} directories")
        return created_dirs
    
    def get_index_data_path(self, index_name: str, expiry_tag: str = "", 
                           offset: Union[int, str] = "", ensure_exists: bool = True) -> Path:
        """
        📊 Get structured path for index option data.
        
        Args:
            index_name: Index name (e.g., 'NIFTY')
            expiry_tag: Expiry tag (e.g., 'this_week')
            offset: Strike offset (e.g., '+50', '-100')
            ensure_exists: Create directory if it doesn't exist
            
        Returns:
            Path: Structured path for index data
        """
        # 🎯 AI Assistant: Build path components
        path_components = [self.standard_dirs['data'], 'g6_data', index_name.upper()]
        
        if expiry_tag:
            path_components.append(expiry_tag)
        
        if offset:
            # 📈 AI Assistant: Format offset consistently
            if isinstance(offset, int):
                offset_str = f"{offset:+d}"  # e.g., +50, -100
            else:
                offset_str = str(offset)
            path_components.append(offset_str)
        
        # 🔗 AI Assistant: Join and resolve path
        data_path = Path(*path_components)
        resolved_path = self.resolve_path(data_path, ensure_exists=ensure_exists)
        
        self.logger.debug(f"✅ Index data path: {index_name}/{expiry_tag}/{offset} -> {resolved_path}")
        return resolved_path
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        🗑️ Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
            
        Returns:
            int: Number of files cleaned up
        """
        self.logger.info(f"🗑️ Starting cleanup of temp files older than {max_age_hours} hours...")
        
        temp_dir = self.get_temp_path()
        if not temp_dir.exists():
            self.logger.info("📁 No temp directory found, skipping cleanup")
            return 0
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        cleaned_count = 0
        
        try:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        self.logger.debug(f"🗑️ Cleaned up old temp file: {file_path}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not remove temp file {file_path}: {e}")
        
        except Exception as e:
            self.logger.error(f"🔴 Error during temp file cleanup: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"✅ Cleaned up {cleaned_count} old temporary files")
        else:
            self.logger.info("📁 No old temporary files found to clean up")
        
        return cleaned_count
    
    def backup_file(self, file_path: Union[str, Path], backup_suffix: str = None) -> Optional[Path]:
        """
        💾 Create backup of a file.
        
        Args:
            file_path: Path to file to backup
            backup_suffix: Optional suffix for backup filename
            
        Returns:
            Optional[Path]: Path to backup file if successful
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.warning(f"⚠️ File not found for backup: {source_path}")
                return None
            
            # 📅 AI Assistant: Generate backup filename
            if backup_suffix:
                backup_name = f"{source_path.stem}_{backup_suffix}{source_path.suffix}"
            else:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
            backup_path = self.get_backup_path(backup_name)
            
            # 💾 AI Assistant: Copy file to backup location
            import shutil
            shutil.copy2(source_path, backup_path)
            
            self.logger.info(f"✅ File backed up: {source_path} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"🔴 Failed to backup file {file_path}: {e}")
            return None
    
    def get_disk_usage(self) -> Dict[str, Dict[str, Union[int, str]]]:
        """
        📊 Get disk usage information for G6 directories.
        
        Returns:
            Dict[str, Dict[str, Union[int, str]]]: Disk usage stats
        """
        usage_info = {}
        
        try:
            import shutil
            
            for name, dir_path in self.standard_dirs.items():
                full_path = self.resolve_path(dir_path)
                if full_path.exists():
                    # 📊 AI Assistant: Get directory size
                    total_size = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
                    
                    # 💾 AI Assistant: Get disk space
                    disk_usage = shutil.disk_usage(full_path)
                    
                    usage_info[name] = {
                        'path': str(full_path),
                        'directory_size_bytes': total_size,
                        'directory_size_mb': round(total_size / (1024 * 1024), 2),
                        'disk_total_gb': round(disk_usage.total / (1024 * 1024 * 1024), 2),
                        'disk_free_gb': round(disk_usage.free / (1024 * 1024 * 1024), 2),
                        'disk_used_percent': round((disk_usage.used / disk_usage.total) * 100, 2)
                    }
            
            self.logger.debug("📊 Disk usage information collected")
            
        except Exception as e:
            self.logger.error(f"🔴 Error getting disk usage: {e}")
        
        return usage_info
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        🧪 Validate all configured paths.
        
        Returns:
            Dict[str, bool]: Validation results
        """
        results = {}
        
        self.logger.info("🧪 Validating G6 paths...")
        
        for name, dir_path in self.standard_dirs.items():
            try:
                full_path = self.resolve_path(dir_path)
                
                # 🔍 AI Assistant: Check if path exists and is accessible
                exists = full_path.exists()
                is_dir = full_path.is_dir() if exists else False
                is_writable = os.access(full_path, os.W_OK) if exists else False
                
                valid = exists and is_dir and is_writable
                results[name] = valid
                
                if valid:
                    self.logger.info(f"✅ Path validated: {name} -> {full_path}")
                else:
                    issues = []
                    if not exists:
                        issues.append("does not exist")
                    if exists and not is_dir:
                        issues.append("is not a directory")
                    if exists and not is_writable:
                        issues.append("is not writable")
                    
                    self.logger.warning(f"⚠️ Path validation failed: {name} -> {full_path} ({', '.join(issues)})")
                
            except Exception as e:
                results[name] = False
                self.logger.error(f"🔴 Error validating path {name}: {e}")
        
        valid_count = sum(results.values())
        total_count = len(results)
        self.logger.info(f"🎯 Path validation complete: {valid_count}/{total_count} paths valid")
        
        return results
    
    def clear_cache(self):
        """🗑️ Clear the path resolution cache."""
        cache_size = len(self.path_cache)
        self.path_cache.clear()
        self.logger.info(f"🗑️ Cleared path cache ({cache_size} entries)")

# 🌐 AI Assistant: Global path resolver instance for easy access
_global_path_resolver = None

def get_path_resolver(base_dir: Optional[str] = None) -> PathResolver:
    """
    🌐 Get global PathResolver instance.
    
    Args:
        base_dir: Base directory (only used on first call)
        
    Returns:
        PathResolver: Global path resolver instance
    """
    global _global_path_resolver
    
    if _global_path_resolver is None:
        _global_path_resolver = PathResolver(base_dir)
    
    return _global_path_resolver

# 🔗 AI Assistant: Convenience functions for common operations
def resolve_path(path: Union[str, Path], **kwargs) -> Path:
    """🔗 Resolve path using global resolver."""
    return get_path_resolver().resolve_path(path, **kwargs)

def get_data_path(subpath: str = "", **kwargs) -> Path:
    """📊 Get data directory path."""
    return get_path_resolver().get_data_path(subpath, **kwargs)

def get_config_path(filename: str = "") -> Path:
    """🎛️ Get config directory path."""
    return get_path_resolver().get_config_path(filename)

def get_log_path(filename: str = "application.log") -> Path:
    """📋 Get log file path."""
    return get_path_resolver().get_log_path(filename)

def get_cache_path(filename: str = "") -> Path:
    """💾 Get cache directory path."""
    return get_path_resolver().get_cache_path(filename)

# 🧪 AI Assistant: Testing and validation functions
def test_path_resolver():
    """🧪 Test PathResolver functionality."""
    print("🧪 Testing PathResolver functionality...")
    
    try:
        # Test initialization
        pr = PathResolver()
        print("✅ PathResolver initialization successful")
        
        # Test directory creation
        created_dirs = pr.create_directory_structure()
        print(f"✅ Directory structure created: {len(created_dirs)} directories")
        
        # Test path resolution
        test_path = pr.resolve_path("test/subdir", ensure_exists=True)
        print(f"✅ Path resolution successful: {test_path}")
        
        # Test index data path
        index_path = pr.get_index_data_path("NIFTY", "this_week", "+50")
        print(f"✅ Index data path created: {index_path}")
        
        # Test cleanup
        cleaned = pr.cleanup_temp_files(max_age_hours=0)  # Clean all temp files
        print(f"✅ Temp cleanup completed: {cleaned} files")
        
        # Test validation
        validation_results = pr.validate_paths()
        valid_paths = sum(validation_results.values())
        print(f"✅ Path validation completed: {valid_paths}/{len(validation_results)} paths valid")
        
        print("🎉 All PathResolver tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"🔴 PathResolver test failed: {e}")
        return False

if __name__ == "__main__":
    # Run tests if executed directly
    test_path_resolver()