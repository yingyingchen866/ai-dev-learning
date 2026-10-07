"""把 left.htm 原样存到本地，方便直接检查它的真实结构。"""

from pathlib import Path

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BASE = "https://www.stats.gov.cn/sj/ndsj/2024/"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

r = requests.get(BASE + "left.htm", headers={"User-Agent": UA}, timeout=25)
r.encoding = "gb2312"

raw_path = OUT / "left_raw.htm"
raw_path.write_text(r.text, encoding="utf-8")
print(f"已保存: {raw_path}  ({len(r.text)} 字符)")

# 统计各种可能的链接写法，看看到底是哪种
import re

checks = {
    'href="..." (双引号)': r'href="([^"]+)"',
    "href='...' (单引号)": r"href='([^']+)'",
    "HREF=... 无引号": r"HREF=([^\s>]+)",
    "<a 标签总数": r"<a[\s>]",
    "<A 标签总数": r"<A[\s>]",
    "onclick": r"onclick=",
    "window.open": r"window\.open",
    "C01 之类编号": r"C\d{2}",
}
print()
for label, pat in checks.items():
    m = re.findall(pat, r.text, re.I)
    print(f"{label:24s} 命中 {len(m)} 次")
    if m and len(m) <= 5:
        for x in m[:5]:
            print(f"      示例: {x[:80]}")

# 直接看前 60 行里含 href / a 标签的部分
print()
print("=" * 70)
print("原始内容片段（含 href 或 <a 的行）")
print("=" * 70)
lines = r.text.splitlines()
shown = 0
for i, line in enumerate(lines):
    if ("href" in line.lower() or "<a " in line.lower()) and shown < 25:
        print(f"{i:5d}| {line.strip()[:150]}")
        shown += 1
