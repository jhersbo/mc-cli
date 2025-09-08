import json
import tempfile
import os
import click
import subprocess
from pathlib import Path
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
    ])
    
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
    ])
    
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
    ])
    
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
    ])
    
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
    ])
    
    # Also show the raw result for debugging
    cli_logger.debug(f"Raw stdout: {repr(result.stdout)}")
    cli_logger.debug(f"Raw stderr: {repr(result.stderr)}")
    cli_logger.debug(f"Return code: {result.returncode}")

@cli.command()
def logs() -> None:
    """Get the logs of the Minecraft Bedrock Server."""
    cli_logger.info(f"Showing logs for {DOCKER_CONTAINER_NAME}...")
    cli_logger.info("Press Ctrl+C to stop following logs")
    
    # For logs, we need to stream output in real-time, not capture it
    import subprocess
    command = ["docker", "logs", "-f", DOCKER_CONTAINER_NAME]
    cli_logger.docker_command("logs -f", DOCKER_CONTAINER_NAME)
    
    try:
        subprocess.run(command, text=True)
    except KeyboardInterrupt:
        cli_logger.info("Logs following stopped by user")

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
    ])
    
    if not is_cmd_successful(archive_result):
        cli_logger.backup_error(backup_name, backup_dest, "Failed to create archive inside container")
        raise click.ClickException("Docker exec tar command failed")
    
    # Copy backup to local filesystem
    cli_logger.info("Copying backup to local filesystem...")
    copy_result = docker_cmd([
        "cp", 
        f"{DOCKER_CONTAINER_NAME}:/data/backups/{backup_name}", 
        f"{backup_dest}/{backup_name}"
    ])
    
    if not is_cmd_successful(copy_result):
        cli_logger.backup_error(backup_name, backup_dest, "Failed to copy backup to local filesystem")
        raise click.ClickException("Docker cp command failed")
    
    cli_logger.backup_success(backup_name, backup_dest)

@cli.command()
@click.argument("name")
@click.argument("uuid")
def add_user(name: str, uuid: str) -> None:
    """Adds a user to the allowlist.json file"""
    cli_logger.info(f"Adding user '{name}' to allowlist...")
    
    allowlist_path = Path(f"{PATH_TO_CONTAINER}/data/allowlist.json")
    
    allowlist_data = []
    try:
        with open(allowlist_path, 'r') as f:
            allowlist_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        allowlist_data = []
    
    if any(user.get("name") == name or user.get("uuid") == uuid for user in allowlist_data):
        raise click.ClickException("User already exists in allowlist")
    
    allowlist_data.append({"name": name, "uuid": uuid})
    
    with open(allowlist_path, 'w') as f:
        json.dump(allowlist_data, f, indent=2)
    
    cli_logger.success(f"Added user '{name}' to allowlist")

@cli.command()
@click.argument("name")
def remove_user(name: str) -> None:
    """Removes a user from the allowlist.json file"""
    cli_logger.info(f"Removing user '{name}' from allowlist...")
    
    allowlist_path = Path(f"{PATH_TO_CONTAINER}/data/allowlist.json")
    
    allowlist_data = []
    try:
        with open(allowlist_path, 'r') as f:
            allowlist_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        allowlist_data = []
    
    original_count = len(allowlist_data)
    allowlist_data = [user for user in allowlist_data if user.get("name") != name]
    
    if len(allowlist_data) == original_count:
        raise click.ClickException(f"User '{name}' not found in allowlist")
    
    with open(allowlist_path, 'w') as f:
        json.dump(allowlist_data, f, indent=2)
    
    cli_logger.success(f"Removed user '{name}' from allowlist")