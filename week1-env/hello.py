"""第一个 Python 程序 —— 验证工具链是否正常工作。

用法：
    python hello.py

如果能看到下面的输出，说明 Python 已经能正常运行，
可以进入第 2 周的数据处理练习了。
"""

import platform
import sys
from datetime import datetime

# 1. 最简单的一件事：把文字打印到屏幕上
print("你好，这是我写下的第一行 Python 代码。")

# 2. 看看我的电脑和 Python 是什么情况
print()
print("--- 运行环境 ---")
print(f"时间       : {datetime.now():%Y-%m-%d %H:%M:%S}")
print(f"操作系统   : {platform.system()} {platform.release()}")
print(f"Python 版本: {sys.version.split()[0]}")
print(f"解释器位置 : {sys.executable}")

# 3. 变量和 f-string：Python 里最常用的两样东西
name = "陈盈盈"
major = "数字经济"
weekly_hours = 5

print()
print("--- 我的学习档案 ---")
print(f"姓名       : {name}")
print(f"专业       : {major}")
print(f"每周投入   : {weekly_hours} 小时")
print(f"12 周合计  : {weekly_hours * 12} 小时")

# 4. 循环：把一件事重复做多次
print()
print("--- 12 周计划进度条 ---")
for week in range(1, 13):
    if week <= 1:
        status = "已完成 ← 你在这里"
    elif week <= 3:
        status = "数据素养"
    elif week <= 6:
        status = "调用大模型"
    elif week <= 10:
        status = "完整小产品"
    else:
        status = "作品集包装"
    bar = "█" * week + "░" * (12 - week)
    print(f"第 {week:>2} 周 {bar} {status}")

print()
print("环境验证通过。下一步：运行 first_chart.py 看第一张图。")
