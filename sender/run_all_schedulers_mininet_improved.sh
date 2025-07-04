#!/bin/bash

SCHEDULERS=("default" "roundrobin" "blest" "ecf")
SCRIPT_PATH="/home/lifistud32/Desktop/vm_test_throughput_scripts/sender/sender_logger_file.py"
ROUNDS=${1:-3}

# 函数：获取 sta1 的正确 PID
get_sta1_pid() {
    local pids=$(pgrep -f 'sta1')
    if [ -z "$pids" ]; then
        echo ""
        return 1
    fi
    
    # 如果有多个 PID，选择第一个
    echo "$pids" | head -1
}

# 函数：验证 PID 是否有效
validate_pid() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if ! kill -0 "$pid" 2>/dev/null; then
        return 1
    fi
    
    return 0
}

# 函数：等待并重试获取有效的 sta1 PID
get_valid_sta1_pid() {
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempting to find sta1 PID (attempt $attempt/$max_attempts)..."
        
        local pid=$(get_sta1_pid)
        if validate_pid "$pid"; then
            echo "Found valid sta1 PID: $pid"
            echo "$pid"
            return 0
        fi
        
        echo "Invalid or no PID found, waiting..."
        sleep 2
        ((attempt++))
    done
    
    echo ""
    return 1
}

# 主循环
success_count=0
total_tests=${#SCHEDULERS[@]}

echo "Starting scheduler tests with $ROUNDS rounds"
echo "Script path: $SCRIPT_PATH"
echo

for i in "${!SCHEDULERS[@]}"; do
    sched="${SCHEDULERS[$i]}"
    echo "==== Testing scheduler: $sched (Rounds: $ROUNDS) ===="

    # 设置调度器
    if sudo sysctl -w net.mptcp.mptcp_scheduler=$sched; then
        echo "Successfully set scheduler to $sched"
    else
        echo "[Error] Failed to set scheduler to $sched"
        continue
    fi

    # 设置发送标志
    if [ "$i" -eq 0 ]; then
        send_flag="true"
    else
        send_flag="false"
    fi

    # 获取有效的 sta1 PID
    sta1_pid=$(get_valid_sta1_pid)
    
    if [ -z "$sta1_pid" ]; then
        echo "[Error] Cannot find valid sta1 process for scheduler $sched"
        echo "Debug info:"
        echo "All processes containing 'sta1':"
        ps aux | grep sta1 | grep -v grep || echo "No sta1 processes found"
        echo "All mininet processes:"
        ps aux | grep mininet | grep -v grep || echo "No mininet processes found"
        continue
    fi

    echo "运行 sender_logger_file.py in sta1 (PID: $sta1_pid)..."
    
    # 构建并执行命令
    cmd="sudo mnexec -a $sta1_pid env SEND_ROUND_FLAG=$send_flag python3 $SCRIPT_PATH $ROUNDS"
    echo "Executing: $cmd"
    
    if eval "$cmd"; then
        echo "==== Scheduler $sched Test Done ===="
        ((success_count++))
    else
        status=$?
        echo "[Error] Scheduler $sched failed (exit $status)"
        
        # 额外的调试信息
        echo "Debug: Checking if sta1 PID is still valid..."
        if validate_pid "$sta1_pid"; then
            echo "PID $sta1_pid is still valid"
        else
            echo "PID $sta1_pid is no longer valid"
        fi
    fi

    echo
    
    # 如果不是最后一个测试，等待一段时间
    if [ $i -lt $((total_tests - 1)) ]; then
        echo "Waiting 30 seconds before next test..."
        sleep 30
    fi
done

echo
echo "========================================="
echo "Tests completed: $success_count/$total_tests schedulers tested successfully"

if [ $success_count -eq $total_tests ]; then
    echo "All tests passed!"
    exit 0
elif [ $success_count -gt 0 ]; then
    echo "Some tests passed, some failed."
    exit 1
else
    echo "All tests failed!"
    exit 2
fi
