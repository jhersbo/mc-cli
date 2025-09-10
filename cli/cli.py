from enum import member
import json
from math import perm
from tempfile import NamedTemporaryFile
import os
from webbrowser import get
import click
import subprocess
from pathlib import Path
from cli.config.permissions import PermissionLevel
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
    
    # Read existing allowlist or start empty
    read_result = docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "cat", 
        "/data/allowlist.json"
    ])
    allowlist_data = json.loads(read_result.stdout) if is_cmd_successful(read_result) else []
    
    # Check for duplicates
    if any(user.get("name") == name or user.get("uuid") == uuid for user in allowlist_data):
        raise click.ClickException("User already exists in allowlist")
    
    # Add user and write back
    allowlist_data.append({"name": name, "uuid": uuid})
    
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(allowlist_data, f, indent=2)
        temp_path = f.name
    
    try:
        copy_result = docker_cmd([
            "cp", 
            temp_path, 
            f"{DOCKER_CONTAINER_NAME}:/data/allowlist.json"
        ])
        if not is_cmd_successful(copy_result):
            raise click.ClickException("Failed to update allowlist")
        cli_logger.success(f"Added user '{name}' to allowlist")
    finally:
        os.unlink(temp_path)

@cli.command()
@click.argument("name")
def remove_user(name: str) -> None:
    """Removes a user from the allowlist.json file"""
    cli_logger.info(f"Removing user '{name}' from allowlist...")
    
    # Read existing allowlist or start empty
    read_result = docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "cat", 
        "/data/allowlist.json"
    ])
    allowlist_data = json.loads(read_result.stdout) if is_cmd_successful(read_result) else []
    
    # Find and remove user
    original_count = len(allowlist_data)
    allowlist_data = [user for user in allowlist_data if user.get("name") != name]
    
    if len(allowlist_data) == original_count:
        raise click.ClickException(f"User '{name}' not found in allowlist")
    
    # Write back to container
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(allowlist_data, f, indent=2)
        temp_path = f.name
    
    try:
        copy_result = docker_cmd([
            "cp", 
            temp_path, 
            f"{DOCKER_CONTAINER_NAME}:/data/allowlist.json"
        ])
        if not is_cmd_successful(copy_result):
            raise click.ClickException("Failed to update allowlist")
        cli_logger.success(f"Removed user '{name}' from allowlist")
    finally:
        os.unlink(temp_path)

@cli.command()
@click.argument("name")
@click.argument("permission", default = PermissionLevel.MEMBER.value)
def grant(name: str, permission: str) -> None:
    """Grants a user a permission level on the server"""
    cli_logger.info(f"Granting user '{name}' the permission level of '{permission}'")

    #read in allowlist.json
    output = docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "cat", 
        "/data/allowlist.json"
    ])
    allowlist_data = json.loads(output.stdout) if is_cmd_successful(output) else []
    # Find user in allowlist.json
    user_entry = next((user for user in allowlist_data if user.get("name") == name and user.get("xuid") is not None), None)

    if user_entry is None:
        raise click.ClickException("User does not exist in allowlist.json")

    user_xuid = user_entry.get("xuid")

    #read in permissions.json
    output = docker_cmd([
        "exec",
        DOCKER_CONTAINER_NAME,
        "cat",
        "/data/permissionlist.json"
    ])
    permissionlist_data = json.loads(output.stdout) if is_cmd_successful(output) else []

    #validate input permission level
    if not any(p.value == permission.lower() for p in list(PermissionLevel)):
        raise click.ClickException(f"{permission} is not a recognized permission group")
    
    # all good - add to permission list
    permissionlist_data.append({ "xuid": user_xuid, "permission": permission.lower() })

    # write to temp file
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(permissionlist_data, f, indent=2)
        temp_path = f.name

    try:
        copy_result = docker_cmd([
            "cp", 
            temp_path, 
            f"{DOCKER_CONTAINER_NAME}:/data/permissionlist.json"
        ])
        if not is_cmd_successful(copy_result):
            raise click.ClickException("Failed to update permissionlist")
        cli_logger.success(f"Added user '{name}' to permissionlist with permission of {permission.lower()}")
    finally:
        os.unlink(temp_path)

@cli.command()
@cli.argument("name")
def revoke(name: str) -> None:
    """Revokes a user from the permissions list"""
    # Read existing allowlist or start empty
    output = docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "cat", 
        "/data/allowlist.json"
    ])
    allowlist_data = json.loads(output.stdout) if is_cmd_successful(output) else []
    # Find user in allowlist.json
    user_entry = next((user for user in allowlist_data if user.get("name") == name and user.get("xuid") is not None), None)

    if user_entry is None:
        raise click.ClickException("User does not exist in allowlist.json")

    user_xuid = user_entry.get("xuid")

    # Read in permissionlist.json
    output = docker_cmd([
        "exec",
        DOCKER_CONTAINER_NAME,
        "cat",
        "/data/permissionlist.json"
    ])
    permissionlist_data = json.loads(output.stdout) if is_cmd_successful(output) else []

    # Remove user from permissionlist_data
    new_permissionlist_data = [entry for entry in permissionlist_data if entry.get("xuid") != user_xuid]

    if len(new_permissionlist_data) == len(permissionlist_data):
        raise click.ClickException(f"User '{name}' is not in the permissionlist")

    # Write to temp file
    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(new_permissionlist_data, f, indent=2)
        temp_path = f.name

    try:
        copy_result = docker_cmd([
            "cp", 
            temp_path, 
            f"{DOCKER_CONTAINER_NAME}:/data/permissionlist.json"
        ])
        if not is_cmd_successful(copy_result):
            raise click.ClickException("Failed to update permissionlist")
        cli_logger.success(f"Revoked user '{name}' from permissionlist")
    finally:
        os.unlink(temp_path)