#!/bin/bash

# Define variables
PEM_FILE=""
INSTANCE_USER="ubuntu"
INSTANCE_HOST=""
REMOTE_PATH=""
LOCAL_CONFIG_PATH=""

# Transfer the local config.json to the remote server
scp -i $PEM_FILE -o StrictHostKeyChecking=no $LOCAL_CONFIG_PATH $INSTANCE_USER@$INSTANCE_HOST:$REMOTE_PATH/config.json

# SSH into the instance and perform the operations
ssh -i $PEM_FILE -o StrictHostKeyChecking=no $INSTANCE_USER@$INSTANCE_HOST << EOF
    # Navigate to the directory
    cd $REMOTE_PATH

    # Restart the Docker containers
    sudo docker-compose down
    sudo docker-compose up -d
EOF

