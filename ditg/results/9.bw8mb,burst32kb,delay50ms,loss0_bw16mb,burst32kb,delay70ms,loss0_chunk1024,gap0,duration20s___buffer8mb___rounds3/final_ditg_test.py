#!/usr/bin/env python3
"""
修复后的完整D-ITG MPTCP测试脚本
"""

import time
import subprocess
import csv
import re
import os
from collections import defaultdict

# ==================== 配置参数 ====================
SCHEDULERS = ["default", "roundrobin", "blest", "ecf"]
TEST_DURATION = 20  # 测试时长（秒）
# 【修改】：改为16KB块连续发送模式，不设置CBR速率
BLOCK_SIZE = 1024 #2048  #16384  # 16KB块大小
N_ROUNDS = 3        # 测试轮数
RECV_LOG = "/tmp/ditg_recv.log"
SEND_LOG = "/tmp/ditg_send.log"
CSV_LOG = "ditg_mptcp_results.csv"
CSV_SUMMARY = "ditg_mptcp_summary.csv"

def set_mptcp_scheduler(scheduler):
    """设置MPTCP调度器"""
    try:
        subprocess.run(['sudo', 'sysctl', '-w', f'net.mptcp.mptcp_scheduler={scheduler}'],
                      check=True, stdout=subprocess.DEVNULL)
        print(f"✓ MPTCP scheduler set to: {scheduler}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to set scheduler {scheduler}: {e}")
        return False

def parse_itg_logs(node):
    """解析D-ITG日志 - 修复版"""
    try:
        # 检查日志文件是否存在
        check_result = node.cmd(f'ls -la {RECV_LOG}')
        if 'No such file' in check_result:
            print(f"✗ Log file not found: {RECV_LOG}")
            return None
        
        print(f"  Log file check: {check_result.strip()}")
        
        # 使用正确的ITGDec格式
        output = node.cmd(f'ITGDec {RECV_LOG}')
        
        if not output or output.strip() == "":
            print("✗ ITGDec produced no output")
            return None
        
        print(f"  ITGDec output (前500字符):")
        print(f"  {output[:500]}...")
        
        # 提取关键指标
        throughput_mbps = 0
        avg_delay_ms = 0
        jitter_ms = 0
        packet_loss_percent = 0
        packets_sent = 0
        packets_received = 0
        # 【新增】：文件传输指标
        total_bytes_received = 0
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # 解析吞吐量: "Average bitrate = 7348.782851 Kbit/s"
            if 'Average bitrate' in line and '=' in line and 'Kbit/s' in line:
                match = re.search(r'Average bitrate\s*=\s*(\d+\.?\d*)\s*Kbit/s', line)
                if match:
                    kbps = float(match.group(1))
                    throughput_mbps = kbps / 1000  # Kbit/s -> Mbps
                    print(f"    ✓ 吞吐量: {kbps:.1f} Kbit/s = {throughput_mbps:.2f} Mbps")
                        
            # 解析平均延迟: "Average delay = 0.301179 s"
            elif 'Average delay' in line and '=' in line and line.count('=') == 1:
                match = re.search(r'Average delay\s*=\s*(\d+\.?\d*)\s*s', line)
                if match:
                    delay_s = float(match.group(1))
                    avg_delay_ms = delay_s * 1000  # s -> ms
                    print(f"    ✓ 平均延迟: {delay_s:.3f} s = {avg_delay_ms:.1f} ms")
                    
            # 解析抖动: "Average jitter = 0.001094 s"
            elif 'Average jitter' in line and '=' in line and line.count('=') == 1:
                match = re.search(r'Average jitter\s*=\s*(\d+\.?\d*)\s*s', line)
                if match:
                    jitter_s = float(match.group(1))
                    jitter_ms = jitter_s * 1000  # s -> ms
                    print(f"    ✓ 抖动: {jitter_s:.6f} s = {jitter_ms:.3f} ms")
                    
            # 解析总包数: "Total packets = 108418"
            elif 'Total packets' in line and '=' in line:
                match = re.search(r'Total packets\s*=\s*(\d+)', line)
                if match:
                    packets_received = int(match.group(1))
                    packets_sent = packets_received  # 接收端看到的就是成功的包
                    print(f"    ✓ 数据包: {packets_received}")
                    
            # 解析丢包: "Packets dropped = 0 (0.00 %)"
            elif 'Packets dropped' in line and '=' in line:
                match = re.search(r'Packets dropped\s*=\s*(\d+)', line)
                if match:
                    dropped = int(match.group(1))
                    if packets_received > 0:
                        total_sent = packets_received + dropped
                        packet_loss_percent = (dropped / total_sent) * 100
                    print(f"    ✓ 丢包: {dropped} ({packet_loss_percent:.2f}%)")
            
            # 【新增】：解析总字节数 "Total bytes = 67108864"
            elif 'Total bytes' in line and '=' in line:
                match = re.search(r'Total bytes\s*=\s*(\d+)', line)
                if match:
                    total_bytes_received = int(match.group(1))
                    print(f"    ✓ 传输字节: {total_bytes_received} 字节 ({total_bytes_received/1024/1024:.1f} MB)")
        
        result = {
            'throughput_mbps': throughput_mbps,
            'avg_delay_ms': avg_delay_ms,
            'jitter_ms': jitter_ms,
            'packet_loss_percent': packet_loss_percent,
            'packets_sent': packets_sent,
            'packets_received': packets_received,
            'total_bytes_received': total_bytes_received  # 【新增】
        }
        
        print(f"  ✓ 最终解析结果: 吞吐量={throughput_mbps:.2f}Mbps, 延迟={avg_delay_ms:.1f}ms, 传输={total_bytes_received/1024/1024:.1f}MB")
        return result
        
    except Exception as e:
        print(f"✗ Error parsing ITG logs: {e}")
        return None

def run_ditg_mptcp_test(net):
    """运行D-ITG MPTCP测试"""
    print("\n" + "="*60)
    print("D-ITG MPTCP连续发送性能测试开始")
    # 【修改】：更新显示信息
    print(f"测试时长: {TEST_DURATION} 秒")
    print(f"块大小: {BLOCK_SIZE/1024:.0f} KB")
    print("发送模式: 16KB块连续发送，能发多少发多少")
    print("="*60)
    
    # 获取节点
    sta1 = net.get('sta1')
    h1 = net.get('h1')
    
    if not sta1 or not h1:
        print("✗ 找不到sta1或h1节点")
        return False
    
    print("✓ 找到网络节点")
    print(f"  sta1: {sta1.IP()} (双链路发送端: WiFi + 5G)")
    print(f"  h1: {h1.IP()} (接收端)")
    
    # 准备CSV文件
    all_results = defaultdict(list)
    
    with open(CSV_LOG, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # 【修改】：更新CSV头部
        csv_writer.writerow([
            'Scheduler', 'Round', 'Throughput_Mbps', 'Avg_Delay_ms',
            'Jitter_ms', 'Packet_Loss_%', 'Packets_Sent', 'Packets_Received',
            'Total_Bytes_MB'  # 【新增】
        ])
        
        # 测试每个调度器
        for scheduler in SCHEDULERS:
            print(f"\n{'='*20} 测试 {scheduler} 调度器 {'='*20}")
            
            # 设置调度器
            if not set_mptcp_scheduler(scheduler):
                continue
            
            # 多轮测试
            for round_id in range(1, N_ROUNDS + 1):
                print(f"\n--- 第 {round_id}/{N_ROUNDS} 轮 ---")
                
                # 清理旧日志和进程
                print("清理环境...")
                h1.cmd('killall -9 ITGRecv 2>/dev/null')
                sta1.cmd('killall -9 ITGSend 2>/dev/null')
                h1.cmd(f'rm -f {RECV_LOG}')
                sta1.cmd(f'rm -f {SEND_LOG}')
                time.sleep(5)
                
                # 启动接收端
                print("启动接收端 (h1)...")
                h1.cmd(f'ITGRecv -l {RECV_LOG} &')
                time.sleep(10)  # 给接收端时间启动
                
                # 验证接收端启动
                recv_check = h1.cmd('ps aux | grep ITGRecv | grep -v grep')
                if recv_check.strip():
                    print("✓ 接收端启动成功")
                else:
                    print("✗ 接收端启动失败")
                    continue
                
                # 【修改】：启动发送端 - 使用连续发送模式
                print(f"启动发送端 (sta1) -> h1:10.0.1.10 (16KB块连续发送{TEST_DURATION}秒)...")
                test_duration_ms = TEST_DURATION * 1000
                send_result = sta1.cmd(f'ITGSend -a 10.0.1.10 -T TCP -c {BLOCK_SIZE} '
                                     f'-t {test_duration_ms} -x {SEND_LOG}')
                
                print(f"发送端输出: {send_result.strip()}")
                
                # 检查发送是否成功
                if 'Started sending' in send_result and 'Finished sending' in send_result:
                    print("✓ 发送完成")
                else:
                    print("✗ 发送可能失败")
                
                # 停止接收端
                print("停止接收端...")
                h1.cmd('killall -9 ITGRecv 2>/dev/null')
                time.sleep(5)
                
                # 解析结果
                print("解析测试结果...")
                results = parse_itg_logs(h1)
                if results and results['throughput_mbps'] > 0:
                    csv_writer.writerow([
                        scheduler, round_id,
                        results['throughput_mbps'],
                        results['avg_delay_ms'], 
                        results['jitter_ms'],
                        results['packet_loss_percent'],
                        results['packets_sent'],
                        results['packets_received'],
                        results['total_bytes_received']/1024/1024  # 【新增】：MB
                    ])
                    
                    all_results[scheduler].append(results)
                    
                    print(f"✓ 测试结果:")
                    print(f"    吞吐量: {results['throughput_mbps']:.2f} Mbps")
                    print(f"    传输量: {results['total_bytes_received']/1024/1024:.1f} MB")
                    print(f"    延迟: {results['avg_delay_ms']:.1f} ms")
                    print(f"    抖动: {results['jitter_ms']:.1f} ms") 
                    print(f"    丢包率: {results['packet_loss_percent']:.1f}%")
                    print(f"    发送/接收包: {results['packets_sent']}/{results['packets_received']}")
                else:
                    print("✗ 解析结果失败或无有效数据")
                
                # 轮次间隔
                if round_id < N_ROUNDS:
                    print("等待下一轮...")
                    time.sleep(20)
            
            # 调度器间隔
            print("等待下一个调度器...")
            time.sleep(30)
    
    # 生成汇总报告
    print(f"\n{'='*30} 测试总结 {'='*30}")
    with open(CSV_SUMMARY, 'w', newline='') as summary_file:
        summary_writer = csv.writer(summary_file)
        # 【修改】：更新汇总头部
        summary_writer.writerow([
            'Scheduler', 'Avg_Throughput_Mbps', 'Avg_Delay_ms',
            'Avg_Jitter_ms', 'Avg_Packet_Loss_%', 'Avg_Transfer_MB', 'Completed_Rounds'
        ])
        
        print(f"{'调度器':<12} {'平均吞吐(Mbps)':<15} {'平均传输(MB)':<12} {'平均延迟(ms)':<12} {'丢包率(%)':<10} {'完成轮数':<8}")
        print("-" * 80)
        
        for scheduler in SCHEDULERS:
            results = all_results[scheduler]
            if results:
                avg_throughput = sum(r['throughput_mbps'] for r in results) / len(results)
                avg_delay = sum(r['avg_delay_ms'] for r in results) / len(results)
                avg_jitter = sum(r['jitter_ms'] for r in results) / len(results)
                avg_loss = sum(r['packet_loss_percent'] for r in results) / len(results)
                avg_transfer = sum(r['total_bytes_received']/1024/1024 for r in results) / len(results)  # 【新增】
                
                summary_writer.writerow([
                    scheduler, avg_throughput, avg_delay, avg_jitter, avg_loss, avg_transfer, len(results)
                ])
                
                print(f"{scheduler:<12} {avg_throughput:>13.2f}   {avg_transfer:>10.1f}    {avg_delay:>10.1f}    {avg_loss:>8.1f}   {len(results):>6}")
            else:
                print(f"{scheduler:<12} {'无数据':<60}")
    
    print(f"\n✓ 详细结果保存到: {CSV_LOG}")
    print(f"✓ 汇总结果保存到: {CSV_SUMMARY}")
    
    # 显示MPTCP调度器对比结论
    if all_results:
        print(f"\n{'='*30} MPTCP调度器对比 {'='*30}")
        valid_results = {k: v for k, v in all_results.items() if v}
        if valid_results:
            # 找出最佳性能
            best_throughput = max(valid_results.keys(), 
                                key=lambda k: sum(r['throughput_mbps'] for r in valid_results[k])/len(valid_results[k]))
            best_delay = min(valid_results.keys(), 
                           key=lambda k: sum(r['avg_delay_ms'] for r in valid_results[k])/len(valid_results[k]))
            
            print(f"🏆 最高吞吐量调度器: {best_throughput}")
            print(f"🏆 最低延迟调度器: {best_delay}")
            
            # 【修改】：显示传输量对比
            print("📊 各调度器20秒传输性能:")
            for scheduler, results in valid_results.items():
                avg_thr = sum(r['throughput_mbps'] for r in results) / len(results)
                avg_transfer = sum(r['total_bytes_received']/1024/1024 for r in results) / len(results)
                print(f"   {scheduler}: {avg_thr:.2f} Mbps, 平均传输 {avg_transfer:.1f} MB")
    
    return True

# 使用说明
if __name__ == "__main__":
    print("请将此脚本集成到你的5g+wifi.py中")
    print("在CLI(net)之前添加:")
    print()
    print("import final_ditg_test")
    print("final_ditg_test.run_ditg_mptcp_test(net)")
    print("CLI(net)")
