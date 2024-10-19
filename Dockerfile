# Base image: Alpine
FROM alpine:latest

# Install required packages: python3, rsync, openssh-client, and bash
RUN apk add --no-cache python3 py3-pip rsync openssh-client bash

# Install Python packages
RUN pip3 install apscheduler --break-system-packages

# Create directories for ssh keys, config, and synced data
RUN mkdir -p /app/ssh /data/sync /app/config && chmod 700 /app/ssh

# Copy the Python script to manage rsync operations
COPY sync_rsync.py /usr/local/bin/sync_rsync.py

# Set execute permission for the script
RUN chmod +x /usr/local/bin/sync_rsync.py

# Start the Python script
CMD ["python3", "/usr/local/bin/sync_rsync.py"]
