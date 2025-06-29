import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
df['File'] = pd.Categorical(df['File'], categories=sorted_files, 
ordered=True)

# 配色：不同文件用不同颜色
palette = sns.color_palette("tab10", len(sorted_files))
file_colors = {f: palette[i] for i, f in enumerate(sorted_files)}

# 设置 3 行 1 列子图
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

def plot_metric(metric, ylabel, ax):
    grouped = df.groupby(['File', 'Scheduler'], 
observed=True)[metric].mean().reset_index()
    for f in sorted_files:
        sub = grouped[grouped['File'] == f]
        if sub.empty:
            continue
        sub = sub.sort_values('Scheduler')
        ax.plot(sub['Scheduler'], sub[metric], marker='o', label=f, 
color=file_colors[f])
    ax.set_title(ylabel)
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.5)

# 绘制三个指标的折线图
plot_metric("AvgDelay(ms)", "Application Delay (ms)", axes[0])
plot_metric("Goodput(KB/s)", "Goodput (KB/s)", axes[1])
plot_metric("DownloadTime(s)", "Completion Time (s)", axes[2])
axes[2].set_xlabel("Scheduler")

# 添加统一图例
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, title="File Size", loc='upper right', 
bbox_to_anchor=(1.13, 0.98))

plt.tight_layout()
plt.savefig("plots/plot_line_all_metrics_fixed.png", bbox_inches="tight")
plt.close()
print("[✓] Saved: plots/plot_line_all_metrics_fixed.png")
