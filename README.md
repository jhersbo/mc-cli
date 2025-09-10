# mc-cli

A simple CLI to manage a Minecraft Bedrock Server running in Docker.

## Usage

```bash
# Server management
mc-cli start          # Start the server
mc-cli stop           # Stop the server
mc-cli up             # Rebuild and start server
mc-cli down           # Stop and cleanup server
mc-cli status         # Check server status
mc-cli logs           # View server logs

# Backup
mc-cli backup [name] [destination]  # Backup world data

# User management
mc-cli add-user <name> <uuid>       # Add user to allowlist
mc-cli remove-user <name>           # Remove user from allowlist
mc-cli grant <name> [permission]  # Grant permission level (visitor/member/operator/admin)