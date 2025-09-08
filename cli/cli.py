import click
import subprocess
from pathlib import Path
from cli.utils.logger import cli_logger

DOCKER_CONTAINER_NAME = "mc-bedrock"
PATH_TO_CONTAINER = str(Path("~/mc-bedrock").expanduser().resolve())
PATH_TO_LOCAL_BACKUPS = str(Path("~/mc-backups").expanduser().resolve())

def docker_cmd(args: str, out: bool) -> subprocess.CompletedProcess:
    """Run a docker command and return the result."""
    command = " ".join(args)
    cli_logger.docker_command(command, DOCKER_CONTAINER_NAME)
    
    result = subprocess.run(["docker"] + args, capture_output=True, text=True)
    
    if out is True:
        if result.stdout:
            cli_logger.info("Docker output:")
            # Print each line of stdout
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    cli_logger.info(f"  {line}")
        
        if result.stderr:
            cli_logger.warning("Docker warnings/errors:")
            # Print each line of stderr
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    cli_logger.warning(f"  {line}")
    
    # Debug: Log the return code
    cli_logger.debug(f"Docker command '{command}' returned code: {result.returncode}")
    
    return result

def is_cmd_successful(result: subprocess.CompletedProcess) -> bool:
    """Check if a docker command was successful."""
    return result.returncode == 0

@click.group()
def cli() -> None:
    """A simple CLI to manage your Minecraft Bedrock Server running in Docker."""
    pass

@cli.command()
def start() -> None:
    """Start the Minecraft Bedrock Server."""
    cli_logger.info(f"Starting {DOCKER_CONTAINER_NAME}...")
    result = docker_cmd([
        "start", 
        DOCKER_CONTAINER_NAME
    ], True)
    
    if is_cmd_successful(result):
        cli_logger.docker_success("start", DOCKER_CONTAINER_NAME)
    else:
        cli_logger.docker_error("start", DOCKER_CONTAINER_NAME, result.stderr or "Unknown error")
        raise click.ClickException("Docker start command failed")

@cli.command()
def up() -> None:
    """Rebuild the server container from the docker-compose.yml file"""
    cli_logger.info(f"Rebuilding {DOCKER_CONTAINER_NAME}")
    result = docker_cmd([
        "compose",
        "-f",
        f"{PATH_TO_CONTAINER}/docker-compose.yml",
        "up",
        "-d"
    ], True)
    
    if is_cmd_successful(result):
        cli_logger.docker_success("compose up", DOCKER_CONTAINER_NAME)
    else:
        cli_logger.docker_error("compose up", DOCKER_CONTAINER_NAME, result.stderr or "Unknown error")
        raise click.ClickException("Docker compose up command failed")

@cli.command()
def stop() -> None:
    """Stop the Minecraft Bedrock Server."""
    cli_logger.info(f"Stopping {DOCKER_CONTAINER_NAME}...")
    result = docker_cmd([
        "stop", 
        DOCKER_CONTAINER_NAME
    ], True)
    
    if is_cmd_successful(result):
        cli_logger.docker_success("stop", DOCKER_CONTAINER_NAME)
    else:
        cli_logger.docker_error("stop", DOCKER_CONTAINER_NAME, result.stderr or "Unknown error")
        raise click.ClickException("Docker stop command failed")

@cli.command()
def down() -> None:
    """Stops and cleans up the container"""
    cli_logger.info(f"Stopping and cleaning up {DOCKER_CONTAINER_NAME}")
    result = docker_cmd([
        "compose",
        "-f",
        f"{PATH_TO_CONTAINER}/docker-compose.yml",
        "down"
    ], True)
    
    if is_cmd_successful(result):
        cli_logger.docker_success("compose down", DOCKER_CONTAINER_NAME)
    else:
        cli_logger.docker_error("compose down", DOCKER_CONTAINER_NAME, result.stderr or "Unknown error")
        raise click.ClickException("Docker compose down command failed")

@cli.command()
def status() -> None:
    """Get the status of the Minecraft Bedrock Server."""
    cli_logger.info(f"Checking status of {DOCKER_CONTAINER_NAME}...")
    result = docker_cmd([
        "ps", 
        "-a", 
        "--filter", 
        f"name={DOCKER_CONTAINER_NAME}"
    ], True)
    
    # Also show the raw result for debugging
    cli_logger.debug(f"Raw stdout: {repr(result.stdout)}")
    cli_logger.debug(f"Raw stderr: {repr(result.stderr)}")
    cli_logger.debug(f"Return code: {result.returncode}")

@cli.command()
def logs() -> None:
    """Get the logs of the Minecraft Bedrock Server."""
    cli_logger.info(f"Showing logs for {DOCKER_CONTAINER_NAME}...")
    cli_logger.info("Press Ctrl+C to stop following logs")
    docker_cmd([
        "logs", 
        "-f", 
        DOCKER_CONTAINER_NAME
    ], False)

@cli.command()
def test_logging() -> None:
    """Test the logging functionality."""
    cli_logger.info("Testing info logging")
    cli_logger.success("Testing success logging")
    cli_logger.warning("Testing warning logging")
    cli_logger.error("Testing error logging")
    cli_logger.debug("Testing debug logging")
    
    # Test with a command that should produce stderr
    cli_logger.info("Testing Docker command with potential errors...")
    result = docker_cmd(["ps", "--filter", "name=nonexistent-container"], True)
    cli_logger.info(f"Command completed with return code: {result.returncode}")

@cli.command()
@click.argument("backup_name", default="backup.tar.gz")
@click.argument("backup_dest", default=PATH_TO_LOCAL_BACKUPS)
def backup(backup_name: str, backup_dest: str) -> None:
    """Backup the Minecraft world data."""
    cli_logger.backup_start(backup_name, backup_dest)
    
    # Create backup inside container
    cli_logger.info("Creating archive inside container...")
    archive_result = docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "tar", 
        "czf", 
        f"/data/backups/{backup_name}", 
        "/data/worlds"
    ], True)
    
    if not is_cmd_successful(archive_result):
        cli_logger.backup_error(backup_name, backup_dest, "Failed to create archive inside container")
        raise click.ClickException("Docker exec tar command failed")
    
    # Copy backup to local filesystem
    cli_logger.info("Copying backup to local filesystem...")
    copy_result = docker_cmd([
        "cp", 
        f"{DOCKER_CONTAINER_NAME}:/data/backups/{backup_name}", 
        f"{backup_dest}/{backup_name}"
    ], True)
    
    if not is_cmd_successful(copy_result):
        cli_logger.backup_error(backup_name, backup_dest, "Failed to copy backup to local filesystem")
        raise click.ClickException("Docker cp command failed")
    
    cli_logger.backup_success(backup_name, backup_dest)