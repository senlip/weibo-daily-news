# -*- coding: utf-8 -*-
"""
微博每日新鲜事报告 - 云端轻量版 (GitHub Actions 每日自动运行)
- 直接调用微博官方热搜 API (weibo.com/ajax/side/hotSearch)，无需浏览器、零第三方依赖
- 生成 reports/YYYY-MM-DD.html + .json + index.html (手机入口页)
用法: python weibo_hot_cloud.py
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """当前北京时间（云端 runner 是 UTC，固定 +8）"""
    return datetime.now(BEIJING_TZ)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
API_URL = "https://weibo.com/ajax/side/hotSearch"
TOP_N = 20

# 热搜分类标签(根据标题关键词归类)
CATEGORY_RULES = [
    ("娱乐", ["电影", "剧", "综艺", "音乐", "演唱会", "颁奖", "演员", "导演", "舞台"]),
    ("体育", ["乒乓球", "篮球", "足球", "比赛", "冠军", "NBA", "奥运", "世乒", "WTT", "国足", "夺冠"]),
    ("科技", ["手机", "芯片", "AI", "发布", "科技", "小米", "华为", "苹果", "鸿蒙", "智能"]),
    ("国际", ["叙利亚", "俄罗斯", "美国", "日本", "韩国", "联合国", "总统", "总理", "战争", "中东", "乌克兰"]),
    ("财经", ["股价", "股市", "基金", "公司", "融资", "上市", "经济", "消费", "涨价", "降价"]),
    ("民生", ["暴雨", "天气", "健康", "医院", "交警", "地铁", "高铁", "社保", "养老金", "教育"]),
]

# 微博 flag -> 标签文字
FLAG_LABEL = {1: "热", 2: "沸", 3: "新", 4: "爆"}


def categorize(title: str) -> str:
    for cat, kws in CATEGORY_RULES:
        if any(k in title for k in kws):
            return cat
    return "热点"


def format_heat(num) -> str:
    """把热度数字格式化为 万/亿 显示"""
    try:
        n = float(num)
    except (TypeError, ValueError):
        return str(num) if num else ""
    if n >= 100000000:
        return "%.1f亿" % (n / 100000000)
    if n >= 10000:
        return "%.0f万" % (n / 10000)
    return str(int(n))


def fetch_hot():
    """调用微博热搜 API，返回 (realtime列表, hotgov置顶)"""
    req = urllib.request.Request(API_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data.get("ok"):
        raise RuntimeError("API 返回异常: %s" % str(data)[:200])
    realtime = data.get("data", {}).get("realtime", [])
    hotgov = data.get("data", {}).get("hotgov", {})
    return realtime, hotgov


def build_html(hot_list, pinned, date_str) -> str:
    rows = ""
    for i, h in enumerate(hot_list, 1):
        cat = categorize(h["title"])
        rows += f"""<tr><td>{i}</td><td class="title">{h['title']}</td>
        <td><span class="cat">{cat}</span></td><td class="heat">{h['heat']}</td></tr>"""
    pinned_rows = ""
    for p in pinned:
        pinned_rows += f"<tr><td>{p['title']}</td><td class='heat'>{p['tag']}</td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>微博新鲜事 {date_str}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:"Microsoft YaHei",sans-serif; background:#f5f6f8; color:#333; padding:24px; }}
h1 {{ text-align:center; margin-bottom:6px; color:#161823; }}
.sub {{ text-align:center; color:#888; font-size:13px; margin-bottom:24px; }}
.card {{ background:#fff; border-radius:12px; padding:20px; margin-bottom:16px; box-shadow:0 2px 8px rgba(0,0,0,.05); }}
h2 {{ font-size:17px; margin-bottom:12px; color:#161823; }}
table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
th,td {{ padding:9px 12px; text-align:left; border-bottom:1px solid #eee; }}
th {{ background:#fafafa; font-weight:600; }}
.title {{ font-weight:500; }}
.heat {{ color:#e64340; font-weight:600; }}
.cat {{ background:#f0f5ff; color:#1677ff; font-size:12px; padding:2px 8px; border-radius:8px; }}
.tag-row td {{ background:#fffbe6; }}
.note {{ color:#999; font-size:12px; text-align:center; margin-top:16px; }}
</style></head><body>
<h1>📰 微博新鲜事 · {date_str}</h1>
<p class="sub">数据来源: 微博实时热搜榜 | 抓取时间: {beijing_now().strftime('%Y-%m-%d %H:%M')} (北京时间)</p>
<div class="card"><h2>📌 今日要闻/置顶</h2>
<table><thead><tr><th>内容</th><th>标记</th></tr></thead><tbody>{pinned_rows or '<tr><td colspan=2>无</td></tr>'}</tbody></table></div>
<div class="card"><h2>🔥 热搜 TOP {len(hot_list)}</h2>
<table><thead><tr><th>#</th><th>热搜词</th><th>分类</th><th>热度</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">本报告由云端定时任务自动生成 | 热搜为实时数据,反映抓取时刻状态</p>
</body></html>"""
    return html


def build_index(report_files) -> str:
    """生成手机友好的报告入口页，最新报告置顶"""
    latest_block = ""
    if report_files:
        name, mtime = report_files[0]
        latest_block = (
            '<div class="latest"><span class="tag">最新报告</span>'
            '<a href="{name}.html">📌 {name} 微博热搜</a>'
            '<div class="meta">更新时间 {mtime}</div></div>'
        ).format(name=name, mtime=mtime)
    items = ""
    for name, mtime in report_files[1:]:
        items += (
            '<a class="item" href="{name}.html">'
            '<div><div class="date">{name}</div>'
            '<div class="time">{mtime}</div></div>'
            '<div class="arrow">›</div></a>'
        ).format(name=name, mtime=mtime)
    html = INDEX_TEMPLATE.replace("{latest_block}", latest_block).replace(
        "{list_items}", items or '<div class="empty" style="text-align:center;color:#95a5a6;padding:40px 0;">暂无报告</div>')
    return html


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>微博每日新鲜事</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
       background:#f5f6fa; color:#2d3436; padding-bottom:60px; }
.header { background:linear-gradient(135deg,#ff6b35,#f7b731);
          padding:28px 20px 20px; color:#fff; }
.header h1 { font-size:22px; font-weight:700; }
.header p { font-size:13px; opacity:.9; margin-top:6px; }
.latest { margin:16px; background:#fff; border-radius:14px; padding:16px;
          box-shadow:0 2px 10px rgba(0,0,0,.06); }
.latest .tag { display:inline-block; background:#ff6b35; color:#fff;
               font-size:12px; padding:3px 10px; border-radius:20px; margin-bottom:10px; }
.latest a { display:block; font-size:18px; font-weight:700; color:#2d3436;
            text-decoration:none; }
.latest .meta { font-size:12px; color:#95a5a6; margin-top:8px; }
.section { margin:20px 16px 8px; font-size:14px; color:#7f8c8d; font-weight:600; }
.list { margin:0 16px; }
.item { background:#fff; border-radius:12px; padding:14px 16px; margin-bottom:10px;
        display:flex; justify-content:space-between; align-items:center;
        box-shadow:0 2px 8px rgba(0,0,0,.04); }
.item .date { font-size:16px; font-weight:600; color:#2d3436; }
.item .time { font-size:12px; color:#b2bec3; margin-top:3px; }
.item .arrow { font-size:20px; color:#ff6b35; }
a { text-decoration:none; }
.footer { text-align:center; font-size:12px; color:#b2bec3; margin-top:24px; }
</style>
</head>
<body>
  <div class="header">
    <h1>📰 微博每日新鲜事</h1>
    <p>热搜报告 · 手机随时看</p>
  </div>
  {latest_block}
  <div class="section">全部报告</div>
  <div class="list">
    {list_items}
  </div>
  <div class="footer">每天 08:00 自动更新 · GitHub Pages 托管</div>
</body>
</html>"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    date_str = beijing_now().strftime("%Y-%m-%d")

    realtime, hotgov = fetch_hot()

    ranked = []
    for item in realtime:
        # 过滤广告位
        if item.get("is_ad") or item.get("is_custom"):
            continue
        word = (item.get("word") or "").strip()
        if not word:
            continue
        pos = item.get("realpos") or item.get("rank") or 0
        try:
            pos = int(pos)
        except (TypeError, ValueError):
            pos = 0
        if pos <= 0:
            continue
        ranked.append({
            "rank": pos,
            "title": word,
            "heat": format_heat(item.get("num")),
            "flag": FLAG_LABEL.get(item.get("flag"), ""),
            "note": item.get("note") or "",
        })
    ranked = sorted(ranked, key=lambda x: x["rank"])[:TOP_N]

    pinned = []
    if hotgov:
        pinned.append({
            "title": (hotgov.get("word") or hotgov.get("note") or "").strip(),
            "tag": hotgov.get("icon_desc") or "置顶",
        })

    html = build_html(ranked, pinned, date_str)
    html_path = os.path.join(OUT_DIR, f"{date_str}.html")
    json_path = os.path.join(OUT_DIR, f"{date_str}.json")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "pinned": pinned, "top": ranked},
                  f, ensure_ascii=False, indent=2)

    # 生成/更新手机入口页 index.html
    report_files = []
    for f in sorted(os.listdir(OUT_DIR)):
        if f.endswith(".html") and f != "index.html":
            fp = os.path.join(OUT_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(fp), BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
            report_files.append((f[:-5], mtime))
    report_files.sort(key=lambda x: x[0], reverse=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(report_files))

    print(f"✅ 报告已生成: {html_path} (共{len(ranked)}条热搜)")
    for r in ranked[:10]:
        print(f"  #{r['rank']} {r['title'][:36]} 热度:{r['heat']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 失败: {e}")
        sys.exit(1)
