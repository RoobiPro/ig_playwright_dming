"""
Logging utilities for Instagram automation
"""
import logging
import os
from datetime import datetime
from typing import Optional
from . import config


def setup_logger(name: str = "instagram_automation", level: str = "INFO") -> logging.Logger:
    """
    Setup a logger with both file and console handlers
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        log_dir = os.path.join(config.DATA_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = f"instagram_automation_{datetime.now().strftime('%Y%m%d')}.log"
        log_filepath = os.path.join(log_dir, log_filename)
        
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
    
    return logger


def log_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """
    Log an error with context information
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
    """
    error_msg = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
    logger.error(error_msg, exc_info=True)


def log_performance(logger: logging.Logger, operation: str, duration: float, 
                   additional_info: Optional[str] = None) -> None:
    """
    Log performance information
    
    Args:
        logger: Logger instance
        operation: Description of the operation
        duration: Time taken in seconds
        additional_info: Additional performance information
    """
    info_msg = f"Performance: {operation} took {duration:.2f}s"
    if additional_info:
        info_msg += f" - {additional_info}"
    logger.info(info_msg)


def log_extraction_results(logger: logging.Logger, username: str, message_count: int, 
                          extraction_type: str = "initial") -> None:
    """
    Log message extraction results
    
    Args:
        logger: Logger instance
        username: Username being processed
        message_count: Number of messages extracted
        extraction_type: Type of extraction (initial, incremental)
    """
    logger.info(f"Extraction completed for {username}: {message_count} messages ({extraction_type})")


def log_chat_processing(logger: logging.Logger, chat_index: int, total_chats: int, 
                       username: str, success: bool = True) -> None:
    """
    Log chat processing status
    
    Args:
        logger: Logger instance
        chat_index: Current chat index (0-based)
        total_chats: Total number of chats
        username: Username being processed
        success: Whether processing was successful
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Chat {chat_index + 1}/{total_chats} ({username}): {status}")


class PerformanceTimer:
    """Context manager for measuring performance"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type is None:
                log_performance(self.logger, self.operation, duration)
            else:
                self.logger.error(f"Failed: {self.operation} after {duration:.2f}s")


# Create default logger instance
default_logger = setup_logger()