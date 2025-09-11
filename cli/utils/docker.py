"""
Utility functions for interacting with the Docker container
"""
from pathlib import Path
import subprocess
from cli.utils.logger import cli_logger

DOCKER_CONTAINER_NAME = "mc-bedrock"
PATH_TO_CONTAINER = str(Path("~/mc-bedrock").expanduser().resolve())
PATH_TO_LOCAL_BACKUPS = str(Path("~/mc-backups").expanduser().resolve())

def docker_cmd(args: str) -> subprocess.CompletedProcess:
    """Run a docker command and return the result."""
    command = " ".join(args)
    cli_logger.docker_command(command, DOCKER_CONTAINER_NAME)
    
    result = subprocess.run(["docker"] + args, capture_output=True, text=True)
    
    if result.stdout:
        cli_logger.info("Docker output:")
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                cli_logger.info(f"  {line}")
    
    if result.stderr:
        cli_logger.warning("Docker warnings/errors:")
        for line in result.stderr.strip().split('\n'):
            if line.strip():
                cli_logger.warning(f"  {line}")
    
    cli_logger.debug(f"Docker command '{command}' returned code: {result.returncode}")
    
    return result

def is_cmd_successful(result: subprocess.CompletedProcess) -> bool:
    """Check if a docker command was successful."""
    return result.returncode == 0