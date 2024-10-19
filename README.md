# SecureRsyncVPNBackup

A Docker-based solution for performing secure `rsync` backups over a VPN network using Gluetun. This setup ensures privacy and security by routing all backup traffic through a VPN connection.

## Features

- **Secure Backups over VPN**: All `rsync` operations are performed over a VPN connection provided by Gluetun.
- **Multiple Server Support**: Backup multiple remote servers, each with its own SSH key and configuration.
- **Per-Server Scheduling**: Configure individual backup intervals for each server directly in `config.json` using hours and minutes.
- **Multiple Paths per Server**: Define multiple files or directories to back up from each remote server.
- **Preserve Directory Hierarchy**: Optionally preserve the full directory hierarchy when backing up.
- **Customizable Backup Directory Structure**: Define custom names for backup directories and choose between date, date-time, or static formats.
- **Automated Retention Policy**: Automatically delete backups older than a specified number of days.
- **Flexible Configuration**: All settings are managed via `config.json`, allowing easy customization without modifying code.

## Configuration

### `config.json`

This file contains all the settings for your backups.

- **`remote_servers`**: An array of servers to back up.
  - **`host`**: The hostname or IP address of the remote server.
  - **`user`**: The SSH username for the remote server.
  - **`paths`**: An array of files or directories on the remote server to back up.
  - **`ssh_private_key`**: Path to the SSH private key inside the Docker container.
  - **`backup_name`**: Custom name for the backup directory.
  - **`backup_name_format`**: Format for backup directory names.
  - **`preserve_paths`**: Set to `true` to preserve the full directory hierarchy.
  - **`schedule`**: Scheduling settings for the backup.
    - **`interval_hours`**: Interval in hours between backups.
    - **`interval_minutes`**: Interval in minutes between backups.

**Example with Scheduling:**

```json
{
  "host": "X.X.X.X",
  "user": "root",
  "paths": ["/opt/backup", "/root", "/etc/systemd"],
  "ssh_private_key": "/app/ssh/key1",
  "backup_name": "backup1",
  "backup_name_format": "static",
  "preserve_paths": true,
  "schedule": {
    "interval_hours": 2,
    "interval_minutes": 30  // Backup every 2 hours and 30 minutes
  }
}
```

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

---

**Note**: The backups can now be scheduled with intervals specified in both hours and minutes, providing more precise control over backup timing.

---

## License

This project is licensed under the MIT License.
