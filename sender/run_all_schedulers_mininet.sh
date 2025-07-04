#!/bin/bash

SCHEDULERS=("default" "roundrobin" "blest" "ecf")
#SCHEDULERS=("ecf")
SCRIPT_PATH="/home/lifistud32/Desktop/vm_test_throughput_scripts/sender/sender_logger_file.py"  # 必须确保 sta1 中这个路径存在该文件
ROUNDS=${1:-3}

for i in "${!SCHEDULERS[@]}"; do
    sched="${SCHEDULERS[$i]}"
    echo "==== Testing scheduler: $sched (Rounds: $ROUNDS) ===="

    # 在宿主机上设置调度器（需要 root）
    sudo sysctl -w net.mptcp.mptcp_scheduler=$sched

    if [ "$i" -eq 0 ]; then
        send_flag="true"
    else
        send_flag="false"
    fi

    # 用 mnexec 进入 sta1 的进程空间并运行脚本
    echo "运行 sender_logger_file.py in sta1 ..."
    sudo mnexec -a $(pgrep -f 'sta1') env SEND_ROUND_FLAG=$send_flag python3 $SCRIPT_PATH $ROUNDS
    status=$?

    if [ $status -ne 0 ]; then
        echo "[Error] Scheduler $sched failed (exit $status)"
    else
        echo "==== Scheduler $sched Test Done ===="
    fi

    echo
    sleep 30
done
