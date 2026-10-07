"""探测国家统计局数据源的可用性。

目的：搞清楚三件事
  1. 这台电脑能不能访问国家统计局网站
  2. 它的数据接口（easyquery）能不能直接调用
  3. 返回的数据长什么结构

这个脚本不需要看懂每一行，跑一次看输出即可。
"""

import time

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

print("=" * 64)
print("国家统计局数据源探测")
print("=" * 64)

# ---------------------------------------------------------------
# 测试 1：能不能打开网站首页
# ---------------------------------------------------------------
print("\n[测试 1] 访问 data.stats.gov.cn 首页")
try:
    r = requests.get(
        "https://data.stats.gov.cn/",
        headers={"User-Agent": UA},
        timeout=20,
    )
    print(f"  状态码: {r.status_code}")
    print(f"  返回长度: {len(r.text)} 字符")
    print(f"  服务器: {r.headers.get('Server', '未知')}")
    reachable = r.status_code == 200
except Exception as exc:
    print(f"  失败: {type(exc).__name__}: {exc}")
    reachable = False

# ---------------------------------------------------------------
# 测试 2：调用数据接口（分省年度数据）
#
# easyquery 是国家统计局网站自己用的接口。
# 关键参数：
#   m=QueryData   表示"我要取数据"
#   dbcode=fsnd   分省年度数据（fen sheng nian du）
#   rowcode=reg   行 = 地区
#   colcode=sj    列 = 时间
#   dfwds         筛选条件，这里先不筛选，看它默认给什么
# ---------------------------------------------------------------
print("\n[测试 2] 调用 easyquery 数据接口（分省年度数据 fsnd）")

session = requests.Session()
session.headers.update({"User-Agent": UA})

try:
    # 先访问一次页面，让服务器下发 cookie（很多政府网站要求这样）
    session.get("https://data.stats.gov.cn/easyquery.htm?cn=E0103", timeout=20)
    print("  已获取 cookie:", dict(session.cookies))
except Exception as exc:
    print(f"  获取 cookie 失败: {type(exc).__name__}: {exc}")

url = "https://data.stats.gov.cn/easyquery.htm"
params = {
    "m": "QueryData",
    "dbcode": "fsnd",
    "rowcode": "reg",
    "colcode": "sj",
    "wds": "[]",
    "dfwds": "[]",
    "k1": str(int(time.time() * 1000)),
}

try:
    r = session.get(url, params=params, timeout=30)
    print(f"  状态码: {r.status_code}")
    print(f"  返回长度: {len(r.text)} 字符")
    print(f"  前 400 字符:")
    print("  " + r.text[:400].replace("\n", "\n  "))
except Exception as exc:
    print(f"  失败: {type(exc).__name__}: {exc}")

# ---------------------------------------------------------------
# 测试 3：取指标目录树，看看有哪些指标可用
# ---------------------------------------------------------------
print("\n[测试 3] 取分省年度数据的指标目录（前若干条）")
try:
    r = session.get(
        url,
        params={"m": "getTree", "dbcode": "fsnd", "wdcode": "zb", "id": "zb"},
        timeout=30,
    )
    print(f"  状态码: {r.status_code}, 长度: {len(r.text)}")
    print("  前 400 字符:")
    print("  " + r.text[:400].replace("\n", "\n  "))
except Exception as exc:
    print(f"  失败: {type(exc).__name__}: {exc}")

print("\n" + "=" * 64)
if reachable:
    print("结论：网站可访问。可以把探测结果发给 AI 助手，确定取数方案。")
else:
    print("结论：网站不可访问。需要改用其他取数方式（手动下载 / 换数据源）。")
print("=" * 64)
