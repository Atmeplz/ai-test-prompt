#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成七题四方向制的公开静态站点。

本脚本只读取项目里的评分与提示词事实源，只写入 pages/：
data/site.json、首页、四张榜单页和七张题目页。
"""

import html
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT.parent
BOARD_JSON = PROJECT / "评分数据" / "out" / "board-data.json"
SITE_JSON = ROOT / "data" / "site.json"
PROMPT_ROOT = PROJECT / "prompts" / "提示词"
ASSET_VERSION = "20260830-6"

PROMPT_FILES = {
    "1_novel_creation": PROMPT_ROOT / "1_novel_creation.md",
    "2_article_reading": PROMPT_ROOT / "2_article_reading.md",
    "3_chinese_architecture": PROMPT_ROOT / "3_chinese_architecture.md",
    "4_voxel_mountain": PROMPT_ROOT / "4_voxel_mountain.md",
    "5_frontend_page": PROMPT_ROOT / "5_frontend_page.md",
    "6_backend_mes": PROMPT_ROOT / "6_backend_mes" / "README.md",
    "7_blackhole_sim": PROMPT_ROOT / "7_blackhole_sim.md",
}

BOARD_PAGES = [
    {
        "no": "01",
        "title": "总分榜",
        "en": "FINAL STANDINGS",
        "lede": "四个方向得分直加形成总分，参考 400。所有完整测评按同一套归一口径横向排列。",
    },
    {
        "no": "02",
        "title": "题目榜",
        "en": "TASK RANKINGS",
        "lede": "七个题目分别排名；切换题目可查看归一分、原始分与检查点拆解。",
    },
    {
        "no": "03",
        "title": "检查点榜",
        "en": "CHECKPOINT INDEX",
        "lede": "把总分拆到每个可验证检查点，公开每个检查点的前三档表现。",
    },
    {
        "no": "04",
        "title": "四方向榜",
        "en": "FOUR DIRECTIONS",
        "lede": "文字、前端、后端、知识四个方向独立排名；方向分由成员题按既定权重合成。",
    },
]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def public_case(case: dict) -> dict:
    keys = (
        "total", "raw_total", "k", "rank", "pct", "items", "raw_items",
        "adjust", "raw_adjust", "base", "conflict", "raw_conflict",
    )
    return {key: case[key] for key in keys if key in case}


def build_site_json() -> dict:
    raw = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    latest = max(row["tested"] for row in raw["rows"] if row.get("tested"))
    rows = []

    for row in raw["rows"]:
        public = {
            "board": row["board"],
            "card_label": row.get("card_label", row["model"]),
            "model": row["model"],
            "vendor": row["vendor"],
            "vendor_display": row.get("vendor_display", row["vendor"]),
            "color": row.get("color"),
            "gradient": row.get("gradient"),
            "effort": row.get("effort"),
            "platform": row.get("platform"),
            "source": row.get("source"),
            "tested": row.get("tested"),
            "complete": row["complete"],
            "total": row.get("total"),
            "rank": row.get("rank"),
            "pct": row.get("pct"),
            "pct100": row.get("pct100"),
            "directions": row.get("directions", {}),
            "cases": {key: public_case(value) for key, value in row.get("cases", {}).items()},
        }
        rows.append(public)

    site = {
        "generated_by": "pages/build.py · 七题四方向公开口径",
        "meta": {
            "updated": raw["updated"],
            "latest": latest,
            "N_total": raw["N_total"],
            "N_complete": raw["N_complete"],
            "total_ref": raw["total_ref"],
            "task_count": len(raw["tasks"]),
            "direction_count": len(raw["directions"]),
        },
        "norm": raw["norm"],
        "directions": raw["directions"],
        "tasks": raw["tasks"],
        "vendors": raw["vendors"],
        "cases": raw["cases"],
        "rows": rows,
    }
    SITE_JSON.write_text(
        json.dumps(site, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return site


def head(title: str, description: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#F4F0E6">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="stylesheet" href="assets/style.css?v={ASSET_VERSION}">
</head>"""


def page_grid() -> str:
    return """<div class="blueprint-lines" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
<span class="reg-cross cross-tl" aria-hidden="true"></span>
<span class="reg-cross cross-tr" aria-hidden="true"></span>"""


def topnav(active: str) -> str:
    links = [
        ("index.html", "INDEX", "首页"),
        ("board-01.html", "TOTAL", "总榜"),
        ("board-04.html", "DIRECTIONS", "方向"),
        ("board-02.html", "TASKS", "题目"),
        ("board-03.html", "POINTS", "检查点"),
    ]
    items = []
    for href, en, zh in links:
        current = ' aria-current="page"' if href == active else ""
        items.append(f'<a href="{href}"{current}><span>{en}</span><b>{zh}</b></a>')
    return f"""<header class="site-nav">
  <a class="nav-brand" href="index.html"><i></i><span>AI 能力专项测试<small>CAPABILITY BENCHMARK</small></span></a>
  <nav>{''.join(items)}</nav>
</header>"""


def footer(site: dict) -> str:
    meta = site["meta"]
    return f"""<footer class="site-foot">
  <div><strong>AI TEST REPORT</strong><span>七个题目 · 四个方向 · 一套公开口径</span></div>
  <div class="foot-meta"><span>UPDATED {esc(meta['latest'])}</span><span>{meta['N_complete']} COMPLETE RUNS</span><span>STATIC / PUBLIC</span></div>
</footer>"""


def hero_meta(rows: list[tuple[str, str]]) -> str:
    return '<div class="report-meta reveal">' + "".join(
        f'<div><span>// {esc(key)}</span><b>{esc(value)}</b></div>' for key, value in rows
    ) + "</div>"


def index_body(site: dict) -> str:
    meta = site["meta"]
    task_cards = []
    for key, task in site["tasks"].items():
        no = task["order"]
        weights = " · ".join(
            f"{site['directions'][direction]['en']} {weight * 100:g}%"
            for direction, weight in task["weight"].items()
        )
        task_cards.append(f"""<a class="task-card drop" href="tc-{no:02}.html">
  <div class="task-no">{no:02}</div>
  <div class="task-copy"><span>{esc(task['domain'])}</span><h3>{esc(task['name'])}</h3><p>{esc(task['band'])}</p></div>
  <div class="task-weight">{esc(weights)}<b>↗</b></div>
</a>""")

    return f"""{head('AI 能力专项测试 · 七题四方向公开榜', '七个真实任务、四个能力方向，同一套检查点体系下的 AI 模型横向实测。')}
<body class="home-page">
{page_grid()}
{topnav('index.html')}

<main>
  <section class="home-hero">
    {hero_meta([('REPORT', 'AI CAPABILITY TEST'), ('SUITE', '7 TASKS · 4 DIRECTIONS'), ('EDITION', f"{meta['latest']} / PUBLIC BOARD")])}
    <div class="subject-lock" aria-hidden="true"><i></i><b>SUBJECTS<br>BENCHMARKED</b><i></i></div>
    <h1 class="hero-title reveal delay-1"><span>AI</span><span>能力专项测试</span></h1>
    <div class="hero-band band-in">
      <div><strong>七个题目<span>.</span> 四个方向<span>.</span></strong><p>同一套检查点下的模型横向实测</p></div>
      <a href="board-01.html">查看总榜 <b>→</b></a>
    </div>
    <div class="hero-folio">INDEX.00 // AI TEST REPORT</div>
  </section>

  <section class="report-section board-preview-section">
    <header class="section-head">
      <div><span>// BOARD.01</span><h2>当前总榜</h2></div>
      <p>{meta['N_complete']} 个完整测评<br>参考总分 {meta['total_ref']}</p>
    </header>
    <div id="top-preview" class="top-preview"></div>
    <a class="section-link" href="board-01.html">OPEN FINAL STANDINGS <b>→</b></a>
  </section>

  <section class="report-section direction-preview-section">
    <header class="section-head">
      <div><span>// BOARD.04</span><h2>四个能力方向</h2></div>
      <p>TEXT · FRONTEND<br>BACKEND · KNOWLEDGE</p>
    </header>
    <div id="direction-preview" class="direction-grid"></div>
  </section>

  <section class="report-section" id="tasks">
    <header class="section-head">
      <div><span>// TASK INDEX</span><h2>七个真实任务</h2></div>
      <p>文字、代码、视觉与知识<br>从交付结果反推能力</p>
    </header>
    <div class="task-list">{''.join(task_cards)}</div>
  </section>

  <section class="method-band">
    <div><span>// METHOD</span><strong>每题以全库基准归一，四方向按固定权重合成。</strong></div>
    <p>本站只公开题面、检查点、排名与分数；评分备注与内部裁决记录不公开。</p>
  </section>
</main>

{footer(site)}
<script src="assets/app.js?v={ASSET_VERSION}" defer></script>
</body>
</html>
"""


def render_prompt_lines(text: str) -> str:
    output = []
    for index, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        classes = ["prompt-line"]
        if re.match(r"^#{1,6}\s", line):
            classes.append("prompt-heading")
        elif re.match(r"^\s*(?:-{3,}|\*{3,})\s*$", line):
            classes.append("prompt-rule")
        output.append(
            f'<div class="{" ".join(classes)}"><span>{index:03d}</span><code>{esc(line) or " "}</code></div>'
        )
    return "\n".join(output)


def task_body(key: str, task: dict, site: dict) -> str:
    no = task["order"]
    prompt = PROMPT_FILES[key].read_text(encoding="utf-8")
    tasks = list(site["tasks"].items())
    previous = tasks[(no - 2) % len(tasks)][1]
    following = tasks[no % len(tasks)][1]
    points = "".join(
        f'<li><b>{esc(point["code"])}</b><span>{esc(point["label"])}</span></li>'
        for point in task["points"]
    )
    weights = "".join(
        f'<span>{esc(site["directions"][direction]["en"])} <b>{weight * 100:g}%</b></span>'
        for direction, weight in task["weight"].items()
    )
    work_label = {"live": "实机交付", "excerpt": "文本 / 摘录", "package": "工程包"}.get(task["work"], task["work"])

    return f"""{head(f'{no:02} {task["name"]} · AI 能力专项测试', f'{task["name"]}的公开题面、检查点与成绩排名。')}
<body class="task-page">
{page_grid()}
{topnav('')}

<main>
  <section class="inner-hero task-hero">
    {hero_meta([('TASK', f'{no:02} / 07'), ('DOMAIN', task['domain']), ('PROMPT', task['prompt_ver'].upper())])}
    <div class="inner-kicker">{esc(task['kicker'])}</div>
    <h1 class="inner-title reveal delay-1">{''.join(f'<span>{esc(line)}</span>' for line in task['lines'])}</h1>
    <div class="inner-band band-in"><strong>{esc(task['band'])}</strong><div>{weights}</div></div>
    <div class="inner-folio">TASK.{no:02} // {esc(task['en'])}</div>
  </section>

  <section class="report-section task-brief">
    <header class="section-head">
      <div><span>// BRIEF</span><h2>题目档案</h2></div>
      <p>{esc(task['en'])}<br>{esc(task['domain'])}</p>
    </header>
    <div class="brief-grid">
      <div><span>任务</span><strong>{esc(task['name'])}</strong></div>
      <div><span>交付形态</span><strong>{esc(work_label)}</strong></div>
      <div><span>原始参考分</span><strong>{task['ref']}</strong></div>
      <div><span>检查点</span><strong>{len(task['points'])}</strong></div>
    </div>
    <ol class="checkpoint-list">{points}</ol>
  </section>

  <section class="report-section task-ranking-section">
    <header class="section-head">
      <div><span>// RESULT WINDOW</span><h2>本题排名</h2></div>
      <p>归一分 / 原始分<br>逐检查点拆解</p>
    </header>
    <div class="task-ranking" data-task="{esc(key)}"></div>
  </section>

  <section class="report-section prompt-section">
    <header class="section-head">
      <div><span>// PROMPT SOURCE</span><h2>完整题面</h2></div>
      <p>{len(prompt)} CHARACTERS<br>{len(prompt.splitlines())} LINES</p>
    </header>
    <div class="prompt-window">
      <div class="prompt-bar"><span>PROMPT.{no:02} / {esc(key.upper())}</span><b>PUBLIC SOURCE</b></div>
      <div class="prompt-body">{render_prompt_lines(prompt)}</div>
      <div class="prompt-end">// END OF PROMPT</div>
    </div>
  </section>

  <nav class="task-switch">
    <a href="tc-{previous['order']:02}.html"><span>← PREVIOUS</span><b>{esc(previous['zh'])}</b></a>
    <a href="tc-{following['order']:02}.html"><span>NEXT →</span><b>{esc(following['zh'])}</b></a>
  </nav>
</main>

{footer(site)}
<script src="assets/app.js?v={ASSET_VERSION}" defer></script>
</body>
</html>
"""


def board_body(board: dict, site: dict) -> str:
    meta = site["meta"]
    return f"""{head(f'{board["title"]} · AI 能力专项测试', board['lede'])}
<body class="board-page">
{page_grid()}
{topnav(f'board-{board["no"]}.html')}

<main>
  <section class="inner-hero board-hero">
    {hero_meta([('BOARD', f'{board["no"]} / 04'), ('RUNS', str(meta['N_complete'])), ('UPDATED', meta['latest'])])}
    <div class="inner-kicker">{esc(board['en'])}</div>
    <h1 class="inner-title reveal delay-1"><span>{esc(board['title'])}</span></h1>
    <div class="inner-band band-in"><strong>{esc(board['lede'])}</strong><div><span>PUBLIC</span><span>REF {meta['total_ref']}</span></div></div>
    <div class="inner-folio">BOARD.{board['no']} // {esc(board['en'])}</div>
  </section>

  <section class="report-section board-content-section">
    <div class="board-content" data-site="{board['no']}"></div>
  </section>
</main>

{footer(site)}
<script src="assets/app.js?v={ASSET_VERSION}" defer></script>
</body>
</html>
"""


def archived_page(site: dict) -> str:
    return f"""{head('八题制归档 · AI 能力专项测试', '旧八题制页面已经合并进新的七题四方向体系。')}
<body class="archive-page">
{page_grid()}
{topnav('')}
<main class="archive-note">
  <span>// ARCHIVE.08</span>
  <h1>八题制已归档</h1>
  <p>当前站点已迁移至七题四方向体系。原 TC-08 黑洞模拟现在是第 7 题。</p>
  <a href="tc-07.html">前往黑洞模拟 →</a>
</main>
{footer(site)}
</body>
</html>
"""


def main() -> None:
    site = build_site_json()
    (ROOT / "index.html").write_text(index_body(site), encoding="utf-8")
    for key, task in site["tasks"].items():
        (ROOT / f"tc-{task['order']:02}.html").write_text(task_body(key, task, site), encoding="utf-8")
    (ROOT / "tc-08.html").write_text(archived_page(site), encoding="utf-8")
    for board in BOARD_PAGES:
        (ROOT / f"board-{board['no']}.html").write_text(board_body(board, site), encoding="utf-8")
    print("generated: index + 7 tasks + 4 boards + archive + data/site.json")


if __name__ == "__main__":
    main()
