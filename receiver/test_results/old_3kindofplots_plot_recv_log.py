import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# 创建输出文件夹
os.makedirs("plots", exist_ok=True)

# 读取日志文件
df = pd.read_csv("recv_log.csv")

# 文件名处理：如 "64KB.file" → "64KB"
df['File'] = df['File'].str.replace('.file', '', regex=False)

# ✅ 自动提取数值和单位用于排序
def extract_file_size(file_str):
    match = re.match(r'(\d+(?:\.\d+)?)([KMG]B)', file_str)
    if not match:
        return float('inf')
    num, unit = match.groups()
    num = float(num)
    if unit == 'KB':
        return num
    elif unit == 'MB':
        return num * 1024
    elif unit == 'GB':
        return num * 1024 * 1024
    return float('inf')

# 添加排序用的数值字段
df['File_Size_Sort'] = df['File'].apply(extract_file_size)

# 排序并重新设置分类顺序
sorted_files = df.sort_values('File_Size_Sort')['File'].unique()
df['File'] = pd.Categorical(df['File'], categories=sorted_files, ordered=True)

# ✅ 学术风格配色（蓝、绿、红、棕、紫）
custom_palette = {
    'default': '#1f77b4',
    'roundrobin': '#9467bd',
    'redundant': '#d62728',
    'blest': '#2ca02c',
    'ecf': '#8c564b'
}

# -------------------------------
# 图 1：Application Delay (Boxplot)
# -------------------------------
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='File', y='AvgDelay(ms)', hue='Scheduler', palette=custom_palette)
plt.title("Application Delay by Scheduler and File Size")
plt.ylabel("Application Delay (ms)")
plt.xlabel("File Size")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(title="Scheduler", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("plots/plot_delay_boxplot.png")
plt.close()

# -------------------------------
# 图 2：Goodput (Grouped Bar)
# -------------------------------
grouped_goodput = df.groupby(['File', 'Scheduler'], observed=True)['Goodput(KB/s)'].mean().reset_index()
pivot_goodput = grouped_goodput.pivot(index='File', columns='Scheduler', values='Goodput(KB/s)')
pivot_goodput = pivot_goodput.reindex(sorted_files).dropna(how='all')

# 设置配色
colors = [custom_palette.get(s, '#333333') for s in pivot_goodput.columns]

# 绘图
pivot_goodput.plot(kind='bar', figsize=(10, 6), color=colors)
plt.title("Average Goodput by Scheduler and File Size")
plt.ylabel("Goodput (KB/s)")
plt.xlabel("File Size")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(title="Scheduler", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("plots/plot_goodput_bar.png")
plt.close()

# -------------------------------
# 图 3：Completion Time (Line per File)
# -------------------------------
grouped_time = df.groupby(['File', 'Scheduler'], observed=True)['DownloadTime(s)'].mean().reset_index()

# 每个文件大小生成一张折线图
for f in sorted_files:
    subset = grouped_time[grouped_time['File'] == f]
    if subset.empty:
        continue
    plt.figure(figsize=(6, 4))
    plt.plot(subset['Scheduler'], subset['DownloadTime(s)'], marker='o', color='#1f77b4')
    plt.title(f"Completion Time ({f})")
    plt.xlabel("Scheduler")
    plt.ylabel("Completion Time (s)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    safe_f = f.replace('/', '_').replace(' ', '_')
    plt.savefig(f"plots/plot_completion_time_{safe_f}.png")
    plt.close()
