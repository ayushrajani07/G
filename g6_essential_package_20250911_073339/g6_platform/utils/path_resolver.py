#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗂️ Path Resolver - G6 Platform v3.0
Comprehensive path management and directory structure creation.

Restructured from: path_resolver_complete.py
Features:
- Cross-platform path resolution
- Automatic directory structure creation
- Path validation and sanitization
- Temporary file management
- Backup and archive organization
- Configuration file discovery
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
import platform

logger = logging.getLogger(__name__)

class PathResolver:
    """
    🗂️ Advanced path resolution and directory management system.
    
    Provides cross-platform path management with automatic directory
    creation, validation, and organization.
    """
    
    # Default directory structure
    DEFAULT_STRUCTURE = {
        'data': {
            'csv': {},
            'archive': {},
            'cache': {},
            'temp': {}
        },
        'logs': {
            'platform': {},
            'collectors': {},
            'storage': {},
            'monitoring': {}
        },
        'config': {
            'templates': {},
            'backup': {}
        },
        'tokens': {},
        'backup': {
            'config': {},
            'data': {},
            'logs': {}
        }
    }
    
    def __init__(self, 
                 base_path: Union[str, Path] = None,
                 create_structure: bool = True,
                 validate_permissions: bool = True):
        """
        Initialize path resolver.
        
        Args:
            base_path: Base directory path (uses cwd if None)
            create_structure: Automatically create directory structure
            validate_permissions: Validate directory permissions
        """
        self.base_path = Path(base_path or os.getcwd()).resolve()
        self.create_structure = create_structure
        self.validate_permissions = validate_permissions
        
        # Platform-specific settings
        self.platform = platform.system().lower()
        self.is_windows = self.platform == 'windows'
        self.is_unix = self.platform in ['linux', 'darwin']
        
        # Path mappings
        self._path_cache: Dict[str, Path] = {}
        self._created_paths: List[Path] = []
        
        # Initialize directory structure
        if create_structure:
            self.create_directory_structure()
        
        logger.info(f"🗂️ Path resolver initialized: {self.base_path}")
        logger.info(f"🖥️ Platform: {self.platform}")
    
    def create_directory_structure(self, structure: Dict = None) -> List[Path]:
        """
        Create directory structure.
        
        Args:
            structure: Directory structure dict (uses default if None)
            
        Returns:
            List of created directory paths
        """
        structure = structure or self.DEFAULT_STRUCTURE
        created_paths = []
        
        def create_recursive(current_path: Path, struct: Dict):
            """Recursively create directory structure."""
            for name, subdirs in struct.items():
                dir_path = current_path / name
                
                if self._create_directory(dir_path):
                    created_paths.append(dir_path)
                    self._created_paths.append(dir_path)
                
                if isinstance(subdirs, dict) and subdirs:
                    create_recursive(dir_path, subdirs)
        
        try:
            # Ensure base path exists
            if self._create_directory(self.base_path):
                created_paths.append(self.base_path)
            
            # Create structure
            create_recursive(self.base_path, structure)
            
            logger.info(f"✅ Created {len(created_paths)} directories")
            return created_paths
            
        except Exception as e:
            logger.error(f"🔴 Failed to create directory structure: {e}")
            return created_paths
    
    def _create_directory(self, path: Path) -> bool:
        """
        Create a single directory with error handling.
        
        Args:
            path: Directory path to create
            
        Returns:
            True if created or already exists
        """
        try:
            if path.exists():
                if not path.is_dir():
                    logger.error(f"🔴 Path exists but is not a directory: {path}")
                    return False
                return True
            
            # Create directory with parents
            path.mkdir(parents=True, exist_ok=True)
            
            # Set permissions (Unix only)
            if self.is_unix:
                path.chmod(0o755)
            
            # Validate permissions if enabled
            if self.validate_permissions:
                if not self._validate_directory_permissions(path):
                    logger.warning(f"⚠️ Limited permissions for directory: {path}")
            
            logger.debug(f"📁 Created directory: {path}")
            return True
            
        except PermissionError:
            logger.error(f"🔴 Permission denied creating directory: {path}")
            return False
        except Exception as e:
            logger.error(f"🔴 Failed to create directory {path}: {e}")
            return False
    
    def _validate_directory_permissions(self, path: Path) -> bool:
        """
        Validate directory permissions.
        
        Args:
            path: Directory path to validate
            
        Returns:
            True if permissions are adequate
        """
        try:
            # Test read permission
            if not os.access(path, os.R_OK):
                return False
            
            # Test write permission
            if not os.access(path, os.W_OK):
                return False
            
            # Test execute permission (needed for directory traversal)
            if not os.access(path, os.X_OK):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to validate permissions for {path}: {e}")
            return False
    
    def get_path(self, 
                path_type: str,
                filename: str = None,
                create_if_missing: bool = True) -> Path:
        """
        Get resolved path for a specific type.
        
        Args:
            path_type: Type of path (data, logs, config, etc.)
            filename: Optional filename to append
            create_if_missing: Create directory if it doesn't exist
            
        Returns:
            Resolved path
        """
        # Parse path type (e.g., "data.csv", "logs.platform")
        path_parts = path_type.split('.')
        
        # Start from base path
        resolved_path = self.base_path
        
        # Navigate through path parts
        for part in path_parts:
            resolved_path = resolved_path / part
        
        # Create directory if requested and doesn't exist
        if create_if_missing and not resolved_path.exists():
            self._create_directory(resolved_path)
        
        # Add filename if provided
        if filename:
            resolved_path = resolved_path / filename
        
        # Cache the path
        cache_key = f"{path_type}:{filename or ''}"
        self._path_cache[cache_key] = resolved_path
        
        return resolved_path
    
    def get_data_path(self, filename: str = None, subdir: str = "csv") -> Path:
        """Get path for data files."""
        return self.get_path(f"data.{subdir}", filename)
    
    def get_log_path(self, filename: str = None, subdir: str = "platform") -> Path:
        """Get path for log files."""
        return self.get_path(f"logs.{subdir}", filename)
    
    def get_config_path(self, filename: str = None) -> Path:
        """Get path for configuration files."""
        return self.get_path("config", filename)
    
    def get_temp_path(self, filename: str = None) -> Path:
        """Get path for temporary files."""
        return self.get_path("data.temp", filename)
    
    def get_backup_path(self, path_type: str = "data", filename: str = None) -> Path:
        """Get path for backup files."""
        return self.get_path(f"backup.{path_type}", filename)
    
    def get_archive_path(self, filename: str = None) -> Path:
        """Get path for archived files."""
        return self.get_path("data.archive", filename)
    
    def create_timestamped_path(self, 
                              base_path_type: str,
                              prefix: str = "",
                              suffix: str = "",
                              timestamp_format: str = "%Y%m%d_%H%M%S") -> Path:
        """
        Create timestamped path.
        
        Args:
            base_path_type: Base path type
            prefix: Filename prefix
            suffix: Filename suffix
            timestamp_format: Timestamp format string
            
        Returns:
            Timestamped path
        """
        timestamp = datetime.now().strftime(timestamp_format)
        filename = f"{prefix}{timestamp}{suffix}"
        return self.get_path(base_path_type, filename)
    
    def find_config_file(self, 
                        filename: str,
                        search_paths: List[str] = None) -> Optional[Path]:
        """
        Find configuration file in multiple locations.
        
        Args:
            filename: Configuration filename
            search_paths: Additional search paths
            
        Returns:
            Path to found config file or None
        """
        search_locations = [
            self.get_config_path(),  # config directory
            self.base_path,          # base directory
            Path.cwd(),              # current working directory
            Path.home(),             # user home directory
        ]
        
        # Add custom search paths
        if search_paths:
            search_locations.extend([Path(p) for p in search_paths])
        
        for location in search_locations:
            config_path = location / filename
            if config_path.exists() and config_path.is_file():
                logger.info(f"📄 Found config file: {config_path}")
                return config_path
        
        logger.warning(f"⚠️ Config file not found: {filename}")
        return None
    
    def create_temp_file(self, 
                        prefix: str = "g6_temp_",
                        suffix: str = "",
                        directory: str = None) -> Path:
        """
        Create temporary file.
        
        Args:
            prefix: Filename prefix
            suffix: Filename suffix
            directory: Directory for temp file (uses temp dir if None)
            
        Returns:
            Path to temporary file
        """
        try:
            temp_dir = directory or self.get_temp_path()
            
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(
                prefix=prefix,
                suffix=suffix,
                dir=str(temp_dir)
            )
            
            # Close file descriptor
            os.close(fd)
            
            temp_path = Path(temp_path)
            logger.debug(f"📄 Created temporary file: {temp_path}")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"🔴 Failed to create temporary file: {e}")
            raise
    
    def create_temp_directory(self, 
                            prefix: str = "g6_temp_",
                            directory: str = None) -> Path:
        """
        Create temporary directory.
        
        Args:
            prefix: Directory prefix
            directory: Parent directory (uses temp dir if None)
            
        Returns:
            Path to temporary directory
        """
        try:
            temp_dir = directory or self.get_temp_path()
            
            # Create temporary directory
            temp_path = tempfile.mkdtemp(
                prefix=prefix,
                dir=str(temp_dir)
            )
            
            temp_path = Path(temp_path)
            logger.debug(f"📁 Created temporary directory: {temp_path}")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"🔴 Failed to create temporary directory: {e}")
            raise
    
    def backup_file(self, 
                   source_path: Union[str, Path],
                   backup_type: str = "data") -> Optional[Path]:
        """
        Create backup of a file.
        
        Args:
            source_path: Source file path
            backup_type: Type of backup (data, config, logs)
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            source_path = Path(source_path)
            
            if not source_path.exists():
                logger.error(f"🔴 Source file not found: {source_path}")
                return None
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = self.get_backup_path(backup_type, backup_filename)
            
            # Copy file to backup location
            shutil.copy2(source_path, backup_path)
            
            logger.info(f"📋 File backed up: {source_path} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"🔴 Failed to backup file {source_path}: {e}")
            return None
    
    def archive_directory(self, 
                         source_dir: Union[str, Path],
                         archive_name: str = None) -> Optional[Path]:
        """
        Archive a directory.
        
        Args:
            source_dir: Source directory path
            archive_name: Archive filename (auto-generated if None)
            
        Returns:
            Path to archive file or None if failed
        """
        try:
            source_dir = Path(source_dir)
            
            if not source_dir.exists() or not source_dir.is_dir():
                logger.error(f"🔴 Source directory not found: {source_dir}")
                return None
            
            # Generate archive name if not provided
            if not archive_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"{source_dir.name}_{timestamp}"
            
            # Create archive path
            archive_path = self.get_archive_path(f"{archive_name}.tar.gz")
            
            # Create archive
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'gztar',
                str(source_dir.parent),
                str(source_dir.name)
            )
            
            logger.info(f"📦 Directory archived: {source_dir} -> {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"🔴 Failed to archive directory {source_dir}: {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of temp files to keep
            
        Returns:
            Number of files cleaned up
        """
        try:
            temp_dir = self.get_temp_path()
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            cleaned_count = 0
            
            for file_path in temp_dir.glob("*"):
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                        
                        cleaned_count += 1
                        logger.debug(f"🗑️ Cleaned up temp file: {file_path}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clean up {file_path}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} temporary files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"🔴 Failed to cleanup temp files: {e}")
            return 0
    
    def get_path_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive path information.
        
        Args:
            path: Path to analyze
            
        Returns:
            Dictionary with path information
        """
        try:
            path = Path(path)
            
            info = {
                'path': str(path),
                'absolute_path': str(path.resolve()),
                'exists': path.exists(),
                'is_file': path.is_file() if path.exists() else None,
                'is_directory': path.is_dir() if path.exists() else None,
                'parent': str(path.parent),
                'name': path.name,
                'stem': path.stem,
                'suffix': path.suffix,
                'platform': self.platform
            }
            
            if path.exists():
                stat = path.stat()
                info.update({
                    'size_bytes': stat.st_size,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'permissions': oct(stat.st_mode)[-3:],
                    'readable': os.access(path, os.R_OK),
                    'writable': os.access(path, os.W_OK),
                    'executable': os.access(path, os.X_OK)
                })
            
            return info
            
        except Exception as e:
            logger.error(f"🔴 Failed to get path info for {path}: {e}")
            return {'error': str(e)}
    
    def get_directory_size(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Calculate directory size recursively.
        
        Args:
            directory: Directory path
            
        Returns:
            Size information dictionary
        """
        try:
            directory = Path(directory)
            
            if not directory.exists() or not directory.is_dir():
                return {'error': 'Directory does not exist'}
            
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
                elif item.is_dir():
                    dir_count += 1
            
            return {
                'directory': str(directory),
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'total_size_gb': total_size / (1024 * 1024 * 1024),
                'file_count': file_count,
                'directory_count': dir_count
            }
            
        except Exception as e:
            logger.error(f"🔴 Failed to calculate directory size for {directory}: {e}")
            return {'error': str(e)}
    
    def list_directory_contents(self, 
                              directory: Union[str, Path],
                              pattern: str = "*",
                              recursive: bool = False) -> List[Dict[str, Any]]:
        """
        List directory contents with details.
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            List of file/directory information
        """
        try:
            directory = Path(directory)
            
            if not directory.exists() or not directory.is_dir():
                return []
            
            contents = []
            glob_method = directory.rglob if recursive else directory.glob
            
            for item in glob_method(pattern):
                item_info = {
                    'name': item.name,
                    'path': str(item.relative_to(directory)),
                    'absolute_path': str(item),
                    'is_file': item.is_file(),
                    'is_directory': item.is_dir(),
                    'size_bytes': item.stat().st_size if item.is_file() else None,
                    'modified_time': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                contents.append(item_info)
            
            return sorted(contents, key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"🔴 Failed to list directory contents for {directory}: {e}")
            return []
    
    def get_resolver_stats(self) -> Dict[str, Any]:
        """Get path resolver statistics."""
        return {
            'base_path': str(self.base_path),
            'platform': self.platform,
            'created_paths_count': len(self._created_paths),
            'cached_paths_count': len(self._path_cache),
            'created_paths': [str(p) for p in self._created_paths],
            'structure_created': self.create_structure,
            'permissions_validated': self.validate_permissions
        }