import pandas as pd
import matplotlib.pyplot as plt
import os
import re

# 创建输出文件夹
os.makedirs("plots", exist_ok=True)

# 读取数据
df = pd.read_csv("recv_log.csv")
df['File'] = df['File'].str.replace('.file', '', regex=False)

# 排序字段
def extract_file_size(file_str):
    match = re.match(r'(\d+(?:\.\d+)?)([KMG]B)', file_str)
    if not match:
        return float('inf')
    num, unit = match.groups()
    num = float(num)
    return num * {"KB": 1, "MB": 1024, "GB": 1024 * 1024}[unit]

df['File_Size_Sort'] = df['File'].apply(extract_file_size)
sorted_files = df.sort_values('File_Size_Sort')['File'].unique()

palette = {
    'default': '#1f77b4',
    'roundrobin': '#9467bd',
    'redundant': '#d62728',
    'blest': '#2ca02c',
    'ecf': '#8c564b',
    'reles': '#ff7f0e',
}

# 创建三行一列子图
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

def plot_line(metric, ylabel, ax):
    grouped = df.groupby(['File', 'Scheduler'], observed=True)[metric].mean().reset_index()
    for scheduler in grouped['Scheduler'].unique():
        sub = grouped[grouped['Scheduler'] == scheduler]
        sub = sub.sort_values('File', key=lambda x: x.map({v: i for i, v in enumerate(sorted_files)}))
        ax.plot(sub['File'], sub[metric], marker='o', label=scheduler, color=palette.get(scheduler, '#333333'))
    ax.set_title(ylabel)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(True, linestyle="--", alpha=0.5)

plot_line("AvgDelay(ms)", "Application Delay (ms)", axes[0])
plot_line("Goodput(KB/s)", "Goodput (KB/s)", axes[1])
plot_line("DownloadTime(s)", "Completion Time (s)", axes[2])
axes[2].set_xlabel("File Size")

# 图例统一
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, title="Scheduler", loc='upper right', bbox_to_anchor=(1.13, 0.98))

plt.tight_layout()
plt.savefig("plots/plot_line_all_metrics.png", bbox_inches="tight")
plt.close()
print("[✓] Saved: plots/plot_line_all_metrics.png")
