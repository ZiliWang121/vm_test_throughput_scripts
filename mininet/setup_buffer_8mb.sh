#!/bin/bash

# ReLeS论文环境设置脚本 - 严格按论文VI-A节
# 论文: "ReLeS: A Neural Adaptive Multipath Scheduler based on Deep Reinforcement Learning"
# 只包含论文明确提到的设置，不添加任何额外"优化"

echo "=================================================="
echo "ReLeS论文环境设置 - 严格复刻论文VI-A节"
echo "=================================================="

# 检查root权限
if [[ $EUID -ne 0 ]]; then
    echo "错误: 需要root权限"
    echo "请使用: sudo $0"
    exit 1
fi

echo "=== 论文明确要求的设置 ==="

# 1. 缓冲区设置 - 论文原文: "We set both send and receive buffers to 8MB (by default)"
echo "设置发送和接收缓冲区为8MB (论文要求)..."

BUFFER_8MB=8388608  # 8MB = 8 * 1024 * 1024 bytes

# 核心缓冲区设置
echo $BUFFER_8MB > /proc/sys/net/core/wmem_max
echo $BUFFER_8MB > /proc/sys/net/core/wmem_default
echo $BUFFER_8MB > /proc/sys/net/core/rmem_max
echo $BUFFER_8MB > /proc/sys/net/core/rmem_default

# TCP缓冲区设置
echo "4096 65536 $BUFFER_8MB" > /proc/sys/net/ipv4/tcp_rmem
echo "4096 65536 $BUFFER_8MB" > /proc/sys/net/ipv4/tcp_wmem

# 2. MPTCP设置 - 论文使用: "MPTCP v0.92"
echo "启用MPTCP (论文使用v0.92)..."

if [ -f /proc/sys/net/mptcp/mptcp_enabled ]; then
    echo 1 > /proc/sys/net/mptcp/mptcp_enabled
    echo "✓ MPTCP已启用"
    
    # 如果支持MPTCP缓冲区设置
    if [ -f /proc/sys/net/mptcp/mptcp_rmem ]; then
        echo $BUFFER_8MB > /proc/sys/net/mptcp/mptcp_rmem
    fi
    if [ -f /proc/sys/net/mptcp/mptcp_wmem ]; then
        echo $BUFFER_8MB > /proc/sys/net/mptcp/mptcp_wmem
    fi
else
    echo "⚠ MPTCP未安装，需要支持MPTCP v0.92的内核"
fi

echo "=== 验证设置 ==="

# 验证缓冲区设置
wmem_max=$(cat /proc/sys/net/core/wmem_max)
rmem_max=$(cat /proc/sys/net/core/rmem_max)
wmem_default=$(cat /proc/sys/net/core/wmem_default)
rmem_default=$(cat /proc/sys/net/core/rmem_default)

echo "缓冲区设置验证:"
echo "  wmem_max: $wmem_max bytes ($(expr $wmem_max / 1024 / 1024)MB)"
echo "  rmem_max: $rmem_max bytes ($(expr $rmem_max / 1024 / 1024)MB)"
echo "  wmem_default: $wmem_default bytes ($(expr $wmem_default / 1024 / 1024)MB)"
echo "  rmem_default: $rmem_default bytes ($(expr $rmem_default / 1024 / 1024)MB)"

tcp_rmem=$(cat /proc/sys/net/ipv4/tcp_rmem)
tcp_wmem=$(cat /proc/sys/net/ipv4/tcp_wmem)
echo "  tcp_rmem: $tcp_rmem"
echo "  tcp_wmem: $tcp_wmem"

# 验证MPTCP
echo ""
echo "MPTCP状态:"
if [ -f /proc/sys/net/mptcp/mptcp_enabled ]; then
    mptcp_enabled=$(cat /proc/sys/net/mptcp/mptcp_enabled)
    echo "  MPTCP启用: $mptcp_enabled"
    
    if [ -f /proc/sys/net/mptcp/mptcp_scheduler ]; then
        scheduler=$(cat /proc/sys/net/mptcp/mptcp_scheduler)
        echo "  当前调度器: $scheduler"
    fi
else
    echo "  MPTCP: 未安装"
fi

# 检查是否符合论文要求
echo ""
if [ "$wmem_max" -eq "$BUFFER_8MB" ] && [ "$rmem_max" -eq "$BUFFER_8MB" ] && \
   [ "$wmem_default" -eq "$BUFFER_8MB" ] && [ "$rmem_default" -eq "$BUFFER_8MB" ]; then
    echo "✅ 缓冲区设置符合论文要求 (8MB)"
else
    echo "❌ 缓冲区设置不符合论文要求"
    exit 1
fi

if echo "$tcp_rmem $tcp_wmem" | grep -q "$BUFFER_8MB"; then
    echo "✅ TCP缓冲区包含8MB设置"
else
    echo "❌ TCP缓冲区设置有问题"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ 论文环境设置完成"
echo ""
echo "论文网络特性 (需在Mininet中用tc配置):"
echo "  WiFi: 8Mbps, 50ms RTT"
echo "  LTE: 16Mbps, 70ms RTT"
echo "  Ethernet: 80Mbps, 10ms RTT"
echo ""
echo "现在可以运行: sudo python3 large_difference_in_paper.py"
echo "=================================================="
