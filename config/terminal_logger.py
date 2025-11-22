"""Shared terminal logger for narrative logging across all agents

Backend Terminal Output Modes (controlled by TERMINAL_OUTPUT environment variable):
- "full" (default): Print all logs to backend console with color coding
- "selective": Print only important logs (INCIDENT, SUCCESS, ORCHESTRATOR, etc.)
- "none": No backend console output (logs only go to frontend terminal viewer)

Usage:
    # Full verbose output (default)
    python backend_api.py

    # Selective output (only key milestones)
    TERMINAL_OUTPUT=selective python backend_api.py

    # No backend output (frontend only)
    TERMINAL_OUTPUT=none python backend_api.py
"""
from collections import deque
from datetime import datetime
from threading import Lock
import os


class TerminalLogger:
    """Singleton logger for terminal viewer - thread-safe log buffer shared across all agents"""

    _instance = None
    _lock = Lock()

    # ANSI color codes for terminal output
    COLORS = {
        'GENERATOR': '\033[95m',      # Purple/Magenta
        'ORCHESTRATOR': '\033[93m',   # Yellow
        'ALERTOPS': '\033[94m',       # Blue
        'PREDICTIVEOPS': '\033[96m',  # Cyan
        'PATCHOPS': '\033[92m',       # Green
        'TASKOPS': '\033[33m',       # Orange/Yellow
        'LEARNING': '\033[35m',       # Magenta
        'PERCEPTION': '\033[90m',     # Dark Gray
        'SYNTHESIS': '\033[91m',      # Light Red
        'INCIDENT': '\033[94m',       # Blue
        'SUCCESS': '\033[92m',        # Green
        'WARNING': '\033[91m',        # Red
        'ERROR': '\033[91m',          # Red
        'KILLSWITCH': '\033[91m',     # Red
        'START': '\033[92m',          # Green
        'STOP': '\033[91m',           # Red
        'METRICS': '\033[90m',        # Dark Gray
        'INFO': '\033[37m',           # White
        'RESET': '\033[0m'            # Reset
    }

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.log_buffer = deque(maxlen=1000)

                    # Read output mode from environment variable
                    # Options: "full", "selective", "none"
                    cls._instance.output_mode = os.getenv("TERMINAL_OUTPUT", "full").lower()

                    # Define which log types are considered "important" for selective mode
                    cls._instance.important_types = {
                        'INCIDENT', 'SUCCESS', 'WARNING', 'ERROR',
                        'ORCHESTRATOR', 'SYNTHESIS', 'START', 'STOP', 'KILLSWITCH'
                    }
        return cls._instance

    def add_log(self, message: str, log_type: str = "INFO", agent: str = None):
        """
        Add a log entry to the terminal viewer buffer and optionally print to backend console.

        Args:
            message: Log message text
            log_type: Type of log (GENERATOR, ORCHESTRATOR, ALERTOPS, etc.)
            agent: Optional agent name for additional context
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": log_type,
            "agent": agent,
            "message": message
        }
        self.log_buffer.append(log_entry)

        # Print to backend terminal based on output mode
        if self.output_mode != "none":
            should_print = False

            if self.output_mode == "full":
                # Print all logs
                should_print = True
            elif self.output_mode == "selective":
                # Print only important logs
                should_print = log_type in self.important_types

            if should_print:
                self._print_to_console(timestamp, log_type, message)

    def _print_to_console(self, timestamp: str, log_type: str, message: str):
        """Print a colored log entry to the backend console"""
        color = self.COLORS.get(log_type, self.COLORS['INFO'])
        reset = self.COLORS['RESET']

        # Format: [HH:MM:SS] [TYPE] Message
        print(f"{color}[{timestamp}] [{log_type:14}]{reset} {message}")

    def get_logs(self, limit: int = None, log_type: str = None):
        """
        Get recent logs from the buffer, optionally filtered by log type.

        Args:
            limit: Optional limit on number of logs to return
            log_type: Optional filter for specific log type (e.g., "INCIDENT", "ALERTOPS")

        Returns:
            List of log entries (most recent last)
        """
        logs = list(self.log_buffer)

        # Filter by log_type if specified
        if log_type and log_type != "ALL":
            logs = [log for log in logs if log.get('type') == log_type]

        # Apply limit
        if limit:
            return logs[-limit:]
        return logs

    def clear_logs(self):
        """Clear all logs from the buffer"""
        self.log_buffer.clear()

    def set_output_mode(self, mode: str):
        """
        Change the terminal output mode dynamically.

        Args:
            mode: "full", "selective", or "none"
        """
        if mode in ["full", "selective", "none"]:
            self.output_mode = mode

    def get_output_mode(self) -> str:
        """
        Get the current terminal output mode.

        Returns:
            Current mode: "full", "selective", or "none"
        """
        return self.output_mode


# Singleton instance - import this in all files
terminal_logger = TerminalLogger()
