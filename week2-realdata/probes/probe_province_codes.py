"""矩阵测试：找出省份代码的正确格式，以及哪个数据集支持分省。

测试两个数据集：
  A. 互联网主要指标发展情况      cid=53f522fb4b1a40ce90977a0b1cd94da1
  B. 企业信息化及电子商务情况    cid=c65e7e59f4434a8cb35fbf9f7c857e60

测试三种省份代码格式：
  1. 110000000000  (12位，和全国的 000000000000 等长)
  2. 110000        (6位，标准行政区划代码)
  3. 11            (2位)
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
        "Content-Type": "application/json",
    }
)
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

ROOT_ID = "c4d82af16c3d4f0cb4f09d4af7d5888e"

DATASETS = {
    "A_互联网": "53f522fb4b1a40ce90977a0b1cd94da1",
    "B_企业信息化及电子商务": "c65e7e59f4434a8cb35fbf9f7c857e60",
}

CODE_FORMATS = {
    "12位": "110000000000",
    "6位": "110000",
    "2位": "11",
}


def get_json(path, params=None, retries=3):
    for i in range(retries):
        try:
            r = session.get(f"{BASE}{path}", params=params, timeout=25)
            if r.status_code == 200:
                try:
                    return r.json()
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    return None


# ---------------------------------------------------------------
# 先看两个数据集各有哪些指标
# ---------------------------------------------------------------
for label, cid in DATASETS.items():
    print("=" * 70)
    print(f"数据集 {label}")
    print("=" * 70)
    j = get_json("/new/queryIndicatorsByCid", {"cid": cid, "dt": "", "name": ""})
    inds = []
    if j:
        data = j.get("data", {})
        inds = data.get("list", []) if isinstance(data, dict) else []
        for it in inds:
            print(f"  {it.get('i_showname')}")
    print(f"  -> 共 {len(inds)} 个指标")
    DATASETS[label] = (cid, [it["_id"] for it in inds[:3]])
    print()
    time.sleep(2)

# ---------------------------------------------------------------
# 矩阵测试
# ---------------------------------------------------------------
print("=" * 70)
print("矩阵测试：哪种省份代码格式能取到数据")
print("=" * 70)

results = {}
for label, (cid, ind_ids) in DATASETS.items():
    if not ind_ids:
        continue
    for fmt_name, code in CODE_FORMATS.items():
        payload = {
            "cid": cid,
            "indicatorIds": ind_ids,
            "das": [{"text": "北京", "value": code}],
            "dts": ["2023YY-2023YY"],
            "showType": "1",
            "rootId": ROOT_ID,
        }
        try:
            r = session.post(f"{BASE}/stream/esData", json=payload, timeout=40)
            res = r.json() if r.status_code == 200 else {}
            blocks = res.get("data", []) or []
            # 统计非空值里出现的地区名
            names = set()
            nonempty = 0
            for b in blocks:
                for v in b.get("values", []):
                    names.add(v.get("da_name"))
                    if str(v.get("value", "")).strip():
                        nonempty += 1
            status = f"地区={sorted(n for n in names if n)}  非空值={nonempty}"
        except Exception as exc:
            status = f"异常 {type(exc).__name__}"
        print(f"  {label:12s} 代码{fmt_name:5s}({code:12s}) -> {status}")
        results[f"{label}|{fmt_name}"] = status
        time.sleep(2)

print()
print("=" * 70)
print("结论：哪种组合能取到分省数据")
print("=" * 70)
for k, v in results.items():
    if "北京" in v and "非空值=0" not in v:
        print(f"  ✔ {k}  ->  {v}")
    else:
        print(f"    {k}  ->  {v}")

(OUT / "matrix_test_results.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
