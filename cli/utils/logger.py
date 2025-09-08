"""
Enhanced logging module using Loguru for CLI applications.
Provides structured, colored, and file-based logging with automatic rotation.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from enum import Enum


class LogLevel(Enum):
    """Log levels matching Loguru's levels."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "CRITICAL"


class CLILogger:
    """Enhanced CLI logger using Loguru with Docker-specific formatting."""
    
    def __init__(self, 
                 log_file: Optional[str] = None,
                 log_level: str = "INFO",
                 show_timestamps: bool = False,
                 colorize: bool = True):
        """
        Initialize the CLI logger.
        
        Args:
            log_file: Path to log file (optional)
            log_level: Minimum log level to display
            show_timestamps: Whether to show timestamps in console output
            colorize: Whether to use colored output
        """
        # Remove default handler
        logger.remove()
        
        # Console handler with custom formatting
        console_format = self._get_console_format(show_timestamps)
        logger.add(
            sys.stderr,
            format=console_format,
            level=log_level,
            colorize=colorize,
            backtrace=True,
            diagnose=True
        )
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level="DEBUG",
                rotation="10 MB",
                retention="7 days",
                compression="zip",
                backtrace=True,
                diagnose=True
            )
    
    def _get_console_format(self, show_timestamps: bool) -> str:
        """Get console format string."""
        if show_timestamps:
            return "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        else:
            return "<level>{level: <8}</level> | <level>{message}</level>"
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        logger.bind(**kwargs).info(message)
    
    def success(self, message: str, **kwargs) -> None:
        """Log a success message."""
        logger.bind(**kwargs).success(message)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        logger.bind(**kwargs).warning(message)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        logger.bind(**kwargs).error(message)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        logger.bind(**kwargs).debug(message)
    
    def trace(self, message: str, **kwargs) -> None:
        """Log a trace message."""
        logger.bind(**kwargs).trace(message)
    
    def docker_command(self, command: str, container: str, **kwargs) -> None:
        """Log Docker command execution."""
        logger.bind(
            docker_command=command,
            container=container,
            **kwargs
        ).info(f"Executing Docker command: {command} on {container}")
    
    def docker_success(self, command: str, container: str, **kwargs) -> None:
        """Log successful Docker command."""
        logger.bind(
            docker_command=command,
            container=container,
            **kwargs
        ).success(f"Docker command succeeded: {command} on {container}")
    
    def docker_error(self, command: str, container: str, error: str, **kwargs) -> None:
        """Log failed Docker command."""
        logger.bind(
            docker_command=command,
            container=container,
            error=error,
            **kwargs
        ).error(f"Docker command failed: {command} on {container} - {error}")
    
    def backup_start(self, backup_name: str, destination: str, **kwargs) -> None:
        """Log backup start."""
        logger.bind(
            backup_name=backup_name,
            destination=destination,
            **kwargs
        ).info(f"Starting backup: {backup_name} to {destination}")
    
    def backup_success(self, backup_name: str, destination: str, size: Optional[str] = None, **kwargs) -> None:
        """Log successful backup."""
        size_info = f" ({size})" if size else ""
        logger.bind(
            backup_name=backup_name,
            destination=destination,
            size=size,
            **kwargs
        ).success(f"Backup completed: {backup_name} to {destination}{size_info}")
    
    def backup_error(self, backup_name: str, destination: str, error: str, **kwargs) -> None:
        """Log backup error."""
        logger.bind(
            backup_name=backup_name,
            destination=destination,
            error=error,
            **kwargs
        ).error(f"Backup failed: {backup_name} to {destination} - {error}")
    
    def container_status(self, container: str, status: str, **kwargs) -> None:
        """Log container status."""
        logger.bind(
            container=container,
            status=status,
            **kwargs
        ).info(f"Container {container} status: {status}")
    
    def exception(self, message: str, exception: Exception, **kwargs) -> None:
        """Log an exception with full traceback."""
        logger.bind(**kwargs).exception(f"{message}: {exception}")
    
    def structured(self, message: str, data: Dict[str, Any], **kwargs) -> None:
        """Log structured data."""
        logger.bind(**data, **kwargs).info(message)
    
    def with_context(self, **context) -> 'CLILogger':
        """Create a logger with persistent context."""
        return logger.bind(**context)

PATH_TO_LOGS = str(Path("~/mc-logs").expanduser().resolve())

# Global logger instance
cli_logger = CLILogger(
    log_file=f"{PATH_TO_LOGS}/mc-cli.log",
    log_level="DEBUG",
    show_timestamps=False,
    colorize=True
)
