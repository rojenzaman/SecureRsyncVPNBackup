# SecureRsyncVPNBackup

A Docker-based solution for performing secure `rsync` backups over a VPN network using Gluetun. This setup ensures privacy and security by routing all backup traffic through a VPN connection.

## Features

- **Secure Backups over VPN**: All `rsync` operations are performed over a VPN connection provided by Gluetun.
- **Multiple Server Support**: Backup multiple remote servers, each with its own SSH key and configuration.
- **Customizable Backup Directory Structure**: Define custom names for backup directories and choose between date, date-time, or static formats.
- **Automated Scheduling**: Use `crontab` to schedule backups at your desired intervals.
- **Configurable Retention Policy**: Automatically delete backups older than a specified number of days.
- **Flexible Configuration**: All settings are managed via `config.json`, allowing easy customization without modifying code.

## Prerequisites

- **Docker** and **Docker Compose** installed on your system.
- **SSH Access** to the remote servers you wish to back up.
- **VPN Credentials** for your preferred VPN service supported by Gluetun.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/SecureRsyncVPNBackup.git
   cd SecureRsyncVPNBackup
   ```

2. **Copy Example Configuration Files**

   Rename the example configuration files and edit them according to your needs:

   ```bash
   cp config.json.example config.json
   cp crontab.example crontab
   ```

## Configuration

### 1. `config.json`

This file contains all the settings for your backups. Below is an explanation of each section:

```json
{
  "sync": {
    "remote_servers": [
      {
        "host": "yourserver.com",
        "user": "username",
        "path": "/remote/directory",
        "ssh_private_key": "/app/ssh/id_rsa_yourserver",
        "backup_name": "custom_backup_name",
        "backup_name_format": "date_time" // Possible values: "date_time", "date", "static"
      }
    ]
  },
  "settings": {
    "sync_target": "/data/sync",
    "ssh_port": 22,
    "max_days": 7,
    "debug_mode": false,
    "ssh_connection_timeout": 10,
    "rsync_max_retries": 3
  }
}
```

- **`remote_servers`**: An array of servers to back up.
  - **`host`**: The hostname or IP address of the remote server.
  - **`user`**: The SSH username for the remote server.
  - **`path`**: The directory on the remote server to back up.
  - **`ssh_private_key`**: Path to the SSH private key inside the Docker container.
  - **`backup_name`**: Custom name for the backup directory (defaults to `host` if not specified).
  - **`backup_name_format`**: Format for backup directory names. Possible values:
    - `"date_time"`: Creates a new backup directory with the current date and time (e.g., `2024-10-19_12-00-00`).
    - `"date"`: Creates a new backup directory with the current date (e.g., `2024-10-19`).
    - `"static"`: Synchronizes to a single directory without creating date-based subdirectories. In this mode, the backup directory specified by `backup_name` will be fully synchronized with the remote server, including deletions.
- **`settings`**:
  - **`sync_target`**: The local directory where backups will be stored.
  - **`ssh_port`**: SSH port of the remote servers.
  - **`max_days`**: Number of days to keep backups before deletion.
  - **`debug_mode`**: Set to `true` to keep the container running after errors for debugging.
  - **`ssh_connection_timeout`**: SSH connection timeout in seconds.
  - **`rsync_max_retries`**: Number of times to retry `rsync` on failure.

**Note**: After editing, make sure your `config.json` is valid JSON. Comments are not allowed in JSON files.

### 2. `crontab`

Defines the schedule for your backups using cron syntax.

Example content:

```bash
# Run the Python rsync script daily at midnight
0 0 * * * python3 /usr/local/bin/sync_rsync.py
```

**Instructions**:

- Edit the `crontab` file to set your desired backup schedule.
- Use [crontab.guru](https://crontab.guru/) for help with cron expressions.
- Ensure the file has no file extension when saving.

### 3. SSH Keys

Place your SSH private keys in the `ssh/` directory.

```bash
ssh/
├── id_rsa_yourserver
```

**Instructions**:

- The paths in `config.json` (e.g., `/app/ssh/id_rsa_yourserver`) should match the filenames in the `ssh/` directory.
- Ensure the keys have the correct permissions.

### 4. Gluetun Configuration

Update the `docker-compose.yml` file to configure Gluetun with your VPN settings.

```yaml
services:
  gluetun:
    image: qmcgaw/gluetun
    cap_add:
      - NET_ADMIN
    environment:
      - VPN_SERVICE_PROVIDER=your_vpn_provider
      - VPN_TYPE=wireguard
      - WIREGUARD_PRIVATE_KEY=your_private_key
      - WIREGUARD_ADDRESSES=your_wireguard_address
      - SERVER_CITIES=your_preferred_city
    restart: always
```

**Instructions**:

- Replace the environment variables with your VPN provider's details.
- Gluetun supports various VPN services; refer to the [Gluetun documentation](https://github.com/qdm12/gluetun/wiki) for configuration options.
- You can use other VPN services by adjusting the Gluetun settings accordingly.

## Usage

1. **Build and Start the Containers**

   ```bash
   docker-compose up -d --build
   ```

2. **Monitor Logs**

   Check the logs to ensure everything is working correctly.

   ```bash
   docker logs ssh-client-container
   ```

3. **Access the Backup Data**

   Your backups will be stored in the `data/sync` directory, organized per your configuration.

## Customization

### Adjust Backup Frequency

Modify the `crontab` file to change how often backups occur.

### Add More Servers

Add additional server configurations to the `remote_servers` array in `config.json`.

### Customize Gluetun Settings

Modify the `docker-compose.yml` file to change VPN providers or settings.

### Change Backup Retention

Update the `max_days` setting in `config.json` to keep backups for a longer or shorter period.

## Backup Directory Formats

You can specify the format for backup directory names using the `backup_name_format` parameter. This can be set per server in the `config.json` file under each server's configuration.

Possible values:

- **`"date_time"`**: Creates a new backup directory with the current date and time (e.g., `2024-10-19_12-00-00`).
- **`"date"`**: Creates a new backup directory with the current date (e.g., `2024-10-19`).
- **`"static"`**: Synchronizes to a single directory without creating date-based subdirectories. In this mode, the backup directory specified by `backup_name` will be fully synchronized with the remote server, including deletions.

**Example:**

```json
{
  "host": "yourserver.com",
  "user": "username",
  "path": "/remote/directory",
  "ssh_private_key": "/app/ssh/id_rsa_yourserver",
  "backup_name": "custom_backup_name",
  "backup_name_format": "static"
}
```

**Note**: When using `"static"` mode, the local backup directory will be fully synchronized with the remote directory, and files deleted on the remote server will also be deleted locally. This is useful when backup rotation is already handled on the remote server.

## Usage Scenarios

- **Secure Offsite Backups**

  Keep secure backups of your remote servers over a VPN to protect sensitive data during transit.

- **Synchronize with Remote Backup Rotation**

  If your remote server already handles backup rotation and you want to keep your local backup directory fully synchronized with it, you can use the `"static"` `backup_name_format`. This mode ensures that your local backup mirrors the remote directory exactly.

- **Multi-Server Backup Management**

  Easily back up multiple servers with different configurations and SSH keys.

- **Automated Backup Solution**

  Set up once and let the system handle backups automatically according to your schedule.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.
