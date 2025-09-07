import click
import subprocess
from pathlib import Path
from cli.utils.writer import Writer, OutputLevel

DOCKER_CONTAINER_NAME = "mc-bedrock"
PATH_TO_CONTAINER = str(Path("~/mc-bedrock").expanduser().resolve())
PATH_TO_LOCAL_BACKUPS = str(Path("~/mc-backups").expanduser().resolve())

# Initialize writer with default settings
writer = Writer(output_level=OutputLevel.NORMAL, show_timestamps=False, colorize=True)

def docker_cmd(args: str, out: bool) -> subprocess.CompletedProcess:
    """Run a docker command and return the result."""
    result = subprocess.run(["docker"] + args, capture_output=True, text=True)
    if out is True:
        writer.write_docker_output(result)
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
    writer.info(f"Starting {DOCKER_CONTAINER_NAME}...")
    result = docker_cmd([
        "start", 
        DOCKER_CONTAINER_NAME
    ], True)
    
    if is_cmd_successful(result):
        writer.success(f"{DOCKER_CONTAINER_NAME} started successfully!")
    else:
        writer.error(f"Failed to start {DOCKER_CONTAINER_NAME}")
        raise click.ClickException("Docker start command failed")

@cli.command()
def up() -> None:
    """Rebuild the server container from the docker-compose.yml file"""
    writer.info(f"Rebuilding {DOCKER_CONTAINER_NAME}")
    result = docker_cmd([
        "compose",
        "-f",
        f"{PATH_TO_CONTAINER}/docker-compose.yml",
        "up",
        "-d"
    ], True)
    
    if is_cmd_successful(result):
        writer.success(f"{DOCKER_CONTAINER_NAME} rebuilt and started!")
    else:
        writer.error(f"Failed to rebuild {DOCKER_CONTAINER_NAME}")
        raise click.ClickException("Docker compose up command failed")

@cli.command()
def stop() -> None:
    """Stop the Minecraft Bedrock Server."""
    writer.info(f"Stopping {DOCKER_CONTAINER_NAME}...")
    result = docker_cmd([
        "stop", 
        DOCKER_CONTAINER_NAME
    ], True)
    
    if is_cmd_successful(result):
        writer.success(f"{DOCKER_CONTAINER_NAME} stopped successfully!")
    else:
        writer.error(f"Failed to stop {DOCKER_CONTAINER_NAME}")
        raise click.ClickException("Docker stop command failed")

@cli.command()
def down() -> None:
    """Stops and cleans up the container"""
    writer.info(f"Stopping and cleaning up {DOCKER_CONTAINER_NAME}")
    result = docker_cmd([
        "compose",
        "-f",
        f"{PATH_TO_CONTAINER}/docker-compose.yml",
        "down"
    ], True)
    
    if is_cmd_successful(result):
        writer.success(f"{DOCKER_CONTAINER_NAME} stopped and cleaned up!")
    else:
        writer.error(f"Failed to stop and clean up {DOCKER_CONTAINER_NAME}")
        raise click.ClickException("Docker compose down command failed")

@cli.command()
def status() -> None:
    """Get the status of the Minecraft Bedrock Server."""
    writer.info(f"Checking status of {DOCKER_CONTAINER_NAME}...")
    docker_cmd([
        "ps", 
        "-a", 
        "--filter", 
        f"name={DOCKER_CONTAINER_NAME}"
    ], True)

@cli.command()
def logs() -> None:
    """Get the logs of the Minecraft Bedrock Server."""
    writer.info(f"Showing logs for {DOCKER_CONTAINER_NAME}...")
    writer.info("Press Ctrl+C to stop following logs")
    docker_cmd([
        "logs", 
        "-f", 
        DOCKER_CONTAINER_NAME
    ], False)

@cli.command()
@click.argument("backup_name", default="backup.tar.gz")
@click.argument("backup_dest", default=PATH_TO_LOCAL_BACKUPS)
def backup(backup_name: str, backup_dest: str) -> None:
    """Backup the Minecraft world data."""
    writer.info(f"Creating backup: {backup_name}")
    writer.verbose(f"Backup destination: {backup_dest}")
    
    # Create backup inside container
    writer.info("Creating archive inside container...")
    archive_result = docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "tar", 
        "czf", 
        f"/data/backups/{backup_name}", 
        "/data/worlds"
    ], True)
    
    if not is_cmd_successful(archive_result):
        writer.error("Failed to create archive inside container")
        raise click.ClickException("Docker exec tar command failed")
    
    # Copy backup to local filesystem
    writer.info("Copying backup to local filesystem...")
    copy_result = docker_cmd([
        "cp", 
        f"{DOCKER_CONTAINER_NAME}:/data/backups/{backup_name}", 
        f"{backup_dest}/{backup_name}"
    ], True)
    
    if not is_cmd_successful(copy_result):
        writer.error("Failed to copy backup to local filesystem")
        raise click.ClickException("Docker cp command failed")
    
    writer.success(f"Backup completed successfully: {backup_dest}/{backup_name}")