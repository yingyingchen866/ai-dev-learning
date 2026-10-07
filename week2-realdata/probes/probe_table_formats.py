"""测试年鉴表格有没有可机读的版本（htm / xls / xlsx），而不只是 jpg。

16-40 是"分地区企业信息化及电子商务情况"，正是我们要的分省数字经济数据。
"""

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BASE = "https://www.stats.gov.cn/sj/ndsj/2024/"

# 表 16-40 和 16-37 的各种可能格式
candidates = []
for tid in ["C16-40", "C16-37", "C16-38", "C01-01"]:
    for ext in ["htm", "html", "xls", "xlsx", "jpg"]:
        candidates.append(f"html/{tid}.{ext}")

print("=" * 70)
print("年鉴表格格式探测")
print("=" * 70)

results = {}
for path in candidates:
    url = BASE + path
    try:
        r = requests.head(url, headers={"User-Agent": UA}, timeout=15, allow_redirects=True)
        code = r.status_code
        size = r.headers.get("Content-Length", "?")
        ctype = r.headers.get("Content-Type", "?")
    except Exception:
        # 有些服务器不支持 HEAD，退回 GET
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20, stream=True)
            code = r.status_code
            size = r.headers.get("Content-Length", "?")
            ctype = r.headers.get("Content-Type", "?")
            r.close()
        except Exception as exc:
            code, size, ctype = f"ERR {type(exc).__name__}", "-", "-"
    results[path] = (code, size, ctype)
    flag = "可用" if code == 200 else "  "
    print(f"[{flag}] {path:20s} {code}  {str(size):>10s} 字节  {ctype}")

print()
print("=" * 70)
print("结论")
print("=" * 70)
ok = {k: v for k, v in results.items() if v[0] == 200}
if ok:
    for k in ok:
        print(f"  存在: {k}")
else:
    print("  没有任何 htm/xls 版本，说明该年鉴在线版只有图片。")

print()
print("=" * 70)
print("附带测试：国家数据网站页面能否打开（决定能否手动下载）")
print("=" * 70)
for u in [
    "https://data.stats.gov.cn/easyquery.htm?cn=E0103",
    "https://data.stats.gov.cn/easyquery.htm?cn=C01",
]:
    try:
        r = requests.get(u, headers={"User-Agent": UA}, timeout=20)
        print(f"{u}\n   状态码 {r.status_code}, 长度 {len(r.content)} 字节")
    except Exception as exc:
        print(f"{u}\n   失败 {type(exc).__name__}: {exc}")
