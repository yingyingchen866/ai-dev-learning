"""数据源备选方案探测。

方案 A：给 easyquery 接口补上完整的浏览器请求头，看能否绕过 WAF 拦截。
方案 B：中国统计年鉴的静态网页表格 —— 用 pandas.read_html 直接读。
"""

import time

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

print("=" * 64)
print("方案 A：easyquery 补全请求头")
print("=" * 64)
session = requests.Session()
session.headers.update(
    {
        "User-Agent": UA,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://data.stats.gov.cn/easyquery.htm?cn=E0103",
        "Connection": "keep-alive",
    }
)
try:
    session.get("https://data.stats.gov.cn/easyquery.htm?cn=E0103", timeout=20)
    r = session.get(
        "https://data.stats.gov.cn/easyquery.htm",
        params={
            "m": "QueryData",
            "dbcode": "fsnd",
            "rowcode": "reg",
            "colcode": "sj",
            "wds": "[]",
            "dfwds": "[]",
            "k1": str(int(time.time() * 1000)),
        },
        timeout=30,
    )
    print(f"状态码: {r.status_code}")
    if r.status_code == 200:
        print("成功！前 300 字符:")
        print(r.text[:300])
    else:
        print("仍被拦截，返回:")
        print(r.text[:200])
except Exception as exc:
    print(f"失败: {type(exc).__name__}: {exc}")

print()
print("=" * 64)
print("方案 B：中国统计年鉴静态网页")
print("=" * 64)

yearbook_urls = [
    "https://www.stats.gov.cn/sj/ndsj/2024/indexch.htm",
    "https://www.stats.gov.cn/sj/ndsj/2023/indexch.htm",
]

for u in yearbook_urls:
    print(f"\n--- {u} ---")
    try:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=25)
        print(f"状态码: {r.status_code}, 长度: {len(r.content)} 字节")
        if r.status_code == 200:
            r.encoding = r.apparent_encoding
            text = r.text
            print("前 200 字符:")
            print(text[:200].replace("\n", " "))

            # 用 pandas 试着把网页里的表格读出来
            import pandas as pd

            try:
                tables = pd.read_html(u)
                print(f"pandas 读到 {len(tables)} 张表")
                for i, t in enumerate(tables[:3]):
                    print(f"  表 {i}: 形状 {t.shape}, 前两行：")
                    print(t.head(2).to_string()[:300])
            except Exception as exc:
                print(f"pandas.read_html 失败: {type(exc).__name__}: {exc}")
        else:
            print("返回内容前 200 字符:")
            print(r.text[:200])
    except Exception as exc:
        print(f"失败: {type(exc).__name__}: {exc}")

print()
print("=" * 64)
