#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.link import Link
from mininet.cli import CLI
from mininet.log import setLogLevel
import os
import sys

# 导入D-ITG测试模块
import final_ditg_test

# 你的原始函数保持不变
def check_for_real_interfaces_in_code():
    print("正在检查代码中是否误用了真实网卡名...")
    dangerous_ifaces = ['eno1', 'enp2s0f0', 'enp2s0f1']
    this_file = os.path.abspath(__file__)
    for iface in dangerous_ifaces:
        grep_cmd = f"grep -w '{iface}' {this_file}"
        result = os.popen(grep_cmd).read()
        if iface in result:
            print(f"警告：在脚本代码中发现引用真实网卡名 {iface}，已退出以保护系统！")
            sys.exit(1)
    print("脚本中未引用任何真实网卡，运行安全。")

def simple_dual_link_shared_switch():
    os.system('mn -c')
    setLogLevel('info')
    
    # 启用MPTCP
    print("尝试启用MPTCP...")
    os.system('echo 1 > /proc/sys/net/mptcp/mptcp_enabled 2>/dev/null || echo "MPTCP未安装，继续使用常规TCP"')
    
    net = Mininet(controller=Controller, link=Link, switch=OVSSwitch)

    print("创建节点")
    h1 = net.addHost('h1', ip='10.0.1.10')
    sta1 = net.addHost('sta1')
    s1 = net.addSwitch('s1')
    c0 = net.addController('c0')

    print("创建链路")
    net.addLink(sta1, s1, intfName1='sta1-eth0')
    net.addLink(sta1, s1, intfName1='sta1-eth1')
    net.addLink(h1, s1)

    print("启动网络")
    net.build()
    c0.start()
    s1.start([c0])

    print("配置 IP 和路由")
    sta1.setIP('10.0.1.1/24', intf='sta1-eth0')
    sta1.setIP('10.0.1.2/24', intf='sta1-eth1')

    # 设置策略路由
    sta1.cmd('ip rule add from 10.0.1.1 table 1')
    sta1.cmd('ip rule add from 10.0.1.2 table 2')
    sta1.cmd('ip route add 10.0.1.10/32 dev sta1-eth0 table 1')
    sta1.cmd('ip route add 10.0.1.10/32 dev sta1-eth1 table 2')
    sta1.cmd('ip route add default dev sta1-eth0')

    # 清除旧设置
    sta1.cmd('tc qdisc del dev sta1-eth0 root || true')
    sta1.cmd('tc qdisc del dev sta1-eth1 root || true')

    # 5G - 修正：eth0是WiFi，eth1是5G
    sta1.cmd('tc qdisc add dev sta1-eth0 root handle 1: tbf rate 8mbit burst 32kbit latency 100ms')
    sta1.cmd('tc qdisc add dev sta1-eth0 parent 1:1 handle 10: netem delay 50ms') #2ms distribution normal')
    
    # Wi-Fi 
    sta1.cmd('tc qdisc add dev sta1-eth1 root handle 1: tbf rate 16mbit burst 32kbit latency 100ms')
    sta1.cmd('tc qdisc add dev sta1-eth1 parent 1:1 handle 10: netem delay 70ms') #3ms distribution normal loss 0.5%')
    
    #print("=== 双链路异构环境配置完成 ===")
    #print("WiFi路径(sta1-eth0): 30Mbps,  25ms RTT, 0.6% loss")
    #print("5G路径(sta1-eth1):   100Mbps, 10ms RTT, 1.5% loss") 
    #print("总理论带宽: 130Mbps")
    #print()
    
    print("=== 基础测试命令 ===")
    print("连通性测试：")
    print("  sta1 ping -I 10.0.1.1 10.0.1.10  # WiFi路径")
    print("  sta1 ping -I 10.0.1.2 10.0.1.10  # 5G路径")
    print()
    print("单路径性能：")
    print("  h1 iperf3 -s &")
    print("  sta1 iperf3 -c 10.0.1.10 -B 10.0.1.1 -t 10  # WiFi")
    print("  sta1 iperf3 -c 10.0.1.10 -B 10.0.1.2 -t 10  # 5G")
    print()
    print("MPTCP性能测试：")
    print("  h1 iperf3 -s &")
    print("  sta1 iperf3 -c 10.0.1.10 -t 30  # 会自动使用MPTCP")
    print()
    
    # ============ 添加D-ITG MPTCP测试 ============
    print("=== 开始D-ITG MPTCP性能测试 ===")
    try:
        # 运行D-ITG MPTCP测试
        final_ditg_test.run_ditg_mptcp_test(net)
        print("=== D-ITG MPTCP测试完成 ===")
    except Exception as e:
        print(f"D-ITG测试出错: {e}")
        print("继续启动CLI...")
    
    print("\n=== 启动Mininet CLI ===")
    print("可以继续手动测试或使用以下命令:")
    print("  dump  # 查看节点信息") 
    print("  h1 iperf3 -s &")
    print("  sta1 iperf3 -c 10.0.1.10 -t 10")
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    simple_dual_link_shared_switch()
