# Base image: Alpine
FROM alpine:latest

# Set build-time argument for timezone
ARG TZ

# Install required packages: python3, rsync, openssh-client, bash, and tzdata
RUN apk add --no-cache python3 py3-pip rsync openssh-client bash tzdata

# Set the timezone
ENV TZ=${TZ}

# Install Python packages
RUN pip3 install --break-system-packages apscheduler pytz

# Create directories for ssh keys, config, and synced data
RUN mkdir -p /app/ssh /data/sync /app/config && chmod 700 /app/ssh

# Copy the Python script to manage rsync operations
COPY sync_rsync.py /usr/local/bin/sync_rsync.py

# Set execute permission for the script
RUN chmod +x /usr/local/bin/sync_rsync.py

# Start the Python script
CMD ["python3", "/usr/local/bin/sync_rsync.py"]
