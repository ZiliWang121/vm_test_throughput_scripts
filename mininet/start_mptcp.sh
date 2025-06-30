#!/bin/bash

echo "[Step 1] Loading MPTCP modules..."
for module in mptcp_balia mptcp_blest mptcp_coupled mptcp_ecf mptcp_ndiffports mptcp_netlink mptcp_olia mptcp_redundant mptcp_rr mptcp_wvegas; do
    sudo modprobe $module
done

# 关闭
echo N | sudo tee /sys/module/mptcp_reles/parameters/cwnd_limited
# echo Y | sudo tee /sys/module/mptcp_reles/parameters/cwnd_limited
# 再次查看
cat /sys/module/mptcp_reles/parameters/cwnd_limited   # 应回显 N

echo "[Step 2] Setting MPTCP congestion control algorithm to cubic..."
sudo sysctl -w net.ipv4.tcp_congestion_control=olia
#sudo sysctl -w net.ipv4.tcp_congestion_control=cubic
#sudo sysctl -w net.ipv4.tcp_congestion_control=cubic

echo "[Step 3] Enabling MPTCP..."
sudo sysctl -w net.mptcp.mptcp_enabled=1
sudo sysctl -w net.mptcp.mptcp_checksum=0
#sudo sysctl -w net.mptcp.mptcp_debug=0
sudo sysctl -w net.mptcp.mptcp_path_manager=fullmesh
#sudo sysctl -w net.mptcp.mptcp_scheduler=roundrobin
sudo sysctl -w net.mptcp.mptcp_scheduler=reles
# sudo sysctl -w net.mptcp.mptcp_path_manager=netlink
#sudo sysctl -w net.mptcp.mptcp_reinject=0
#sudo sysctl -w net.mptcp.mptcp_check_fallback=0

echo "===== UE Configuration Completed ====="
