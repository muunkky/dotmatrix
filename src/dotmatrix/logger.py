"""
Logging configuration and utilities for dotmatrix.

Provides centralized logging setup with file rotation, console output,
JSON formatting for structured logs, and performance metric capture.

Usage:
    # In main application
    from dotmatrix.logger import setup_logging
    setup_logging(log_file="log/dotmatrix.log", verbose=True)
    
    # In modules
    from dotmatrix.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Processing image...")
    
    # Performance logging
    from dotmatrix.logger import log_performance
    with log_performance("circle_detection"):
        detect_circles(image)
"""

import json
import logging
import logging.handlers
import sys
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Optional


# Global logger instance
_logger: Optional[logging.Logger] = None


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs log records as JSON with timestamp, level, message, and any extra fields.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add any extra fields from record.__dict__
        # Exclude standard attributes
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'getMessage', 'taskName'
        }
        
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                log_data[key] = value
                
        return json.dumps(log_data)


def setup_logging(
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    verbose: bool = False,
    debug: bool = False,
    use_json: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB default
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup logging configuration for dotmatrix.
    
    Args:
        log_file: Path to log file. If None, only console logging is used.
        console_level: Minimum level for console output (default: INFO).
        file_level: Minimum level for file output (default: DEBUG).
        verbose: If True, sets console level to DEBUG.
        debug: If True, sets logger level to DEBUG (shows all messages).
        use_json: If True, use JSON formatter for structured logs.
        max_bytes: Maximum size of log file before rotation (default: 10MB).
        backup_count: Number of backup log files to keep (default: 5).
        
    Returns:
        Configured logger instance.
        
    Example:
        >>> logger = setup_logging(log_file="log/dotmatrix.log", verbose=True)
        >>> logger.info("Application started")
    """
    global _logger
    
    # Create or get logger
    logger = logging.getLogger("dotmatrix")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()  # Remove any existing handlers
    
    # Formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _logger = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance.
    
    Args:
        name: Logger name. If None, returns root dotmatrix logger.
              If provided, returns child logger (e.g., "dotmatrix.circle_detector").
              
    Returns:
        Logger instance.
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    if name is None:
        return logging.getLogger("dotmatrix")
    elif name.startswith("dotmatrix."):
        return logging.getLogger(name)
    else:
        return logging.getLogger(f"dotmatrix.{name}")


@contextmanager
def log_performance(operation: str, logger: Optional[logging.Logger] = None):
    """
    Context manager to log operation performance.
    
    Args:
        operation: Name of the operation being timed.
        logger: Logger instance to use. If None, uses default logger.
        
    Yields:
        None
        
    Example:
        >>> with log_performance("circle_detection"):
        ...     circles = detect_circles(image)
    """
    if logger is None:
        logger = get_logger()
        
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Performance: {operation}",
            extra={"operation": operation, "duration_ms": round(duration_ms, 2)}
        )


def performance_timer(operation_name: str):
    """
    Decorator to log function performance.
    
    Args:
        operation_name: Name of the operation for logging.
        
    Returns:
        Decorated function.
        
    Example:
        >>> @performance_timer("detect_circles")
        ... def detect_circles(image):
        ...     # detection logic
        ...     return circles
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"Performance: {operation_name}",
                    extra={"operation": operation_name, "duration_ms": round(duration_ms, 2)}
                )
        return wrapper
    return decorator
