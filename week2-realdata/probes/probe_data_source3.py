"""挖出中国统计年鉴的真实表格页面地址。

indexch.htm 只有 887 字节，说明它是框架页（frameset），
真正的目录和表格在它引用的子页面里。这里把结构打印出来。
"""

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BASE = "https://www.stats.gov.cn/sj/ndsj/2024/"


def show(label, url, limit=1500):
    print(f"\n{'=' * 64}")
    print(f"{label}")
    print(url)
    print("=" * 64)
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        r.encoding = "gb2312" if "charset=gb2312" in r.text.lower()[:500] else r.apparent_encoding
        print(f"状态码: {r.status_code}  长度: {len(r.content)} 字节  最终URL: {r.url}")
        if r.status_code == 200:
            print("-" * 64)
            print(r.text[:limit])
            print("-" * 64)
            return r.text
    except Exception as exc:
        print(f"失败: {type(exc).__name__}: {exc}")
    return None


# 1. 框架页全文（很短，全打印）
show("1. 年鉴首页（框架页全文）", BASE + "indexch.htm", limit=2000)

# 2. 框架页通常会引用几个子页面，逐个试
for name in ["left.htm", "right.htm", "main.htm", "directory.htm", "index.htm"]:
    show(f"2. 子页面 {name}", BASE + name, limit=800)

# 3. 猜测的表格页面路径
for name in ["html/C0101.htm", "html/C0101c.htm", "html/C01-01.htm"]:
    show(f"3. 表格页面 {name}", BASE + name, limit=600)
