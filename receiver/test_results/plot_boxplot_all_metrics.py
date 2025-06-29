import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# 三种指标的boxplot放到一张图中方便查看
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
df['File'] = pd.Categorical(df['File'], categories=sorted_files, ordered=True)

# 配色
palette = {
    'default': '#1f77b4',
    'roundrobin': '#9467bd',
    'redundant': '#d62728',
    'blest': '#2ca02c',
    'ecf': '#8c564b',
    'reles': '#ff7f0e',
}

# 创建三行一列大图：三个指标的 boxplot
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

sns.boxplot(data=df, x='File', y='AvgDelay(ms)', hue='Scheduler', palette=palette, ax=axes[0])
axes[0].set_title("Application Delay (ms)")
axes[0].set_xlabel("")
axes[0].grid(True, linestyle="--", alpha=0.5)

sns.boxplot(data=df, x='File', y='Goodput(KB/s)', hue='Scheduler', palette=palette, ax=axes[1])
axes[1].set_title("Goodput (KB/s)")
axes[1].set_xlabel("")
axes[1].grid(True, linestyle="--", alpha=0.5)

sns.boxplot(data=df, x='File', y='DownloadTime(s)', hue='Scheduler', palette=palette, ax=axes[2])
axes[2].set_title("Completion Time (s)")
axes[2].set_xlabel("File Size")
axes[2].grid(True, linestyle="--", alpha=0.5)

# 优化图例（只保留一个）
handles, labels = axes[0].get_legend_handles_labels()
for ax in axes:
    ax.legend_.remove()
fig.legend(handles, labels, title="Scheduler", loc='upper right', bbox_to_anchor=(1.13, 0.98))

plt.tight_layout()
plt.savefig("plots/plot_boxplot_all_metrics.png", bbox_inches="tight")
plt.close()
print("[✓] Saved: plots/plot_boxplot_all_metrics.png")
