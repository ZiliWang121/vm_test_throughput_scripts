import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# 创建输出文件夹
os.makedirs("plots", exist_ok=True)

# 读取数据
df = pd.read_csv("recv_log.csv")
df['File'] = df['File'].str.replace('.file', '', regex=False)

# 排序文件大小
def extract_file_size(file_str):
    match = re.match(r'(\d+(?:\.\d+)?)([KMG]B)', file_str)
    if not match:
        return float('inf')
    num, unit = match.groups()
    num = float(num)
    return num * {"KB": 1, "MB": 1024, "GB": 1024 * 1024}[unit]

df['File_Size_Sort'] = df['File'].apply(extract_file_size)
sorted_files = df.sort_values('File_Size_Sort')['File'].unique()

# 通用折线图函数
def plot_line_per_file(metric, ylabel, prefix):
    grouped = df.groupby(['File', 'Scheduler'], observed=True)[metric].mean().reset_index()
    for f in sorted_files:
        subset = grouped[grouped['File'] == f]
        if subset.empty:
            continue
        plt.figure(figsize=(6, 4))
        plt.plot(subset['Scheduler'], subset[metric], marker='o', color='#1f77b4')
        plt.title(f"{ylabel} ({f})")
        plt.xlabel("Scheduler")
        plt.ylabel(ylabel)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        safe_f = f.replace('/', '_').replace(' ', '_')
        filename = f"plots/{prefix}_{safe_f}.png"
        plt.savefig(filename)
        plt.close()
        print(f"[✓] Saved: {filename}")

# 画每个指标每个文件的折线图
plot_line_per_file("AvgDelay(ms)", "Application Delay (ms)", "plot_delay_line")
plot_line_per_file("Goodput(KB/s)", "Goodput (KB/s)", "plot_goodput_line")
plot_line_per_file("DownloadTime(s)", "Completion Time (s)", "plot_time_line")
