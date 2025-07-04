#!/bin/bash

# List of schedulers to test
SCHEDULERS=("default" "roundrobin" "blest" "ecf")
#SCHEDULERS=("blest" "ecf")

# Network namespace name (assumes MPTCP interface is inside this namespace)
#NS_NAME="ns-mptcp"

# Path to the Python sender script
# SCRIPT_PATH="/home/vagrant/sender_logger_file.py"
SCRIPT_PATH="sender_logger_file.py"

# Number of test rounds (can be passed as argument, default is 3)
ROUNDS=${1:-3}

# Iterate through each scheduler
for i in "${!SCHEDULERS[@]}"; do
    sched="${SCHEDULERS[$i]}"
    echo "==== Testing scheduler: $sched (Rounds: $ROUNDS) ===="

    # Set the MPTCP scheduler via sysctl
    sysctl -w net.mptcp.mptcp_scheduler=$sched

    # Only for the first scheduler: send the number of rounds to the receiver
    if [ "$i" -eq 0 ]; then
        export SEND_ROUND_FLAG=true
    else
        export SEND_ROUND_FLAG=false
    fi

    # Execute the sender script in the specified network namespace
    # SEND_ROUND_FLAG is passed as an environment variable
    env SEND_ROUND_FLAG=$SEND_ROUND_FLAG python3 $SCRIPT_PATH $ROUNDS
    status=$?

    # Check if the script execution was successful
    if [ $status -ne 0 ]; then
        echo "[Error] Scheduler $sched failed to complete sending (exit code $status)"
    else
        echo "==== Scheduler $sched Test Done ===="
    fi
    echo
    sleep 30  # Wait between tests to avoid congestion or overlap
done
