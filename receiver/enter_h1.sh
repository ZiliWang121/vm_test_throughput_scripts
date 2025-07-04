#!/bin/bash

# 简单进入 h1 节点脚本

# 查找 h1 进程 PID
get_h1_pid() {
    # 方法1: 查找 h1 bash 进程
    pid=$(ps aux | grep -E 'bash.*h1|h1.*bash' | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "$pid" ] && [ "$pid" != "0" ] && kill -0 "$pid" 2>/dev/null; then
        echo "$pid"
        return
    fi
    
    # 方法2: pgrep 但过滤掉无效的
    for pid in $(pgrep -f 'h1' 2>/dev/null); do
        if [ "$pid" != "0" ] && kill -0 "$pid" 2>/dev/null && [ -e "/proc/$pid/ns/net" ]; then
            echo "$pid"
            return
        fi
    done
}

# 获取 PID
h1_pid=$(get_h1_pid)

if [ -z "$h1_pid" ]; then
    echo "Error: Cannot find h1 process"
    echo "Debug: Available h1 processes:"
    ps aux | grep h1 | grep -v grep
    exit 1
fi

echo "Found h1 PID: $h1_pid"

# 进入 h1 节点
if [ $# -gt 0 ]; then
    # 执行指定命令
    sudo mnexec -a "$h1_pid" "$@"
else
    # 交互式 bash
    sudo mnexec -a "$h1_pid" bash
fi
