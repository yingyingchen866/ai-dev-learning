"""摸清国家统计局新接口的返回结构，并下钻"分省年度数据"目录树。

目标：找到「互联网普及率」「电子商务销售额」这类指标的分省数据 cid。

注意：请求之间必须加延时，否则会被限流（返回非 JSON 内容）。
"""

import json
import time
from pathlib import Path

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
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)


def get_json(path, params=None, retries=3, pause=1.5):
    """带重试和延时的 GET，返回解析后的 JSON；失败返回 None。"""
    for attempt in range(retries):
        try:
            r = session.get(f"{BASE}{path}", params=params, timeout=25)
            if r.status_code == 200:
                try:
                    return r.json()
                except json.JSONDecodeError:
                    print(f"    [限流/非JSON] 第 {attempt + 1} 次，等待后重试...")
            else:
                print(f"    [HTTP {r.status_code}] 第 {attempt + 1} 次")
        except Exception as exc:
            print(f"    [{type(exc).__name__}] 第 {attempt + 1} 次")
        time.sleep(pause * (attempt + 1))
    return None


# ===============================================================
# 第一部分：看清搜索结果的字段结构
# ===============================================================
print("=" * 70)
print("第一部分：搜索结果里有哪些字段")
print("=" * 70)

j = get_json("/query", {"search": "互联网普及率", "pagenum": 1, "pageSize": 5})
if j:
    (OUT / "search_sample.json").write_text(
        json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    inner = j.get("data", {})
    items = inner.get("data", []) if isinstance(inner, dict) else inner
    print(f"结果数: {len(items)}")
    if items:
        print("\n第 1 条的完整字段：")
        for k, v in items[0].items():
            print(f"  {k:24s} = {str(v)[:70]}")
        print("\n所有条目的关键字段：")
        for it in items:
            print(f"  {it.get('show_name')}")
            print(f"      type_text = {it.get('type_text')}")
            print(f"      cid       = {it.get('cid')}")
            print(f"      globalid  = {str(it.get('treeinfo_globalid'))[:60]}")
else:
    print("搜索失败")

time.sleep(2)

# ===============================================================
# 第二部分：下钻「分省年度数据」目录树
# ===============================================================
print()
print("=" * 70)
print("第二部分：下钻分省年度数据目录树")
print("=" * 70)

KEYWORDS = ["互联网", "电子商务", "软件", "信息传输", "电信", "邮电", "数字"]
found_leaves = []
visited = 0


def walk(pid, depth=0, max_depth=4):
    """递归下钻目录树，收集命中的叶子节点。"""
    global visited
    if depth > max_depth or len(found_leaves) >= 40:
        return
    j = get_json("/new/queryIndexTreeAsync", {"pid": pid, "code": "6"}, pause=1.2)
    if not j:
        return
    nodes = j.get("data", []) or []
    for node in nodes:
        visited += 1
        name = node.get("name", "")
        nid = node.get("_id")
        leaf = node.get("isLeaf")
        indent = "  " * depth

        if leaf:
            if any(kw in name for kw in KEYWORDS):
                found_leaves.append(
                    {
                        "name": name,
                        "cid": nid,
                        "sdate": node.get("sdate"),
                        "edate": node.get("edate"),
                    }
                )
                print(f"{indent}[叶子·命中] {name}  ({node.get('sdate')}-{node.get('edate')})")
                print(f"{indent}            cid={nid}")
        else:
            print(f"{indent}[目录] {name}")
            time.sleep(0.8)
            walk(nid, depth + 1, max_depth)


# 根节点
j = get_json("/new/queryIndexTreeAsync", {"pid": "", "code": "6"}, pause=1.5)
if j and j.get("data"):
    root = j["data"][0]
    print(f"根节点: {root.get('name')}  _id={root.get('_id')}")
    time.sleep(1)
    walk(root.get("_id"), depth=1)

print()
print("=" * 70)
print(f"共访问 {visited} 个节点，命中 {len(found_leaves)} 个数字经济相关数据集")
print("=" * 70)
for item in found_leaves:
    print(f"  {item['name']}")
    print(f"      cid={item['cid']}  时间范围 {item['sdate']}-{item['edate']}")

(OUT / "nbs_province_leaves.json").write_text(
    json.dumps(found_leaves, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"\n已保存: {OUT / 'nbs_province_leaves.json'}")
