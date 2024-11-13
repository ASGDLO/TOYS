#!/bin/bash

while true; do
    # Activate your virtual environment if needed
    # source /path/to/venv/bin/activate

    # Navigate to the directory containing the scripts
    cd /home/ethan/Documents/GitHub/TOY/binance_auto_post/ || { echo "Failed to change directory."; exit 1; }

    # Function to run a script with timeout and log output
    run_with_timeout_and_log() {
        local timeout_duration=$1
        local script_command=$2
        local log_file=$3

        echo "Running: $script_command"
        timeout "$timeout_duration" $script_command > "$log_file" 2>&1
        local exit_code=$?

        if [ $exit_code -eq 124 ]; then
            echo "Error: $script_command timed out after $timeout_duration seconds."
        elif [ $exit_code -ne 0 ]; then
            echo "Error: $script_command exited with code $exit_code. Check $log_file for details."
        else
            echo "Success: $script_command completed successfully."
        fi

        return $exit_code
    }

    # Function to kill Chrome processes
    kill_chrome() {
        echo "Killing existing Chrome processes..."
        pkill chrome || echo "No Chrome processes to kill."
    }

    # Function to kill Google Drive processes
    kill_google_drive() {
        echo "Killing existing Google Drive processes..."
        pkill -f "Google Drive" || echo "No Google Drive processes to kill."
    }

    # Function to run a script with retries
    run_with_retries() {
        local max_retries=$1
        local retry_interval=$2
        shift 2
        local script_command="$@"

        local attempt=1
        while [ $attempt -le $max_retries ]; do
            echo "Attempt $attempt: Starting $script_command..."
            run_with_timeout_and_log 300 "$script_command" "${script_command##*/}.log"
            local exit_code=$?
            if [ $exit_code -eq 0 ]; then
                echo "$script_command completed successfully."
                return 0
            else
                echo "$script_command failed with exit code $exit_code."
                if [ $attempt -lt $max_retries ]; then
                    echo "Retrying in $retry_interval seconds..."
                    sleep $retry_interval
                fi
            fi
            attempt=$((attempt + 1))
        done

        echo "Failed to execute $script_command after $max_retries attempts."
        return 1
    }

    # Run chatgpt3_image.py with retry mechanism
    kill_chrome
    run_with_retries 3 10 "python3 chatgpt3_image.py"

    # Run main6_image.py with retry mechanism
    kill_chrome
    run_with_retries 3 10 "python3 main6_image.py"

    # Kill all Chrome and Google Drive processes after scripts have finished
    echo "Cleaning up processes..."
    kill_chrome
    kill_google_drive

    echo "All specified processes have been terminated."

    # Wait for an hour (3600 seconds) before the next loop iteration
    sleep 3600
done
