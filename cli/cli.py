import click
import subprocess

DOCKER_CONTAINER_NAME = "mc-bedrock"
PATH_TO_CONTAINER = "~/mc-bedrock"

def out(out: subprocess.CompletedProcess) -> None:
    click.echo(out.stdout)
    click.echo(out.stderr)

def docker_cmd(args: str) -> None:
    out(subprocess.run(["docker"] + args, capture_output=True, text=True))

@click.group()
def cli() -> None:
    """A simple CLI to manage your Minecraft Bedrock Server running in Docker."""
    pass

@cli.command()
def start() -> None:
    """Start the Minecraft Bedrock Server."""
    click.echo(f"Starting {DOCKER_CONTAINER_NAME}...")
    docker_cmd([
        "start", 
        DOCKER_CONTAINER_NAME
    ])

@cli.command()
def up() -> None:
    """Rebuild the server container from the docker-compose.yml file"""
    click.echo(f"Rebuilding {DOCKER_CONTAINER_NAME}")
    docker_cmd([
        "compose",
        "-f",
        f"{PATH_TO_CONTAINER}/docker-compose.yml"
        "up",
        "-d"
    ])

@cli.command()
def stop() -> None:
    """Stop the Minecraft Bedrock Server."""
    click.echo(f"Stopping {DOCKER_CONTAINER_NAME}...")
    docker_cmd([
        "stop", 
        DOCKER_CONTAINER_NAME
    ])

@cli.command()
def down() -> None:
    """Stops and cleans up the container"""
    click.echo(f"Stopping and cleaning up {DOCKER_CONTAINER_NAME}")
    docker_cmd([
        "compose",
        "-f",
        f"{PATH_TO_CONTAINER}/docker-compose.yml"
        "down"
    ])

@cli.command()
def status() -> None:
    """Get the status of the Minecraft Bedrock Server."""
    click.echo(f"Status of {DOCKER_CONTAINER_NAME}...")
    docker_cmd([
        "ps", 
        "-a", 
        "--filter", 
        f"name={DOCKER_CONTAINER_NAME}"
    ])

@cli.command()
def logs() -> None:
    """Get the logs of the Minecraft Bedrock Server."""
    click.echo(f"Logs of {DOCKER_CONTAINER_NAME}...")
    docker_cmd([
        "logs", 
        "-f", 
        DOCKER_CONTAINER_NAME
    ])

@cli.command()
@click.argument("backup_name", default="backup.tar.gz")
@click.argument("backup_dest", default="~/mc-backups")
def backup(backup_name: str, backup_dest: str) -> None:
    """Backup the Minecraft world data."""
    click.echo(f"Attempting to backup world data to {backup_dest}/{backup_name}...")
    out(docker_cmd([
        "exec", 
        DOCKER_CONTAINER_NAME, 
        "tar", 
        "czf", 
        f"/data/backups/{backup_name}", 
        "/data/worlds"
    ]))
    out(docker_cmd([
        "cp", 
        f"{DOCKER_CONTAINER_NAME}:/data/backups/{backup_name}", 
        f"{backup_dest}/{backup_name}"
    ]))
    click.echo("Backup complete...")