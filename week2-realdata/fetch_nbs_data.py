"""从国家统计局新版接口抓取分省数字经济相关数据。

数据来源
--------
国家统计局「国家数据」平台 · 分省年度数据
接口：https://data.stats.gov.cn/dg/website/publicrelease/web/external
本脚本只做「取数」，不做分析。分析见 analyze_digital_economy.py。

为什么单独写一个取数脚本？
    这样别人 clone 你的仓库后，跑一次就能复现整个数据获取过程，
    而不是收到一个来路不明的 Excel。这是可复现研究的基本要求。

用法
----
    python fetch_nbs_data.py

输出
----
    data/raw/nbs_digital_economy.csv    整齐的「长表」格式
    data/raw/数据说明.md                 数据出处记录
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path

import requests

# ===============================================================
# 配置区：想改抓取范围，只改这里
# ===============================================================

BASE = "https://data.stats.gov.cn/dg/website/publicrelease/web/external"
ROOT_ID = "c4d82af16c3d4f0cb4f09d4af7d5888e"   # 分省年度数据根节点

YEARS = "2015YY-2024YY"      # 抓取年份范围
REQUEST_PAUSE = 1.3          # 每次请求后的等待秒数（太快会被限流）
MAX_RETRY = 3

# 要抓的数据集：cid 是通过遍历目录树找到的
DATASETS = {
    "企业信息化及电子商务情况": {
        "cid": "c65e7e59f4434a8cb35fbf9f7c857e60",
        "指标": [
            "电子商务销售额 (亿元)",
            "电子商务采购额 (亿元)",
            "有电子商务交易活动的企业数 (个)",
            "有电子商务交易活动的企业数比重 (%)",
            "每百家企业拥有网站数 (个)",
            "每百人使用计算机数 (台)",
        ],
    },
    "互联网主要指标发展情况": {
        "cid": "53f522fb4b1a40ce90977a0b1cd94da1",
        "指标": [
            "互联网宽带接入用户 (万户)",
            "移动互联网用户 (万户)",
            "移动互联网接入流量 (万GB)",
        ],
    },
}

# 31 个省级行政区（不含港澳台），值为国家统计局使用的 12 位地区代码
PROVINCES = {
    "北京": "110000000000", "天津": "120000000000", "河北": "130000000000",
    "山西": "140000000000", "内蒙古": "150000000000", "辽宁": "210000000000",
    "吉林": "220000000000", "黑龙江": "230000000000", "上海": "310000000000",
    "江苏": "320000000000", "浙江": "330000000000", "安徽": "340000000000",
    "福建": "350000000000", "江西": "360000000000", "山东": "370000000000",
    "河南": "410000000000", "湖北": "420000000000", "湖南": "430000000000",
    "广东": "440000000000", "广西": "450000000000", "海南": "460000000000",
    "重庆": "500000000000", "四川": "510000000000", "贵州": "520000000000",
    "云南": "530000000000", "西藏": "540000000000", "陕西": "610000000000",
    "甘肃": "620000000000", "青海": "630000000000", "宁夏": "640000000000",
    "新疆": "650000000000",
}

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://data.stats.gov.cn/",
        "Content-Type": "application/json",
    }
)


def get_json(path, params=None, max_retry=MAX_RETRY):
    """带重试的 GET。被限流时返回的不是 JSON，所以要单独处理。"""
    for attempt in range(max_retry):
        try:
            r = session.get(f"{BASE}{path}", params=params, timeout=30)
            if r.status_code == 200:
                try:
                    return r.json()
                except json.JSONDecodeError:
                    pass
        except requests.RequestException:
            pass
        time.sleep(REQUEST_PAUSE * (attempt + 1))
    return None


def resolve_indicator_ids(cid, wanted_names):
    """把指标中文名解析成接口需要的 indicatorId。

    为什么不把 ID 写死在代码里？
        因为接口文档明确说明 indicatorId 跨数据集不稳定，
        指标名才是人能看懂、相对稳定的东西。
    """
    j = get_json("/new/queryIndicatorsByCid", {"cid": cid, "dt": "", "name": ""})
    if not j:
        return {}
    data = j.get("data", {})
    lst = data.get("list", []) if isinstance(data, dict) else []

    # 接口返回的名字末尾常带空格，比较前统一去掉
    by_name = {str(it.get("i_showname", "")).strip(): it for it in lst}

    resolved = {}
    for wanted in wanted_names:
        if wanted in by_name:
            resolved[wanted] = by_name[wanted]["_id"]
        else:
            # 退一步：用包含匹配
            for name, it in by_name.items():
                if wanted.split(" (")[0] in name:
                    resolved[wanted] = it["_id"]
                    break
    return resolved


def fetch_province(cid, ind_ids, province_code):
    """取一个省的全部指标数值。"""
    payload = {
        "cid": cid,
        "indicatorIds": list(ind_ids.values()),
        "das": [{"text": "", "value": province_code}],
        "dts": [YEARS],
        "showType": "1",
        "rootId": ROOT_ID,
    }
    for attempt in range(MAX_RETRY):
        try:
            r = session.post(f"{BASE}/stream/esData", json=payload, timeout=45)
            if r.status_code == 200:
                res = r.json()
                if res.get("success"):
                    return res.get("data", []) or []
        except (requests.RequestException, json.JSONDecodeError):
            pass
        time.sleep(REQUEST_PAUSE * (attempt + 1))
    return None


# ===============================================================
# 主流程
# ===============================================================
print("=" * 70)
print("国家统计局分省数据抓取")
print("=" * 70)
print(f"时间范围: {YEARS}")
print(f"省份数量: {len(PROVINCES)}")
print(f"数据集数量: {len(DATASETS)}")
print()

# id -> 指标名 的反查表，用于解析返回值
id_to_name = {}
rows = []
failures = []
metadata = []

for ds_name, cfg in DATASETS.items():
    cid = cfg["cid"]
    print(f"\n--- 数据集：{ds_name} ---")

    resolved = resolve_indicator_ids(cid, cfg["指标"])
    print(f"  解析到 {len(resolved)}/{len(cfg['指标'])} 个指标")
    for wanted in cfg["指标"]:
        mark = "OK " if wanted in resolved else "缺失"
        print(f"    [{mark}] {wanted}")
    if not resolved:
        failures.append(f"{ds_name}: 指标解析失败")
        continue

    for wanted, iid in resolved.items():
        id_to_name[iid] = wanted

    metadata.append({"数据集": ds_name, "cid": cid, "指标": resolved})
    time.sleep(REQUEST_PAUSE)

    ok_prov = 0
    for prov_name, prov_code in PROVINCES.items():
        data = fetch_province(cid, resolved, prov_code)
        if data is None:
            failures.append(f"{ds_name}/{prov_name}: 请求失败")
            print(f"    x {prov_name} 失败")
            time.sleep(REQUEST_PAUSE)
            continue

        count = 0
        for block in data:
            year = str(block.get("code", "")).replace("YY", "")
            for v in block.get("values", []):
                iid = v.get("_id")
                value = str(v.get("value", "")).strip()
                if value == "":
                    continue
                rows.append(
                    {
                        "省份": prov_name,
                        "地区代码": prov_code,
                        "年份": year,
                        "数据集": ds_name,
                        "指标": id_to_name.get(iid, str(v.get("i_showname", "")).strip()),
                        "数值": value,
                        "单位": str(v.get("du_name", "")).strip(),
                    }
                )
                count += 1
        if count:
            ok_prov += 1
        print(f"    ✓ {prov_name:4s} {count:3d} 条")
        time.sleep(REQUEST_PAUSE)

    print(f"  -> {ok_prov}/{len(PROVINCES)} 个省份取到数据")

# ===============================================================
# 写出文件
# ===============================================================
print()
print("=" * 70)
print("写出数据")
print("=" * 70)

csv_path = RAW_DIR / "nbs_digital_economy.csv"
fields = ["省份", "地区代码", "年份", "数据集", "指标", "数值", "单位"]
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"已写出: {csv_path}")
print(f"总记录数: {len(rows)}")

if rows:
    years = sorted({r["年份"] for r in rows})
    provs = sorted({r["省份"] for r in rows})
    inds = sorted({r["指标"] for r in rows})
    print(f"年份范围: {years[0]} - {years[-1]}  ({len(years)} 年)")
    print(f"覆盖省份: {len(provs)} 个")
    print(f"指标数量: {len(inds)} 个")
    for i in inds:
        n = sum(1 for r in rows if r["指标"] == i)
        print(f"    {i:38s} {n:4d} 条")

# 数据说明文件（研究规范：数据来源必须可追溯）
note_path = RAW_DIR / "数据说明.md"
note = f"""# 数据说明

## 来源

- 平台：国家统计局「国家数据」
- 数据集：分省年度数据
- 接口：`{BASE}`
- 抓取脚本：`week2-realdata/fetch_nbs_data.py`
- 抓取时间：{datetime.now():%Y-%m-%d %H:%M:%S}
- 时间范围：{YEARS}

## 检索路径

国家数据 → 分省年度数据 → 运输和邮电 → 各数据集

## 数据集与指标 ID

```json
{json.dumps(metadata, ensure_ascii=False, indent=2)}
```

## 字段说明

| 字段 | 含义 |
|---|---|
| 省份 | 省级行政区简称 |
| 地区代码 | 国家统计局使用的 12 位地区代码 |
| 年份 | 数据所属年份 |
| 数据集 | 该指标所属的数据集名称 |
| 指标 | 指标全名（含单位） |
| 数值 | 指标数值 |
| 单位 | 计量单位 |

## 注意事项

1. 接口对同一指标可能按时间段切成多个数据集（时间分片），
   本脚本只抓取了当前数据集覆盖的年份，早期年份可能缺失。
2. 空值表示该省份该年无数据，脚本已跳过，未做插值。
3. 引用时请以国家统计局官方发布为准。

## 抓取失败记录

{chr(10).join("- " + f for f in failures) if failures else "无"}
"""
note_path.write_text(note, encoding="utf-8")
print(f"已写出: {note_path}")

if failures:
    print()
    print(f"有 {len(failures)} 条失败记录，已写入数据说明文件。")
    for f in failures[:10]:
        print(f"  - {f}")

print()
print("=" * 70)
print("取数完成。下一步运行： python analyze_digital_economy.py")
print("=" * 70)
