"""测试国家统计局 2026 新版数据接口。

旧接口 easyquery.htm 被 WAF 拦截（403 UrlACL），
新版接口路径完全不同：/dg/website/publicrelease/web/external
如果这个能通，就能拿到真正的分省官方数据。

三步走策略（新版接口的设计）：
  1. queryIndexTreeAsync    遍历目录树，找到数据集 cid
  2. queryIndicatorsByCid   拿到指标 indicatorId
  3. stream/esData          取具体数值
"""

import json
import time

import requests

BASE = "https://data.stats.gov.cn/dg/website/publicrelease/web/external"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
session = requests.Session()
session.headers.update(
    {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://data.stats.gov.cn/",
    }
)

print("=" * 68)
print("国家统计局新版接口测试")
print("=" * 68)

# ---------------------------------------------------------------
# 测试 1：根节点目录树（code=6 表示分省年度数据）
# ---------------------------------------------------------------
print("\n[测试 1] 取分类树根节点 (code=6 分省年度)")
try:
    r = session.get(
        f"{BASE}/new/queryIndexTreeAsync",
        params={"pid": "", "code": "6"},
        timeout=25,
    )
    print(f"状态码: {r.status_code}  长度: {len(r.content)}")
    if r.status_code == 200:
        j = r.json()
        print(f"success: {j.get('success')}")
        nodes = j.get("data", [])
        print(f"顶层节点数: {len(nodes)}")
        for n in nodes[:15]:
            print(f"  isLeaf={str(n.get('isLeaf')):5s} {n.get('name')}")
    else:
        print("前 300 字符:", r.text[:300])
except Exception as exc:
    print(f"失败: {type(exc).__name__}: {exc}")

time.sleep(1)

# ---------------------------------------------------------------
# 测试 2：关键词搜索（找数字经济相关指标）
# ---------------------------------------------------------------
print("\n[测试 2] 关键词搜索")
for kw in ["互联网", "电子商务", "软件"]:
    try:
        r = session.get(
            f"{BASE}/query",
            params={"search": kw, "pagenum": 1, "pageSize": 5},
            timeout=25,
        )
        print(f"\n  关键词 '{kw}': 状态码 {r.status_code}, 长度 {len(r.content)}")
        if r.status_code == 200:
            j = r.json()
            inner = j.get("data", {})
            items = inner.get("data", []) if isinstance(inner, dict) else inner
            print(f"  结果数: {len(items) if isinstance(items, list) else '?'}")
            if isinstance(items, list):
                for it in items[:5]:
                    if isinstance(it, dict):
                        print(f"    - {it.get('show_name')}  [{it.get('type_text')}]")
    except Exception as exc:
        print(f"  失败: {type(exc).__name__}: {exc}")
    time.sleep(1)

# ---------------------------------------------------------------
# 测试 3：把原始返回存下来，方便细看结构
# ---------------------------------------------------------------
print("\n[测试 3] 保存原始返回以便分析结构")
from pathlib import Path

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
try:
    r = session.get(f"{BASE}/query", params={"search": "互联网", "pagenum": 1}, timeout=25)
    (OUT / "nbs_search_互联网.json").write_text(
        json.dumps(r.json(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  已保存: {OUT / 'nbs_search_互联网.json'}")
except Exception as exc:
    print(f"  失败: {type(exc).__name__}: {exc}")

print("\n" + "=" * 68)
