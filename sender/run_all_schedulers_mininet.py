#!/usr/bin/env python3

import sys
import os
import time
import subprocess
from mininet.net import Mininet
from mininet.util import pmonitor

def set_mptcp_scheduler(scheduler):
    """设置 MPTCP 调度器"""
    try:
        result = subprocess.run(
            ['sudo', 'sysctl', '-w', f'net.mptcp.mptcp_scheduler={scheduler}'],
            capture_output=True, text=True, check=True
        )
        print(f"net.mptcp.mptcp_scheduler = {scheduler}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to set scheduler {scheduler}: {e}")
        return False

def run_scheduler_test(net, scheduler, rounds, script_path, is_first=False):
    """运行单个调度器测试"""
    print(f"==== Testing scheduler: {scheduler} (Rounds: {rounds}) ====")
    
    # 设置调度器
    if not set_mptcp_scheduler(scheduler):
        return False
    
    # 获取 sta1 节点
    sta1 = net.get('sta1')
    if sta1 is None:
        print("[Error] Cannot find sta1 node in network")
        return False
    
    # 设置环境变量
    send_flag = "true" if is_first else "false"
    env_vars = f'SEND_ROUND_FLAG={send_flag}'
    
    # 构建命令
    cmd = f'{env_vars} python3 {script_path} {rounds}'
    
    print("运行 sender_logger_file.py in sta1 ...")
    print(f"Command: {cmd}")
    
    try:
        # 在 sta1 节点上执行命令
        result = sta1.cmd(cmd)
        
        # 检查命令是否成功执行
        # 由于 sta1.cmd() 总是返回字符串，我们需要检查输出来判断是否成功
        if "Error" in result or "failed" in result.lower():
            print(f"[Error] Scheduler {scheduler} failed")
            print(f"Output: {result}")
            return False
        else:
            print(f"==== Scheduler {scheduler} Test Done ====")
            if result.strip():  # 如果有输出就显示
                print(f"Output: {result}")
            return True
            
    except Exception as e:
        print(f"[Error] Exception while running scheduler {scheduler}: {e}")
        return False

def main():
    # 配置
    SCHEDULERS = ["default", "roundrobin", "blest", "ecf"]
    SCRIPT_PATH = "/home/lifistud32/Desktop/vm_test_throughput_scripts/sender/sender_logger_file.py"
    
    # 从命令行参数获取轮数
    rounds = 3
    if len(sys.argv) >= 2:
        try:
            rounds = int(sys.argv[1])
        except ValueError:
            print("[Warning] Invalid round number argument. Using default (3).")
    
    print(f"Starting tests with {rounds} rounds")
    
    # 检查脚本文件是否存在
    if not os.path.exists(SCRIPT_PATH):
        print(f"[Error] Script file not found: {SCRIPT_PATH}")
        return 1
    
    # 尝试连接到现有的 Mininet 网络
    try:
        # 创建一个 Mininet 实例来访问现有网络
        # 注意：这假设网络已经在运行
        net = Mininet()
        
        # 检查是否能找到 sta1 节点
        # 由于网络已经存在，我们需要用不同的方法
        print("Attempting to connect to existing Mininet network...")
        
        # 使用 subprocess 来检查 mininet 是否在运行
        try:
            subprocess.run(['sudo', 'mn', '--version'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("[Error] Mininet does not seem to be running or accessible")
            return 1
        
        # 由于我们不能直接连接到现有网络，我们需要使用一个混合方法
        success_count = 0
        
        for i, scheduler in enumerate(SCHEDULERS):
            is_first = (i == 0)
            
            # 设置调度器
            if not set_mptcp_scheduler(scheduler):
                continue
            
            # 设置环境变量
            send_flag = "true" if is_first else "false"
            
            print(f"==== Testing scheduler: {scheduler} (Rounds: {rounds}) ====")
            print("运行 sender_logger_file.py in sta1 ...")
            
            try:
                # 使用改进的 mnexec 方法
                # 首先获取所有可能的 sta1 进程
                pgrep_result = subprocess.run(
                    ['pgrep', '-f', 'sta1'], 
                    capture_output=True, text=True
                )
                
                if pgrep_result.returncode != 0 or not pgrep_result.stdout.strip():
                    print("[Error] Cannot find sta1 process")
                    continue
                
                # 获取第一个 PID（最可能是正确的）
                pids = pgrep_result.stdout.strip().split('\n')
                sta1_pid = pids[0]
                
                print(f"Using sta1 PID: {sta1_pid}")
                
                # 使用 mnexec 执行命令
                cmd = [
                    'sudo', 'mnexec', '-a', sta1_pid,
                    'env', f'SEND_ROUND_FLAG={send_flag}',
                    'python3', SCRIPT_PATH, str(rounds)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
                
                if result.returncode == 0:
                    print(f"==== Scheduler {scheduler} Test Done ====")
                    success_count += 1
                    if result.stdout.strip():
                        print("Output:")
                        print(result.stdout)
                else:
                    print(f"[Error] Scheduler {scheduler} failed (exit {result.returncode})")
                    if result.stderr.strip():
                        print("Error output:")
                        print(result.stderr)
                
            except subprocess.TimeoutExpired:
                print(f"[Error] Scheduler {scheduler} test timed out")
            except Exception as e:
                print(f"[Error] Exception during {scheduler} test: {e}")
            
            print()
            time.sleep(30)  # 等待 30 秒再进行下一个测试
        
        print(f"\nTests completed. {success_count}/{len(SCHEDULERS)} schedulers tested successfully.")
        return 0 if success_count > 0 else 1
        
    except Exception as e:
        print(f"[Error] Failed to initialize: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
