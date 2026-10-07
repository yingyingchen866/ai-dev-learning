"""分省数字经济数据分析。

输入：data/raw/nbs_digital_economy.csv（由 fetch_nbs_data.py 生成）
输出：output/ 下的图表 + 终端里的结论

分析思路（也是写任何数据分析项目的通用框架）：
    1. 先看数据长什么样 —— 有多少行、覆盖哪些年份、缺多少
    2. 整理成能分析的形状 —— 把「长表」转成「省份 × 年份」矩阵
    3. 回答具体问题 —— 排名、增长、差距
    4. 画图 —— 让人一眼看懂
    5. 说清局限 —— 数据能支持什么结论，不能支持什么结论

用法：
    python analyze_digital_economy.py
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------
# 0. 中文字体（不设置的话图上中文会变成方框）
# ---------------------------------------------------------------
def setup_chinese_font():
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"]:
        if name in available:
            matplotlib.rcParams["font.sans-serif"] = [name]
            matplotlib.rcParams["axes.unicode_minus"] = False
            return name
    return None


FONT = setup_chinese_font()

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "data" / "raw" / "nbs_digital_economy.csv"
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25

# ===============================================================
# 1. 读数据 + 体检
# ===============================================================
print("=" * 72)
print("分省数字经济数据分析")
print("=" * 72)

if not CSV_PATH.exists():
    print(f"\n找不到数据文件: {CSV_PATH}")
    print("请先运行: python fetch_nbs_data.py")
    raise SystemExit(1)

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df["年份"] = pd.to_numeric(df["年份"], errors="coerce").astype("Int64")
df["数值"] = pd.to_numeric(df["数值"], errors="coerce")
df = df.dropna(subset=["年份", "数值"])

print(f"\n[1] 数据体检")
print(f"    文件     : {CSV_PATH.name}")
print(f"    记录数   : {len(df)}")
print(f"    年份范围 : {int(df['年份'].min())} - {int(df['年份'].max())}")
print(f"    省份数   : {df['省份'].nunique()}")
print(f"    指标数   : {df['指标'].nunique()}")

print(f"\n    各指标数据量：")
coverage = (
    df.groupby("指标")
    .agg(记录数=("数值", "size"), 年份数=("年份", "nunique"), 省份数=("省份", "nunique"))
    .sort_values("记录数", ascending=False)
)
for name, row in coverage.iterrows():
    print(f"      {name:40s} {row['记录数']:4d} 条  "
          f"({row['年份数']} 年 × {row['省份数']} 省)")

# ---------------------------------------------------------------
# 选出主分析指标：优先用「电子商务销售额」
# ---------------------------------------------------------------
PREFERRED = ["电子商务销售额 (亿元)", "有电子商务交易活动的企业数比重 (%)"]
main_indicator = None
for p in PREFERRED:
    if p in set(df["指标"]):
        main_indicator = p
        break
if main_indicator is None:
    main_indicator = coverage.index[0]

main_unit = df.loc[df["指标"] == main_indicator, "单位"].iloc[0]
sub = df[df["指标"] == main_indicator]

print(f"\n[2] 主分析指标：{main_indicator}")
print(f"    单位     : {main_unit}")
print(f"    记录数   : {len(sub)}")

# ===============================================================
# 3. 转成「省份 × 年份」矩阵
# ===============================================================
pivot = sub.pivot_table(index="省份", columns="年份", values="数值", aggfunc="mean")
pivot = pivot.sort_index()
years = [int(y) for y in pivot.columns]
latest_year = max(years)
earliest_year = min(years)

print(f"\n[3] 省份 × 年份 矩阵：{pivot.shape[0]} 省 × {pivot.shape[1]} 年")
missing_rate = pivot.isna().mean().mean()
print(f"    缺失率   : {missing_rate:.1%}")

print(f"\n    {latest_year} 年数据完整度: "
      f"{pivot[latest_year].notna().sum()}/{len(pivot)} 个省份有值")

# ===============================================================
# 4. 回答具体问题
# ===============================================================
print("\n" + "=" * 72)
print(f"[4] 数据说了什么（{latest_year} 年，{main_unit}）")
print("=" * 72)

latest = pivot[latest_year].dropna().sort_values(ascending=False)
if latest.empty:
    print(f"  {latest_year} 年没有可用数据")
    latest = pivot[years[-1] if pivot.columns[-1] <= latest_year else years[0]].dropna()

national_total = latest.sum()
print(f"\n  31 省合计 : {national_total:,.0f} {main_unit}")
print(f"  平均值    : {latest.mean():,.1f}")
print(f"  中位数    : {latest.median():,.1f}")
print(f"  最大/最小 : {latest.max():,.0f} / {latest.min():,.0f}"
      f"  （相差 {latest.max() / max(latest.min(), 1e-9):,.1f} 倍）")

# 集中度：前 5 省占比
top5_share = latest.head(5).sum() / national_total
print(f"  前 5 省占比: {top5_share:.1%}   <- 集中度的直观度量")

print(f"\n  排名前 10：")
for i, (prov, val) in enumerate(latest.head(10).items(), 1):
    share = val / national_total
    bar = "█" * int(share * 120)
    print(f"    {i:2d}. {prov:5s} {val:10,.0f}  {share:5.1%}  {bar}")

print(f"\n  排名后 5：")
for i, (prov, val) in enumerate(latest.tail(5).items(), len(latest) - 4):
    print(f"    {i:2d}. {prov:5s} {val:10,.0f}  {val / national_total:5.1%}")

# 增长：首年到末年
if earliest_year != latest_year:
    print(f"\n  {earliest_year} -> {latest_year} 增长（仅有完整两端的省份）")
    growth = pd.DataFrame(
        {
            "首年": pivot[earliest_year],
            "末年": pivot[latest_year],
        }
    ).dropna()
    if not growth.empty:
        growth["倍数"] = growth["末年"] / growth["首年"].replace(0, np.nan)
        growth = growth.dropna().sort_values("倍数", ascending=False)
        print(f"    可比较省份数: {len(growth)}")
        if not growth.empty:
            print(f"    增长最快 5 省：")
            for prov, row in growth.head(5).iterrows():
                print(f"      {prov:5s} {row['首年']:>9,.0f} -> {row['末年']:>9,.0f}"
                      f"  （{row['倍数']:.2f} 倍）")
            print(f"    增长最慢 5 省：")
            for prov, row in growth.tail(5).iterrows():
                print(f"      {prov:5s} {row['首年']:>9,.0f} -> {row['末年']:>9,.0f}"
                      f"  （{row['倍数']:.2f} 倍）")

# ---------------------------------------------------------------
# 4b. 异常值检查（真实研究里最重要的一步之一）
#
# 为什么必须做：官方数据也会出现"某省突然腰斩"的情况，
# 这通常不是真实的经济现象，而是统计口径调整、调查范围变化，
# 或者数据录入问题。不检查就直接解读，会得出错误结论。
# ---------------------------------------------------------------
print("\n" + "=" * 72)
print("[4b] 异常值检查：同比大幅下滑的年份")
print("=" * 72)

anomalies = []
for prov in pivot.index:
    series = pivot.loc[prov].dropna()
    if len(series) < 2:
        continue
    years_sorted = sorted(series.index)
    for prev_y, cur_y in zip(years_sorted[:-1], years_sorted[1:]):
        prev_v, cur_v = series[prev_y], series[cur_y]
        if prev_v and prev_v > 0:
            change = cur_v / prev_v - 1
            if change < -0.30:  # 下滑超过 30% 视为异常
                anomalies.append(
                    {
                        "省份": prov,
                        "年份": cur_y,
                        "上年": prev_v,
                        "本年": cur_v,
                        "变化": change,
                    }
                )

if anomalies:
    print(f"\n  发现 {len(anomalies)} 处同比下滑超过 30% 的记录：\n")
    for a in sorted(anomalies, key=lambda x: x["变化"]):
        print(f"    {a['省份']:5s} {int(a['年份'])} 年  "
              f"{a['上年']:>9,.0f} -> {a['本年']:>9,.0f}  ({a['变化']:+.1%})")
    print("""
  怎么理解这些异常？三种可能，必须逐一排除后才能下结论：
    1. 统计口径调整 —— 调查范围、企业门槛、指标定义变了（最常见）
    2. 真实的经济冲击 —— 确有事件导致规模下降
    3. 数据错误 —— 录入或传输问题
  排查办法：查该指标的「统计口径说明」字段（接口的 i_mark），
  或对照国家统计局同期发布的统计公报。绝不能直接写成"某省数字经济负增长"。""")
else:
    print("\n  未发现同比下滑超过 30% 的记录。")

# ===============================================================
# 5. 画图
# ===============================================================
print("\n" + "=" * 72)
print("[5] 生成图表")
print("=" * 72)

# --- 图 1：最新一年各省排名 ---
fig, ax = plt.subplots(figsize=(10, 9))
data = latest.sort_values(ascending=True)
colors = ["#C44E52" if v >= latest.quantile(0.75) else "#4C72B0" for v in data.values]
ax.barh(data.index, data.values, color=colors)
ax.set_xlabel(f"{main_indicator}")
ax.set_title(f"{latest_year} 年各省{main_indicator.split(' (')[0]}排名\n"
             f"（红色为前 25%，合计 {national_total:,.0f} {main_unit}）", fontsize=13)
for i, (prov, v) in enumerate(data.items()):
    ax.text(v, i, f" {v:,.0f}", va="center", fontsize=8)
ax.margins(x=0.12)
fig.tight_layout()
p1 = OUT_DIR / "chart1_province_ranking.png"
fig.savefig(p1, bbox_inches="tight")
plt.close(fig)
print(f"  已保存: {p1.name}")

# --- 图 2：几个代表省份的时间趋势 ---
fig, ax = plt.subplots(figsize=(11, 6))
# 挑 6 个代表：规模前 4 + 首尾对比用 2 个
picks = list(latest.head(4).index)
for extra in ["西藏", "青海", "宁夏", "海南", "甘肃"]:
    if extra in pivot.index and extra not in picks:
        picks.append(extra)
    if len(picks) >= 6:
        break

for prov in picks:
    series = pivot.loc[prov].dropna()
    if len(series) >= 2:
        ax.plot(series.index.astype(int), series.values, marker="o", label=prov, linewidth=2)

ax.set_xlabel("年份")
ax.set_ylabel(f"{main_indicator}")
ax.set_title(f"代表省份的{main_indicator.split(' (')[0]}变化趋势", fontsize=13)
ax.legend()
fig.tight_layout()
p2 = OUT_DIR / "chart2_trend.png"
fig.savefig(p2, bbox_inches="tight")
plt.close(fig)
print(f"  已保存: {p2.name}")

# --- 图 3：所有省份的热力图 ---
if pivot.shape[1] >= 2:
    fig, ax = plt.subplots(figsize=(11, 10))
    plot_data = pivot.loc[latest.sort_values(ascending=False).index]
    im = ax.imshow(plot_data.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(plot_data.columns)))
    ax.set_xticklabels([int(c) for c in plot_data.columns], rotation=45)
    ax.set_yticks(range(len(plot_data.index)))
    ax.set_yticklabels(plot_data.index, fontsize=8)
    ax.set_title(f"各省{main_indicator.split(' (')[0]}热力图（按 {latest_year} 年规模排序）",
                 fontsize=13)
    ax.grid(False)
    fig.colorbar(im, ax=ax, label=main_unit, shrink=0.6)
    fig.tight_layout()
    p3 = OUT_DIR / "chart3_heatmap.png"
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    print(f"  已保存: {p3.name}")

# --- 图 4：如果有企业电商参与率，做个对比散点图 ---
participation = "有电子商务交易活动的企业数比重 (%)"
if participation in set(df["指标"]) and main_indicator != participation:
    p_sub = df[df["指标"] == participation]
    p_pivot = p_sub.pivot_table(index="省份", columns="年份", values="数值", aggfunc="mean")
    if p_pivot.shape[1] >= 1:
        # 两个指标的年份取交集，用最晚的公共年份对比
        common_years = [y for y in pivot.columns if y in p_pivot.columns]
        if common_years:
            cmp_year = max(common_years)
            merged = pd.DataFrame(
                {"规模": pivot[cmp_year], "参与率": p_pivot[cmp_year]}
            ).dropna()
        else:
            merged = pd.DataFrame()
        if len(merged) >= 5:
            fig, ax = plt.subplots(figsize=(9, 7))
            ax.scatter(merged["规模"], merged["参与率"], s=70, color="#4C72B0", alpha=0.8)
            for prov, row in merged.iterrows():
                ax.annotate(prov, (row["规模"], row["参与率"]),
                            fontsize=8, xytext=(4, 3), textcoords="offset points")
            corr = merged["规模"].corr(merged["参与率"])
            ax.set_xlabel(f"{main_indicator}")
            ax.set_ylabel(participation)
            ax.set_title(f"{int(cmp_year)} 年：企业电商规模 vs 企业电商参与率\n"
                         f"相关系数 r = {corr:.2f}（n={len(merged)}，仅供观察，未做检验）",
                         fontsize=12)
            fig.tight_layout()
            p4 = OUT_DIR / "chart4_scatter.png"
            fig.savefig(p4, bbox_inches="tight")
            plt.close(fig)
            print(f"  已保存: {p4.name}")

# ===============================================================
# 6. 局限说明（研究规范：不能过度解读）
# ===============================================================
print("\n" + "=" * 72)
print("[6] 这份分析能说明什么，不能说明什么")
print("=" * 72)
print("""
  能说明：
    - 各省在「""" + main_indicator + """」上的规模差异与集中程度
    - 该指标随时间的变化方向

  不能说明：
    - 不能等同于「数字经济发展水平」。单一指标只是代理变量，
      真正的数字经济测度需要构建多维度指标体系（基础设施、产业、
      应用、创新等）并说明权重设定。
    - 不能做因果判断。"广东规模大"不等于"广东模式更有效"，
      规模差异同时受人口、经济体量、产业结构影响。
    - 未做价格平减、未控制人口规模，所以是名义值和总量值。
    - 缺失值已跳过，未插值，因此省际比较要留意各省年份覆盖是否一致。

  下一步可以做什么：
    - 用人口或 GDP 做分母，改看「人均/地均」指标
    - 构建多维指标体系，做省际数字经济综合排名
    - 与其他数据集（如互联网普及率）做相关分析
    - 加入时间维度做面板回归（需要更强的计量方法）
""")

print("=" * 72)
print(f"完成。图表在: {OUT_DIR}")
print("=" * 72)
