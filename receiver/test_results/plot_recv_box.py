import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# ✅ 创建输出文件夹
os.makedirs("plots", exist_ok=True)

# ✅ 读取 recv_log.csv 数据
df = pd.read_csv("recv_log.csv")
df['File'] = df['File'].str.replace('.file', '', regex=False)

# ✅ 文件大小排序函数
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

# ✅ 学术风格调度器配色
custom_palette = {
    'default': '#1f77b4',
    'roundrobin': '#9467bd',
    'redundant': '#d62728',
    'blest': '#2ca02c',
    'ecf': '#8c564b',
    'reles': '#ff7f0e'
}

# ✅ 通用 boxplot 绘图函数
def draw_boxplot(metric_col, ylabel, filename):
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='File', y=metric_col, hue='Scheduler', palette=custom_palette)
    plt.title(f"{ylabel} by Scheduler and File Size")
    plt.ylabel(ylabel)
    plt.xlabel("File Size")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(title="Scheduler", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f"plots/{filename}")
    plt.close()
    print(f"[✓] Saved: plots/{filename}")

# ✅ 绘制三个图（全部使用 boxplot）
draw_boxplot("AvgDelay(ms)", "Application Delay (ms)", "plot_delay_boxplot.png")
draw_boxplot("Goodput(KB/s)", "Goodput (KB/s)", "plot_goodput_boxplot.png")
draw_boxplot("DownloadTime(s)", "Completion Time (s)", "plot_time_boxplot.png")
