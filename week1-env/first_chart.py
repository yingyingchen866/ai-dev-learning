"""用 pandas 处理表格 + matplotlib 画图 —— 第一次真正的数据分析练习。

用法：
    python first_chart.py

运行后会在 week1-env/output/ 目录下生成一张图表。

⚠️ 重要说明：
下面的数据是【示意数据】，只用来练习代码，绝对不要写进论文或简历。
真实分析请到国家统计局、中国信通院、各省统计年鉴等公开来源取数，
并把数据来源写清楚（这是学术诚信，也是简历上的加分项）。
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------
# 第 1 步：处理中文显示问题
# matplotlib 默认字体不含中文，不设置的话图上会显示成方框（□□□）。
# 这段代码会自动挑一个你电脑上已有的中文字体。
# ---------------------------------------------------------------
def setup_chinese_font() -> str | None:
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    candidates = [
        "Microsoft YaHei",   # 微软雅黑（Windows 自带）
        "SimHei",            # 黑体
        "SimSun",            # 宋体
        "Noto Sans CJK SC",
        "Source Han Sans SC",
    ]
    for name in candidates:
        if name in available:
            matplotlib.rcParams["font.sans-serif"] = [name]
            matplotlib.rcParams["axes.unicode_minus"] = False  # 让负号正常显示
            return name
    return None


font_used = setup_chinese_font()

# ---------------------------------------------------------------
# 第 2 步：准备数据
# pandas 的核心是 DataFrame —— 可以理解成"Python 里的 Excel 表格"。
# 这里手动构造一个小表，真实场景中通常是 pd.read_csv("文件.csv")。
# ---------------------------------------------------------------
data = {
    "省份": ["广东", "江苏", "山东", "浙江", "河南", "四川", "湖北", "福建"],
    "数字经济规模_万亿元": [6.5, 5.1, 3.9, 4.6, 2.4, 2.6, 2.5, 2.9],
    "同比增速_百分比": [11.2, 12.5, 10.1, 13.4, 9.8, 12.9, 11.6, 14.2],
}

df = pd.DataFrame(data)

# 派生一列：按规模排序后的名次
df["规模排名"] = df["数字经济规模_万亿元"].rank(ascending=False).astype(int)

print("=" * 64)
print("示意数据表（请勿直接引用）")
print("=" * 64)
print(df.to_string(index=False))
print()

# ---------------------------------------------------------------
# 第 3 步：用几行代码回答问题
# ---------------------------------------------------------------
print("--- 几个可以直接回答的问题 ---")
top = df.loc[df["数字经济规模_万亿元"].idxmax()]
print(f"规模最大的省份       : {top['省份']}（{top['数字经济规模_万亿元']} 万亿元）")

fastest = df.loc[df["同比增速_百分比"].idxmax()]
print(f"增速最快的省份       : {fastest['省份']}（{fastest['同比增速_百分比']}%）")

print(f"平均规模             : {df['数字经济规模_万亿元'].mean():.2f} 万亿元")
print(f"平均增速             : {df['同比增速_百分比'].mean():.2f}%")

# 相关系数：规模和增速之间有关系吗？
corr = df["数字经济规模_万亿元"].corr(df["同比增速_百分比"])
print(f"规模与增速的相关系数 : {corr:.3f}")
print("（注意：只有 8 个样本，相关系数没有统计意义，这里只是为了练习代码。）")
print()

# ---------------------------------------------------------------
# 第 4 步：画图并保存
# ---------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# 左图：横向柱状图，看规模
axes[0].barh(df["省份"], df["数字经济规模_万亿元"], color="#4C72B0")
axes[0].set_xlabel("数字经济规模（万亿元）")
axes[0].set_title("各省数字经济规模（示意数据）")
axes[0].invert_yaxis()  # 让第一名显示在最上面

# 右图：柱状图，看增速
axes[1].bar(df["省份"], df["同比增速_百分比"], color="#DD8452")
axes[1].set_ylabel("同比增速（%）")
axes[1].set_title("各省数字经济增速（示意数据）")
axes[1].tick_params(axis="x", rotation=45)

fig.suptitle("第一张图：用 pandas + matplotlib 做出来", fontsize=14)
fig.tight_layout()

# 保存到 output 目录
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)
save_path = output_dir / "first_chart.png"
fig.savefig(save_path, dpi=150, bbox_inches="tight")

print("=" * 64)
if font_used:
    print(f"中文字体 : {font_used}")
else:
    print("中文字体 : 未找到，图上中文可能显示为方框")
print(f"图表已保存到 : {save_path}")
print("=" * 64)
print()
print("试着改一改：把 data 里的数字换成别的，或者换几个省份，再跑一次。")
print("改动 → 运行 → 看结果，这就是学编程的全部循环。")
