import os
import json
import subprocess
import logging
import shutil
import time
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Load settings from JSON configuration file
CONFIG_PATH = '/app/config/config.json'

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

config = load_config()

# Extract values from the config
remote_servers = config['sync']['remote_servers']
sync_target_base = config['settings']['sync_target']
ssh_port = config['settings']['ssh_port']
max_days = config['settings']['max_days']
debug_mode = config['settings'].get('debug_mode', False)
ssh_connection_timeout = config['settings'].get('ssh_connection_timeout', 10)
rsync_max_retries = config['settings'].get('rsync_max_retries', 3)

# Function to create a server-specific subdirectory
def get_backup_directory(server):
    backup_name = server.get('backup_name', server['host'])
    backup_name_format = server.get('backup_name_format', 'date_time')  # Default to 'date_time' if not specified
    server_directory = os.path.join(sync_target_base, backup_name)

    if backup_name_format == 'date_time':
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_directory = os.path.join(server_directory, current_time)
    elif backup_name_format == 'date':
        current_time = datetime.now().strftime('%Y-%m-%d')
        backup_directory = os.path.join(server_directory, current_time)
    elif backup_name_format == 'static':
        backup_directory = server_directory
    else:
        logging.error(f"Invalid backup_name_format: {backup_name_format}. Using 'date_time' as default.")
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_directory = os.path.join(server_directory, current_time)

    # Create the backup directory if it doesn't exist
    os.makedirs(backup_directory, exist_ok=True)

    return backup_directory, backup_name_format

# Function to check and fix SSH key file permissions
def check_and_fix_ssh_key_permissions(ssh_private_key):
    try:
        key_file_stat = os.stat(ssh_private_key)
        # Check if permissions are 600
        if oct(key_file_stat.st_mode & 0o777) != '0o600':
            logging.info(f"Setting permissions of {ssh_private_key} to 600")
            os.chmod(ssh_private_key, 0o600)
    except Exception as e:
        logging.error(f"Error checking or setting permissions for {ssh_private_key}: {e}")
        if not debug_mode:
            raise

# Function to execute rsync command with retries
def run_rsync_with_retries(server, backup_directory, backup_name_format):
    remote_user = server['user']
    remote_host = server['host']
    ssh_private_key = server['ssh_private_key']
    paths = server.get('paths', [])

    # Check and fix SSH key permissions
    check_and_fix_ssh_key_permissions(ssh_private_key)

    # Ensure at least one path is specified
    if not paths:
        logging.error(f"No paths specified for server {remote_host}. Skipping.")
        return

    for remote_path in paths:
        rsync_command = [
            'rsync', '-avz',
            '--timeout=30',  # Rsync timeout in seconds
            '-e', f'ssh -p {ssh_port} -i {ssh_private_key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout={ssh_connection_timeout}',
            f'{remote_user}@{remote_host}:{remote_path}',
            backup_directory
        ]

        if backup_name_format == 'static':
            rsync_command.insert(1, '--delete')  # Insert '--delete' option after 'rsync'

        attempt = 1
        while attempt <= rsync_max_retries:
            logging.info(f"Attempt {attempt}/{rsync_max_retries}: Starting rsync from {remote_host}:{remote_path} to {backup_directory}")
            try:
                result = subprocess.run(rsync_command, check=True, capture_output=True, text=True)
                logging.info(f"Rsync completed successfully on attempt {attempt}:\n{result.stdout}")
                break  # Exit the retry loop if rsync is successful
            except subprocess.CalledProcessError as e:
                logging.error(f"Rsync failed on attempt {attempt} with error:\n{e.stderr}")
                if attempt == rsync_max_retries:
                    logging.error(f"Maximum retries reached for {remote_host}. Moving on to the next path.")
                    if not debug_mode:
                        break
                else:
                    logging.info(f"Retrying rsync for {remote_host} after a short delay...")
                    time.sleep(5)  # Wait 5 seconds before retrying
            attempt += 1

# Function to remove backups older than max_days
def clean_old_backups():
    cutoff_date = datetime.now() - timedelta(days=max_days)
    date_formats = ['%Y-%m-%d_%H-%M-%S', '%Y-%m-%d']  # Both date formats
    for server_dir in os.listdir(sync_target_base):
        server_dir_path = os.path.join(sync_target_base, server_dir)
        if os.path.isdir(server_dir_path):
            # Get backup_name_format for this server from the config
            server = next((s for s in remote_servers if s.get('backup_name', s['host']) == server_dir), None)
            if server:
                backup_name_format = server.get('backup_name_format', 'date_time')
            else:
                backup_name_format = 'date_time'  # Default

            # Skip cleaning for 'static' backup_name_format
            if backup_name_format == 'static':
                continue

            for backup_dir in os.listdir(server_dir_path):
                backup_dir_path = os.path.join(server_dir_path, backup_dir)
                if os.path.isdir(backup_dir_path):
                    dir_name = backup_dir
                    dir_date = None
                    for fmt in date_formats:
                        try:
                            dir_date = datetime.strptime(dir_name, fmt)
                            break  # Stop trying formats after a successful parse
                        except ValueError:
                            continue  # Try the next format
                    if dir_date:
                        if dir_date < cutoff_date:
                            logging.info(f"Removing old backup: {backup_dir_path}")
                            shutil.rmtree(backup_dir_path)
                    else:
                        logging.warning(f"Skipping directory {backup_dir_path} — unable to parse date")
        else:
            logging.warning(f"Skipping non-directory {server_dir_path}")

# Run rsync for each remote server
for server in remote_servers:
    try:
        backup_directory, backup_name_format = get_backup_directory(server)
        run_rsync_with_retries(server, backup_directory, backup_name_format)
    except Exception as e:
        logging.error(f"Error occurred during backup of {server['host']}: {e}")
        if debug_mode:
            logging.info("Debug mode enabled. Container will remain alive for inspection.")
        else:
            continue  # Move on to the next server

# Clean up old backups
try:
    clean_old_backups()
except Exception as e:
    logging.error(f"Error occurred during cleanup: {e}")
    if debug_mode:
        logging.info("Debug mode enabled. Container will remain alive for inspection.")

# If debug_mode is enabled, keep the container alive for debugging
if debug_mode:
    logging.info("Debug mode enabled. Sleeping to keep the container alive...")
    while True:
        time.sleep(3600)  # Sleep for 1 hour in an infinite loop
