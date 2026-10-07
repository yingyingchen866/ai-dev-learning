"""环境自检脚本 —— 检查 AI 开发所需的 Python 库是否就绪。

用法：
    python check_env.py

输出中带 [OK] 的是已安装，带 [--] 的是缺失。
"""

import importlib
import sys

# 每个库：(import 名, 用途说明, 最低要求版本)
REQUIRED = [
    ("pandas", "表格数据处理（分析经济数据的主力工具）", "2.0"),
    ("numpy", "数值计算", "1.24"),
    ("matplotlib", "画图", "3.7"),
    ("requests", "调用网络接口 / 下载数据", "2.28"),
    ("jupyter", "交互式笔记本（写分析记录）", "1.0"),
    ("openai", "调用大模型 API", "1.0"),
    ("streamlit", "把脚本变成网页应用", "1.30"),
    ("dotenv", "安全管理 API 密钥", "1.0"),
]

print("=" * 62)
print("Python 环境自检")
print("=" * 62)
print(f"解释器版本 : {sys.version.split()[0]}")
print(f"解释器路径 : {sys.executable}")
print("-" * 62)

ok, missing = 0, []

for module_name, purpose, _ in REQUIRED:
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "未知版本")
        print(f"[OK]  {module_name:<12} {version:<12} {purpose}")
        ok += 1
    except ImportError:
        print(f"[--]  {module_name:<12} {'未安装':<12} {purpose}")
        missing.append(module_name)

print("-" * 62)
print(f"已就绪 {ok} / {len(REQUIRED)}")

if missing:
    print()
    print("缺失的库可以用下面这条命令一次装好：")
    print(f"  python -m pip install {' '.join(missing)}")
else:
    print()
    print("全部就绪，可以开始第 2 周的数据处理练习了。")

print("=" * 62)
