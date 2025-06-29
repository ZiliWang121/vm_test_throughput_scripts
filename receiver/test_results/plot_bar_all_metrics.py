import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# 创建输出文件夹
os.makedirs("plots", exist_ok=True)

# 读取数据
df = pd.read_csv("recv_log.csv")
df['File'] = df['File'].str.replace('.file', '', regex=False)

# 文件排序字段
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

palette = {
    'default': '#1f77b4',
    'roundrobin': '#9467bd',
    'redundant': '#d62728',
    'blest': '#2ca02c',
    'ecf': '#8c564b',
    'reles': '#ff7f0e',
}

# 创建图形窗口
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

# 通用绘图函数
def draw_bar(metric, ylabel, ax):
    grouped = df.groupby(['File', 'Scheduler'], observed=True)[metric].mean().reset_index()
    pivot = grouped.pivot(index='File', columns='Scheduler', values=metric)
    pivot = pivot.reindex(sorted_files).dropna(how='all')
    colors = [palette.get(s, '#333333') for s in pivot.columns]
    pivot.plot(kind='bar', ax=ax, color=colors, legend=False)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.set_title(ylabel)
    ax.grid(True, linestyle="--", alpha=0.5)

draw_bar("AvgDelay(ms)", "Application Delay (ms)", axes[0])
draw_bar("Goodput(KB/s)", "Goodput (KB/s)", axes[1])
draw_bar("DownloadTime(s)", "Completion Time (s)", axes[2])
axes[2].set_xlabel("File Size")

# 设置统一图例
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, title="Scheduler", loc='upper right', bbox_to_anchor=(1.13, 0.98))

plt.tight_layout()
plt.savefig("plots/plot_bar_all_metrics.png", bbox_inches="tight")
plt.close()
print("[✓] Saved: plots/plot_bar_all_metrics.png")
