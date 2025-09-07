import click
import subprocess
from typing import Optional, Union, List
from enum import Enum


class OutputLevel(Enum):
    """Output verbosity levels"""
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


class Writer:
    """Enhanced output writer for CLI commands with multiple output modes and formatting options."""
    
    def __init__(self, output_level: OutputLevel = OutputLevel.NORMAL, 
                 show_timestamps: bool = False, 
                 colorize: bool = True):
        """
        Initialize the Writer with configuration options.
        
        Args:
            output_level: Verbosity level for output
            show_timestamps: Whether to include timestamps in output
            colorize: Whether to use colored output
        """
        self.output_level = output_level
        self.show_timestamps = show_timestamps
        self.colorize = colorize
    
    def _format_message(self, message: str, level: OutputLevel = OutputLevel.NORMAL) -> str:
        """Format a message with optional timestamp and color."""
        if level.value > self.output_level.value:
            return ""
        
        formatted = message
        
        if self.show_timestamps:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted = f"[{timestamp}] {formatted}"
        
        return formatted
    
    def _echo(self, message: str, level: OutputLevel = OutputLevel.NORMAL, 
              fg: Optional[str] = None, bg: Optional[str] = None) -> None:
        """Echo a message with optional formatting."""
        formatted = self._format_message(message, level)
        if formatted:
            if self.colorize and (fg or bg):
                click.echo(click.style(formatted, fg=fg, bg=bg))
            else:
                click.echo(formatted)
    
    def info(self, message: str) -> None:
        """Write an info message."""
        self._echo(f"ℹ️  {message}", OutputLevel.NORMAL, fg="blue")
    
    def success(self, message: str) -> None:
        """Write a success message."""
        self._echo(f"✅ {message}", OutputLevel.NORMAL, fg="green")
    
    def warning(self, message: str) -> None:
        """Write a warning message."""
        self._echo(f"⚠️  {message}", OutputLevel.NORMAL, fg="yellow")
    
    def error(self, message: str) -> None:
        """Write an error message."""
        self._echo(f"❌ {message}", OutputLevel.NORMAL, fg="red")
    
    def debug(self, message: str) -> None:
        """Write a debug message."""
        self._echo(f"🐛 {message}", OutputLevel.DEBUG, fg="magenta")
    
    def verbose(self, message: str) -> None:
        """Write a verbose message."""
        self._echo(f"📝 {message}", OutputLevel.VERBOSE, fg="cyan")
    
    def write_subprocess_output(self, result: subprocess.CompletedProcess, 
                               show_stdout: bool = True, 
                               show_stderr: bool = True,
                               prefix_stdout: str = "",
                               prefix_stderr: str = "") -> None:
        """
        Write subprocess output with enhanced formatting.
        
        Args:
            result: Completed subprocess result
            show_stdout: Whether to show stdout
            show_stderr: Whether to show stderr
            prefix_stdout: Optional prefix for stdout lines
            prefix_stderr: Optional prefix for stderr lines
        """
        if show_stdout and result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    self._echo(f"{prefix_stdout}{line}", OutputLevel.NORMAL)
        
        if show_stderr and result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    self._echo(f"{prefix_stderr}{line}", OutputLevel.NORMAL, fg="red")
    
    def write_docker_output(self, result: subprocess.CompletedProcess) -> None:
        """Write Docker command output with specialized formatting."""
        if result.stdout:
            self.info("Docker output:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    self._echo(f"  {line}", OutputLevel.NORMAL)
        
        if result.stderr:
            self.warning("Docker warnings/errors:")
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    self._echo(f"  {line}", OutputLevel.NORMAL, fg="yellow")
    
    def write_progress(self, current: int, total: int, message: str = "") -> None:
        """Write a progress indicator."""
        if self.output_level.value >= OutputLevel.NORMAL.value:
            percentage = (current / total) * 100 if total > 0 else 0
            progress_bar = "█" * int(percentage / 2) + "░" * (50 - int(percentage / 2))
            self._echo(f"\r{message} [{progress_bar}] {percentage:.1f}% ({current}/{total})", 
                      OutputLevel.NORMAL, fg="green")
    
    def write_table(self, headers: List[str], rows: List[List[str]], 
                   title: Optional[str] = None) -> None:
        """Write a formatted table."""
        if title:
            self.info(title)
        
        if not headers or not rows:
            return
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Write header
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        self._echo(header_row, OutputLevel.NORMAL, fg="bright_blue")
        self._echo("-" * len(header_row), OutputLevel.NORMAL)
        
        # Write rows
        for row in rows:
            row_str = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            self._echo(row_str, OutputLevel.NORMAL)
    
    def write_json(self, data: Union[dict, list], indent: int = 2) -> None:
        """Write JSON data in a formatted way."""
        import json
        formatted_json = json.dumps(data, indent=indent)
        self._echo(formatted_json, OutputLevel.NORMAL, fg="bright_white")
    
    def clear_line(self) -> None:
        """Clear the current line."""
        click.echo("\r" + " " * 80 + "\r", nl=False)
    
    def newline(self) -> None:
        """Write a newline."""
        click.echo()