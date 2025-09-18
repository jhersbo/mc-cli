# mc-cli

A simple CLI to manage a Minecraft Bedrock Server running in Docker.

## Configuration

- Docker must be running (Docker Desktop on macOS/Windows, Docker Engine on Linux).
- Container name must be `mc-bedrock` (the CLI targets this name).
- A `docker-compose.yml` must exist at `~/mc-bedrock/docker-compose.yml`.
- The server data directory in the container must be mounted to `/data`.
- The backups directory in the container must be mounted to `/backups`

Minimal docker-compose.yml example:

```yaml
services:
  mc-bedrock:
    image: itzg/minecraft-bedrock-server:latest
    container_name: mc-bedrock
    ports:
      - "19132:19132/udp"
    volumes:
      - ./data:data
      - ./backups:data/backups
    environment:
      EULA: "TRUE"
    restart: unless-stopped
```

Notes:
- The CLI reads/writes `/data/allowlist.json`, `/data/permissionlist.json` via Docker commands.
- Ensure the container user can read/write those files inside `/data`.

## Usage

```bash
# Server management
mc-cli start          # Start the server
mc-cli stop           # Stop the server
mc-cli restart        # Restart the server
mc-cli up             # Rebuild and start server
mc-cli down           # Stop and cleanup server
mc-cli status         # Check server status
mc-cli logs           # View server logs

# Backup
mc-cli backup [name] [destination]  # Backup world data

# User management
mc-cli add-user <name> <uuid>       # Add user to allowlist
mc-cli remove-user <name>           # Remove user from allowlist