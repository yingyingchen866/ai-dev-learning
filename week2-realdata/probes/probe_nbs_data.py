"""最后一步验证：能否按省份取出具体数值。

三步走：
  1. queryIndicatorsByCid  拿到指标 ID
  2. stream/esData         按省份 + 时间取数值
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

# 分省年度数据的根节点（上一轮已经确认）
ROOT_ID = "c4d82af16c3d4f0cb4f09d4af7d5888e"
# 互联网主要指标发展情况
CID_INTERNET = "53f522fb4b1a40ce90977a0b1cd94da1"


def get_json(path, params=None, retries=3):
    for i in range(retries):
        try:
            r = session.get(f"{BASE}{path}", params=params, timeout=25)
            if r.status_code == 200:
                try:
                    return r.json()
                except json.JSONDecodeError:
                    print(f"  [非JSON，可能限流] 重试 {i + 1}")
            else:
                print(f"  [HTTP {r.status_code}] 重试 {i + 1}")
        except Exception as exc:
            print(f"  [{type(exc).__name__}] 重试 {i + 1}")
        time.sleep(2 * (i + 1))
    return None


# ===============================================================
# 第 1 步：拿到「互联网主要指标发展情况」里的指标列表
# ===============================================================
print("=" * 70)
print("第 1 步：获取指标列表")
print("=" * 70)

j = get_json("/new/queryIndicatorsByCid", {"cid": CID_INTERNET, "dt": "", "name": ""})
indicators = []
if j:
    data = j.get("data", {})
    lst = data.get("list", []) if isinstance(data, dict) else []
    print(f"指标数: {len(lst)}\n")
    for it in lst:
        indicators.append(it)
        print(f"  {it.get('i_showname')}")
        print(f"      _id = {it.get('_id')}")
        print(f"      du  = {it.get('du')}   精度 dp={it.get('dp')}")
        mark = it.get("i_mark")
        if mark:
            print(f"      口径: {str(mark)[:80]}")
    (OUT / "internet_indicators.json").write_text(
        json.dumps(lst, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n已保存: {OUT / 'internet_indicators.json'}")
else:
    print("获取指标失败")

time.sleep(2)

# ===============================================================
# 第 2 步：按省份取数值
# ===============================================================
print()
print("=" * 70)
print("第 2 步：按省份取数值")
print("=" * 70)

if indicators:
    ind_ids = [it["_id"] for it in indicators[:4]]

    payload = {
        "cid": CID_INTERNET,
        "indicatorIds": ind_ids,
        "das": [
            {"text": "全国", "value": "000000000000"},
            {"text": "北京", "value": "110000000000"},
            {"text": "广东", "value": "440000000000"},
        ],
        "dts": ["2020YY-2024YY"],
        "showType": "1",
        "rootId": ROOT_ID,
    }

    print("请求体:")
    print(json.dumps(payload, ensure_ascii=False, indent=2)[:600])

    try:
        r = session.post(f"{BASE}/stream/esData", json=payload, timeout=40)
        print(f"\n状态码: {r.status_code}  长度: {len(r.content)}")
        if r.status_code == 200:
            try:
                res = r.json()
                print(f"success: {res.get('success')}  message: {res.get('message')}")
                (OUT / "esdata_sample.json").write_text(
                    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"已保存原始返回: {OUT / 'esdata_sample.json'}\n")

                rows = res.get("data", [])
                print(f"返回 {len(rows)} 个时间点")
                for block in rows[:6]:
                    print(f"\n  【{block.get('code')}】{block.get('name')}")
                    for v in block.get("values", []):
                        print(
                            f"      {v.get('da_name', '?'):6s} "
                            f"{str(v.get('i_showname'))[:28]:30s} "
                            f"= {v.get('value')} {v.get('du_name', '')}"
                        )
            except json.JSONDecodeError:
                print("返回不是 JSON，前 400 字符:")
                print(r.text[:400])
        else:
            print(r.text[:400])
    except Exception as exc:
        print(f"失败: {type(exc).__name__}: {exc}")

print()
print("=" * 70)
