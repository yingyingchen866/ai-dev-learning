"""测试世界银行开放数据 API 是否可用。

为什么测这个：
  它是一个正规的开放数据接口，不需要绕过任何风控，
  而且数据可以直接用代码取，做到"跑一次脚本就复现全部分析"。
  指标里包含各国互联网普及率、宽带订阅、ICT 出口等数字经济指标。
"""

import requests

print("=" * 66)
print("世界银行开放数据 API 测试")
print("=" * 66)

# 指标：IT.NET.USER.ZS = 使用互联网的人口比例
indicator = "IT.NET.USER.ZS"
url = f"https://api.worldbank.org/v2/country/CHN;USA;IND;BRA;JPN/indicator/{indicator}"

try:
    r = requests.get(
        url,
        params={"format": "json", "per_page": "100", "date": "2010:2023"},
        timeout=30,
    )
    print(f"状态码: {r.status_code}")
    print(f"返回长度: {len(r.content)} 字节")

    if r.status_code == 200:
        data = r.json()
        print(f"返回结构: 列表，含 {len(data)} 部分")
        print(f"元信息: {data[0]}")
        rows = data[1]
        print(f"数据行数: {len(rows)}")
        print()
        print("前 8 条记录:")
        for row in rows[:8]:
            country = row["country"]["value"]
            year = row["date"]
            value = row["value"]
            print(f"  {country:6s} {year}  {value}")
    else:
        print(r.text[:300])
except Exception as exc:
    print(f"失败: {type(exc).__name__}: {exc}")

print()
print("=" * 66)
print("顺便测：有没有分地区的指标（比如按省/州）")
print("=" * 66)
# 世界银行对中国有时提供省级数据，试一下
try:
    r = requests.get(
        "https://api.worldbank.org/v2/country/CHN/indicator/IT.NET.USER.ZS",
        params={"format": "json", "per_page": "5"},
        timeout=30,
    )
    print(f"中国该指标请求状态码: {r.status_code}")
except Exception as exc:
    print(f"失败: {type(exc).__name__}: {exc}")
