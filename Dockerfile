# Base image: Alpine
FROM alpine:latest

# Install required packages: python3, rsync, openssh-client, bash, and cronie
RUN apk add --no-cache python3 py3-pip rsync openssh-client bash cronie

# Create directories for ssh keys, config, and synced data
RUN mkdir -p /app/ssh && mkdir -p /data/sync && mkdir -p /app/config && chmod 700 /app/ssh

# Copy the Python script to manage rsync operations
COPY sync_rsync.py /usr/local/bin/sync_rsync.py

# Copy the crontab file (customized via Docker Compose)
COPY crontab /etc/crontabs/root

# Set permissions for crontab
RUN chmod 600 /etc/crontabs/root

# Start cron and run the Python script
CMD ["/bin/bash", "-c", "crond && python3 /usr/local/bin/sync_rsync.py"]
