import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# 创建输出文件夹
os.makedirs("plots", exist_ok=True)

# 读取日志文件
df = pd.read_csv("recv_log.csv")
df['File'] = df['File'].str.replace('.file', '', regex=False)

# 文件大小排序用
def extract_file_size(file_str):
    match = re.match(r'(\d+(?:\.\d+)?)([KMG]B)', file_str)
    if not match:
        return float('inf')
    num, unit = match.groups()
    num = float(num)
    return num * {"KB": 1, "MB": 1024, "GB": 1024 * 1024}[unit]

df['File_Size_Sort'] = df['File'].apply(extract_file_size)
sorted_files = df.sort_values('File_Size_Sort')['File'].unique()
df['File'] = pd.Categorical(df['File'], categories=sorted_files, ordered=True)

# 学术风格配色
palette = {
    'default': '#1f77b4',
    'roundrobin': '#9467bd',
    'redundant': '#d62728',
    'blest': '#2ca02c',
    'ecf': '#8c564b',
    'reles': '#ff7f0e',
}

# 通用绘图函数
def plot_grouped_bar(metric, ylabel, filename):
    grouped = df.groupby(['File', 'Scheduler'], observed=True)[metric].mean().reset_index()
    pivot = grouped.pivot(index='File', columns='Scheduler', values=metric)
    pivot = pivot.reindex(sorted_files).dropna(how='all')
    colors = [palette.get(s, '#333333') for s in pivot.columns]
    
    pivot.plot(kind='bar', figsize=(10, 6), color=colors)
    plt.title(f"{ylabel} by Scheduler and File Size")
    plt.ylabel(ylabel)
    plt.xlabel("File Size")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(title="Scheduler", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f"plots/{filename}")
    plt.close()
    print(f"[✓] Saved: plots/{filename}")

# 绘制三张柱状图
plot_grouped_bar("AvgDelay(ms)", "Application Delay (ms)", "plot_delay_bar.png")
plot_grouped_bar("Goodput(KB/s)", "Goodput (KB/s)", "plot_goodput_bar.png")
plot_grouped_bar("DownloadTime(s)", "Completion Time (s)", "plot_time_bar.png")
