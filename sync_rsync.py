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
backup_name_format = config['settings'].get('backup_name_format', 'date_time')  # Default to 'date_time'

# Function to create a server-specific subdirectory
def get_backup_directory(server):
    backup_name = server.get('backup_name', server['host'])
    if backup_name_format == 'date_time':
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    elif backup_name_format == 'date':
        current_time = datetime.now().strftime('%Y-%m-%d')
    else:
        logging.error(f"Invalid backup_name_format: {backup_name_format}. Using 'date_time' as default.")
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    server_directory = os.path.join(sync_target_base, backup_name)
    backup_directory = os.path.join(server_directory, current_time)
    
    # Create the backup directory if it doesn't exist
    os.makedirs(backup_directory, exist_ok=True)
    
    return backup_directory

# Function to execute rsync command with retries
def run_rsync_with_retries(remote_user, remote_host, remote_path, ssh_private_key, backup_directory):
    rsync_command = [
        'rsync', '-avz',
        '--timeout=30',  # Rsync timeout in seconds
        '-e', f'ssh -p {ssh_port} -i {ssh_private_key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout={ssh_connection_timeout}',
        f'{remote_user}@{remote_host}:{remote_path}', backup_directory
    ]

    attempt = 1
    while attempt <= rsync_max_retries:
        logging.info(f"Attempt {attempt}/{rsync_max_retries}: Starting rsync from {remote_host}:{remote_path} to {backup_directory}")
        try:
            result = subprocess.run(rsync_command, check=True, capture_output=True, text=True)
            logging.info(f"Rsync completed successfully on attempt {attempt}:\n{result.stdout}")
            return  # Exit the function if rsync is successful
        except subprocess.CalledProcessError as e:
            logging.error(f"Rsync failed on attempt {attempt} with error:\n{e.stderr}")
            if attempt == rsync_max_retries:
                logging.error(f"Maximum retries reached for {remote_host}. Moving on to the next server.")
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

# Run rsync for each remote server
for server in remote_servers:
    try:
        backup_directory = get_backup_directory(server)
        run_rsync_with_retries(
            server['user'],
            server['host'],
            server['path'],
            server['ssh_private_key'],
            backup_directory
        )
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
