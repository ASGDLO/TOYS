#!/bin/bash

# Define the array of servers and corresponding PEM files
declare -a SERVERS=(

)

# Define the local config path
LOCAL_CONFIG_PATH=""

# Ensure correct permissions for PEM files
for SERVER in "${SERVERS[@]}"; do
    IFS=' ' read -r -a SERVER_INFO <<< "$SERVER"
    PEM_FILE="${SERVER_INFO[0]}"
    chmod 400 "/home/ethan/Documents/AWS_KEY/$PEM_FILE"
done

# Function to handle each SSH connection, renaming and replacing config files
handle_ssh() {
    PEM_FILE="$1"
    SSH_INFO="$2"
    REMOTE_PATH="$3"

    echo "Connecting to $SSH_INFO to rename and replace config.json..."
    ssh -i "/home/ethan/Documents/AWS_KEY/$PEM_FILE" -o StrictHostKeyChecking=no -t $SSH_INFO << EOF
        if [ -f "$REMOTE_PATH/config.json" ]; then
            mv $REMOTE_PATH/config.json $REMOTE_PATH/config_temp.json
        fi
EOF

    echo "Transferring new config.json to $SSH_INFO..."
    scp -i "/home/ethan/Documents/AWS_KEY/$PEM_FILE" -o StrictHostKeyChecking=no $LOCAL_CONFIG_PATH "$SSH_INFO:$REMOTE_PATH/config.json"

    echo "Restarting Docker containers on $SSH_INFO..."
    ssh -i "/home/ethan/Documents/AWS_KEY/$PEM_FILE" -o StrictHostKeyChecking=no -t $SSH_INFO << EOF
        cd $REMOTE_PATH
        sudo docker-compose down
        sudo docker-compose up -d
EOF
}

# Loop through the servers and run each SSH command asynchronously
for SERVER in "${SERVERS[@]}"; do
    IFS=' ' read -r -a SERVER_INFO <<< "$SERVER"
    handle_ssh "${SERVER_INFO[0]}" "${SERVER_INFO[1]}" "${SERVER_INFO[2]}" &
done

# Wait for all background processes to complete
wait

echo "All SSH connections, file operations, and Docker operations completed."
