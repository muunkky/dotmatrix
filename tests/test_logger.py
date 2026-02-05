"""
TDD tests for logging system.

Tests the logger.py module configuration, handlers, formatters,
and performance impact.
"""

import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from dotmatrix.logger import setup_logging, get_logger, log_performance


class TestLoggerInitialization:
    """Test logger setup with different configurations."""

    def test_setup_logging_creates_logger(self, tmp_path):
        """Test that setup_logging creates a configured logger."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            console_level=logging.INFO,
            file_level=logging.DEBUG
        )
        
        assert logger is not None
        assert logger.name == "dotmatrix"
        assert logger.level == logging.DEBUG
        
    def test_setup_logging_with_verbose_flag(self, tmp_path):
        """Test verbose flag sets console to DEBUG level."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            verbose=True
        )
        
        # Console handler should be DEBUG level
        console_handlers = [h for h in logger.handlers 
                           if isinstance(h, logging.StreamHandler) 
                           and not isinstance(h, logging.FileHandler)]
        assert len(console_handlers) > 0
        assert console_handlers[0].level == logging.DEBUG
        
    def test_setup_logging_with_debug_flag(self, tmp_path):
        """Test debug flag enables debug mode."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            debug=True
        )
        
        assert logger.level == logging.DEBUG


class TestFileHandler:
    """Test file logging with rotation."""
    
    def test_file_handler_creates_log_file(self, tmp_path):
        """Test that file handler creates log file."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(log_file=str(log_file))
        logger.info("Test message")
        
        assert log_file.exists()
        assert log_file.read_text().strip().endswith("Test message")
        
    def test_file_handler_with_rotation(self, tmp_path):
        """Test that rotation works at size limit."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            max_bytes=1024,  # 1KB for testing
            backup_count=2
        )
        
        # Write enough to trigger rotation
        for i in range(100):
            logger.info(f"Message {i}: {'x' * 100}")
            
        # Check backup files exist
        assert (tmp_path / "test.log.1").exists() or (tmp_path / "test.log").stat().st_size < 1024


class TestConsoleHandler:
    """Test console output with level filtering."""
    
    def test_console_handler_filters_by_level(self, tmp_path, caplog):
        """Test console only shows messages at configured level."""
        log_file = tmp_path / "test.log"
        
        with caplog.at_level(logging.INFO):
            logger = setup_logging(
                log_file=str(log_file),
                console_level=logging.INFO
            )
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            
        # Console should only have INFO and WARNING
        assert "Debug message" not in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        
    def test_console_handler_verbose_shows_debug(self, tmp_path, caplog):
        """Test verbose mode shows DEBUG messages on console."""
        log_file = tmp_path / "test.log"
        
        with caplog.at_level(logging.DEBUG):
            logger = setup_logging(
                log_file=str(log_file),
                verbose=True
            )
            
            logger.debug("Debug message")
            
        assert "Debug message" in caplog.text


class TestJSONFormatter:
    """Test JSON-structured logging format."""
    
    def test_json_formatter_creates_valid_json(self, tmp_path):
        """Test that JSON formatter produces valid JSON."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            use_json=True
        )
        
        logger.info("Test message", extra={"metric": "detection", "value": 123})
        
        # Read log file and parse JSON
        log_content = log_file.read_text().strip()
        log_data = json.loads(log_content)
        
        assert "message" in log_data
        assert "timestamp" in log_data
        assert "level" in log_data
        assert log_data["metric"] == "detection"
        assert log_data["value"] == 123


class TestPerformanceLogging:
    """Test performance metric capture and logging."""
    
    def test_log_performance_captures_metrics(self, tmp_path):
        """Test log_performance() function captures timing."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file), use_json=True)
        
        with log_performance("test_operation"):
            # Simulate work
            total = sum(range(1000))
            
        # Read log and verify performance metric
        log_content = log_file.read_text().strip().split('\n')[-1]
        log_data = json.loads(log_content)
        
        assert "operation" in log_data
        assert log_data["operation"] == "test_operation"
        assert "duration_ms" in log_data
        assert log_data["duration_ms"] > 0
        
    def test_performance_decorator(self, tmp_path):
        """Test @log_performance decorator on functions."""
        from dotmatrix.logger import performance_timer
        
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file), use_json=True)
        
        @performance_timer("math_operation")
        def calculate_sum(n):
            return sum(range(n))
            
        result = calculate_sum(1000)
        assert result == 499500
        
        # Verify performance was logged
        log_content = log_file.read_text()
        assert "math_operation" in log_content
        assert "duration_ms" in log_content


class TestLogRotation:
    """Test automatic log rotation and cleanup."""
    
    def test_rotation_at_size_limit(self, tmp_path):
        """Test logs rotate when reaching max size."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            max_bytes=512,  # Very small for testing
            backup_count=3
        )
        
        # Write messages until rotation occurs
        for i in range(50):
            logger.info(f"Message {i}: " + "x" * 50)
            
        # Should have rotated
        backup_files = list(tmp_path.glob("test.log.*"))
        assert len(backup_files) > 0
        
    def test_backup_count_limits_old_logs(self, tmp_path):
        """Test backup_count parameter limits number of old logs."""
        log_file = tmp_path / "test.log"
        
        logger = setup_logging(
            log_file=str(log_file),
            max_bytes=256,
            backup_count=2  # Only keep 2 backups
        )
        
        # Force multiple rotations
        for i in range(100):
            logger.info(f"Message {i}: " + "x" * 100)
            
        # Should have max 2 backup files
        backup_files = list(tmp_path.glob("test.log.*"))
        assert len(backup_files) <= 2


class TestGetLogger:
    """Test get_logger() helper function."""
    
    def test_get_logger_returns_configured_logger(self, tmp_path):
        """Test get_logger() returns the dotmatrix logger."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))
        
        logger = get_logger()
        
        assert logger.name == "dotmatrix"
        assert len(logger.handlers) > 0
        
    def test_get_logger_with_module_name(self, tmp_path):
        """Test get_logger(__name__) creates child logger."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))
        
        logger = get_logger("dotmatrix.circle_detector")
        
        assert logger.name == "dotmatrix.circle_detector"
        # Child logger should inherit handlers from parent
        assert logger.parent is not None
        assert logger.parent.name == "dotmatrix"
