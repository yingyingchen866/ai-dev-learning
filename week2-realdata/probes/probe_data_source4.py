"""从中国统计年鉴的目录页 left.htm 中提取所有表格链接。

left.htm 是框架的左侧导航，60KB，里面列出了年鉴全部表格。
这里把 <a href="...">表名</a> 全部抓出来，并按关键词筛选。
"""

import re
from pathlib import Path

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BASE = "https://www.stats.gov.cn/sj/ndsj/2024/"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

print("正在下载目录页 left.htm ...")
r = requests.get(BASE + "left.htm", headers={"User-Agent": UA}, timeout=25)
r.encoding = "gb2312"
html = r.text
print(f"状态码 {r.status_code}，长度 {len(html)} 字符")

# 提取所有链接
pattern = re.compile(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
raw = pattern.findall(html)


def clean(s: str) -> str:
    """去掉 HTML 标签和多余空白。"""
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


links = [(href, clean(text)) for href, text in raw]
links = [(h, t) for h, t in links if t]
print(f"共提取到 {len(links)} 个链接\n")

# 保存完整目录，方便以后查
csv_path = OUT / "yearbook_2024_toc.csv"
with open(csv_path, "w", encoding="utf-8-sig") as f:
    f.write("链接,表名\n")
    for h, t in links:
        f.write(f'"{h}","{t}"\n')
print(f"完整目录已保存: {csv_path}\n")

# ---------------------------------------------------------------
# 按数字经济相关关键词筛选
# ---------------------------------------------------------------
KEYWORDS = [
    "信息传输", "软件", "信息技术", "互联网", "电子商务",
    "邮电", "电信", "移动电话", "宽带", "科学技术", "R&D", "研发",
    "数字", "专利", "高技术",
]

print("=" * 70)
print("数字经济相关指标")
print("=" * 70)
hit = 0
for href, text in links:
    for kw in KEYWORDS:
        if kw in text:
            print(f"[{kw}] {text}")
            print(f"        -> {href}")
            hit += 1
            break
print(f"\n命中 {hit} 条")

# ---------------------------------------------------------------
# 顺便看看目录的整体结构（章节名）
# ---------------------------------------------------------------
print()
print("=" * 70)
print("目录中含'章'或纯编号的条目（章节标题）")
print("=" * 70)
for href, text in links:
    if re.match(r"^[一二三四五六七八九十]+[、\s]", text) or "章" in text:
        print(f"  {text}")
