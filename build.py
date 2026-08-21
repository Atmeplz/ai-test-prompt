#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pages/build.py — 站点生成器（v3 · 清透玻璃拟态 + 数据驱动）

一条命令完成全部更新（评分榜更新同样走这里）：

    python build.py

流程：
  1) 若 ../评分数据/scores.yaml 有改动（或 out/board-data.json 缺失），
     自动先跑 ../评分数据/build.py 重算榜单与数据；
  2) 从 board-data.json 派生 **公开版** data/site.json
     （评分备注 / 金句 / 画像 / 判例等内部审计内容不进站点，只留在 ../评分数据/*.md）；
  3) 渲染 index.html + tc-01~08.html + board-01~04.html 外壳
     （榜单正文由 assets/app.js 在浏览器端读 data/site.json 渲染）。

提示词更新：编辑 ../prompts/提示词/TC-XX.md 后同样重跑本脚本。
"""

import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROMPTS_DIR = ROOT.parent / "prompts" / "提示词"
SCORES_DIR = ROOT.parent / "评分数据"
BOARD_JSON = SCORES_DIR / "out" / "board-data.json"
SITE_JSON = ROOT / "data" / "site.json"

# —— 用例元数据（与 测试项目.md 保持一致） ——
CASES = [
    dict(id="TC-01", name="3D 体素中国古典建筑群", en="VOXEL CLASSIC ARCHITECTURE", dim="空间建模",
         dims="A1 空间想象 · A2 提示词复现 · A3 事实准确 · A4 主次与叙事 · A5 环境与光影 · A6 性能与代码",
         desc="Three.js 生成 Minecraft 风格中式古建群：主殿/配殿/山门/宝塔，中轴对称院落 + 飞檐翘角 + 光影氛围。"),
    dict(id="TC-02", name="3D 体素自然景观 · 山瀑布穿云", en="VOXEL LANDSCAPE · FALL & CLOUD", dim="世界理解与知识储备（Addon）",
         dims="B1 地貌常识 · B2 水体物理 · B3 云雾层次 · B4 生态与光环境",
         desc="体素山脉 + 瀑布倾泻 + 穿云遮挡关系，考察模型对自然地貌与水体物理的世界知识。"),
    dict(id="TC-03", name="前端落地页 · 户外机能风", en="LANDING PAGE · OUTDOOR GEAR", dim="视觉与交互设计",
         dims="C1 提示词服从 · C2 视觉与交互 · C3 工程完备 · C4 代码质量",
         desc="不给风格约束的商业落地页：由模型自主设计一套自洽、有辨识度的视觉方案。"),
    dict(id="TC-04", name="童话改编创作 · 小红帽反套路", en="FAIRY TALE REWRITE · LITTLE RED RIDING HOOD", dim="文本创作",
         dims="D1 提示词服从 · D2 过拟合程度 · D3 故事逻辑性 · D4 文学性",
         desc="以《小红帽》人设为基础创作全新故事：情节必须与原作截然不同，考察过拟合/创意/文本能力（500~2000 字）。"),
    dict(id="TC-05", name="公文理解提炼", en="OFFICIAL DOCUMENT MINING", dim="结构化理解",
         dims="E1 议定事项 · E2 关键限定 · E3 格式 · E4 公文表达 · E5 约束遵守",
         desc="从会议纪要中提炼议定事项要点：限 7 条、限 500 字、按时间节点排序、零幻觉。"),
    dict(id="TC-06", name="论文解读 · 小众论文问答", en="PAPER READING · Q&A", dim="文本理解与信息提取",
         dims="F1~F3 知识点覆盖 · F4 语风分析",
         desc="阅读随附的小众科学论文（PDF），解答 3 个问题（每答 ≤1000 字）——考察 PDF 解析、要点提取与幻觉抑制。"),
    dict(id="TC-07", name="库存服务 · 规格陷阱题", en="INVENTORY SERVICE · TRAP SPEC", dim="后端能力",
         dims="G1 状态码 · G2 无锁原子 · G3 重试一致 · G4 审计脱敏 · G5 幂等 · G6 回滚合并 · G7 自证 + 冲突处理",
         desc="内存版库存服务接入外部合作方：幂等 + 并发 + 回滚 + 自证，标准 vs 实践冲突 + 蜜罐陷阱逐项拦截。"),
    dict(id="TC-08", name="黑洞模拟 · 广义相对论", en="BLACK HOLE · GENERAL RELATIVITY", dim="物理知识",
         dims="H1 提示词服从 · H2 物理知识 · H3 科学逻辑 · H4 主观视觉",
         desc="HTML 真实物理黑洞模拟：广义相对论光线追踪 + 物理公式 + OrbitControls，考察物理理解与保真度（不评代码）。"),
]

BOARDS = [
    dict(no="01", title="总分榜", en="TOTAL SCORE",
         lede="八个用例全部测完的 run 按合计分排名。百分位 = 该行得分 ÷ 榜首得分（榜首恒 100%）；百分制 = 得分 ÷ 384.6。点开任意一行可看 8 个用例的逐项得分。"),
    dict(no="02", title="用例榜", en="PER CASE",
         lede="TC-01 ~ TC-08 每个用例一张排名表：总分、百分位与各考察点得分。切换上方标签查看不同用例。"),
    dict(no="03", title="单项榜", en="PER ITEM",
         lede="考察点级前三甲（含并列）。完整逐行记录与评分备注留存在内部评分档案，不在此公开。"),
    dict(no="04", title="六维能力", en="SIX DIMENSIONS",
         lede="六维能力雷达：前端开发 / 后端代码 / 逻辑理解 / 科学研究 / 文学创作 / 审美视觉。默认排名换算百分位口径（该维第一名恒 100%），可切换 10 分制原始值，支持双模型叠加对比。"),
]


def esc(s: str) -> str:
    return html.escape(s, quote=False)


# ---------- 数据链 ----------

def ensure_scores_fresh() -> None:
    """scores.yaml 比 board-data.json 新（或 json 缺失）时，自动重跑评分数据 build。"""
    yaml_path = SCORES_DIR / "scores.yaml"
    stale = (not BOARD_JSON.exists()) or yaml_path.stat().st_mtime > BOARD_JSON.stat().st_mtime
    if stale:
        print("→ scores.yaml 有更新，先重跑 评分数据/build.py …")
        subprocess.run([sys.executable, str(SCORES_DIR / "build.py")], cwd=str(SCORES_DIR), check=True)


def build_site_json() -> dict:
    """board-data.json → 公开版 site.json（剥离 profile / video / run_note / jinju / note 等内部字段）。"""
    raw = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    rows = []
    latest = ""
    for r in raw["rows"]:
        entry = {
            "board": r["board"], "model": r["model"], "vendor": r["vendor"],
            "effort": r.get("effort"), "platform": r.get("platform"),
            "tested": r.get("tested"), "complete": r["complete"],
        }
        if r.get("tested"):
            latest = max(latest, r["tested"])
        if r["complete"]:
            entry.update(total=r["total"], rank=r["rank"], pct=r["pct"], pct100=r["pct100"],
                         radar=r.get("radar"), radar_mean=r.get("radar_mean"))
        cases = {}
        for tc, c in r.get("cases", {}).items():
            cc = {"total": c["total"], "rank": c["rank"], "pct": c["pct"], "items": c.get("items", {})}
            for k in ("raw", "base", "conflict", "x1", "adjust"):
                if k in c:
                    cc[k] = c[k]
            cases[tc] = cc
        entry["cases"] = cases
        rows.append(entry)
    site = {
        "generated_by": "pages/build.py — 公开口径（内部备注/金句/判例不上站）",
        "meta": {"updated": raw["updated"], "latest": latest or raw["updated"],
                 "N_total": raw["N_total"], "N_complete": raw["N_complete"],
                 "total_max": raw["total_max"]},
        "vendors": raw["vendors"],
        "cases": raw["cases"],
        "radar_dims": raw["radar_dims"],
        "rows": rows,
    }
    SITE_JSON.parent.mkdir(exist_ok=True)
    SITE_JSON.write_text(json.dumps(site, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return site


# ---------- 通用模板 ----------

def head(title: str, desc: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%235b8cff'/%3E%3Cstop offset='1' stop-color='%232fd4b6'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='32' height='32' rx='9' fill='url(%23g)'/%3E%3Crect x='9' y='9' width='14' height='14' rx='4' fill='white'/%3E%3C/svg%3E">
<link rel="stylesheet" href="assets/style.css">
</head>"""


def bg_layers() -> str:
    return '<div class="aurora"><i></i><i></i><i></i><i></i></div>\n<div class="gridlines"></div>'


def topnav(active: str) -> str:
    links = [("index.html", "首页"), ("board-01.html", "总分榜"), ("board-02.html", "用例榜"),
             ("board-03.html", "单项榜"), ("board-04.html", "六维")]
    parts = []
    for h, t in links:
        cls = ' class="on"' if h == active else ""
        parts.append(f'<a href="{h}"{cls}>{t}</a>')
    nav = "".join(parts)
    return f"""<header class="topnav">
  <a class="brand" href="index.html"><span class="logo"></span><span class="bt">AI 能力专项测试</span></a>
  <nav>{nav}</nav>
</header>"""


def footer(site: dict) -> str:
    return f"""<footer class="foot"><div class="wrap">
  <span class="fm">PROMPT.LIB × SCORE.BOARDS — 8 CASES / 4 BOARDS</span>
  <span class="fn">数据更新 <b>{esc(site['meta']['latest'])}</b> · {site['meta']['N_total']} runs · {site['meta']['N_complete']} 完整测评 · 由 scores.yaml 自动生成</span>
</div></footer>"""


# ---------- 首页 ----------

def index_body(site: dict) -> str:
    m = site["meta"]
    case_cards = "".join(f"""
      <a class="card" href="{c['id'].lower()}.html">
        <div class="no">{c['id'][-2:]}</div>
        <div class="en">{esc(c['en'])}</div>
        <h3>{esc(c['name'])}</h3>
        <p>{esc(c['desc'])}</p>
        <div class="foot"><span>{esc(c['dim'])}</span><span class="go">→</span></div>
      </a>""" for c in CASES)
    board_cards = "".join(f"""
      <a class="card" href="board-{b['no']}.html">
        <div class="no">{b['no']}</div>
        <div class="en">BOARD · {b['en']}</div>
        <h3>{b['title']}</h3>
        <p>{esc(b['lede'].split("。")[0])}。</p>
        <div class="foot"><span>{b['en']}</span><span class="go">→</span></div>
      </a>""" for b in BOARDS)

    return f"""{head("提示词全库 × 评分榜 · AI 能力专项测试", "8 道全栈用例 × 4 张评分榜：同一套检查点体系下的 AI 模型横向实测。")}
<body class="page-home">
{bg_layers()}
{topnav("index.html")}

<section class="hero">
  <canvas id="hero3d" aria-hidden="true"></canvas>
  <div class="hero-inner">
    <div class="chip rv"><span class="dot"></span>AI 能力专项测试 · CHECKPOINT SUITE 2026</div>
    <h1 class="rv d1">
      <span class="en">PROMPT LIBRARY × SCORE BOARDS</span>
      <span class="gt">提示词全库</span><br>× 评分榜
    </h1>
    <p class="lede rv d2">8 道全栈用例 × 4 张评分榜——3D 体素古建、山水瀑布、前端落地页、童话改编、公文提炼、论文问答、后端陷阱规格、黑洞模拟，同一套检查点体系下的横向实测。</p>
    <div class="cta rv d3">
      <a class="btn btn-p" href="board-01.html">直达总分榜 <span class="ar">→</span></a>
      <a class="btn btn-g" href="#cases">浏览八个用例</a>
    </div>
    <div class="stats rv d4">
      <div class="stat"><b data-stat="runs">{m['N_total']}</b><span>RUNS 评测次数</span></div>
      <div class="stat"><b data-stat="complete">{m['N_complete']}</b><span>完整八用例</span></div>
      <div class="stat"><b data-stat="cases">8</b><span>测试用例</span></div>
      <div class="stat"><b data-stat="updated" style="font-size:15px;line-height:31px">{esc(m['latest'])}</b><span>最近更新</span></div>
    </div>
  </div>
  <div class="scroll-hint">SCROLL</div>
</section>

<main class="wrap">
  <section class="sec">
    <div class="sec-head">
      <h2><span class="en">LEADERBOARD PREVIEW</span>总榜速览 · TOP 5</h2>
      <a class="more" href="board-01.html">完整总分榜 →</a>
    </div>
    <div id="top-preview"></div>
  </section>

  <section class="sec" id="cases">
    <div class="sec-head">
      <h2><span class="en">TEST CASES · TC-01~08</span>八个测试用例</h2>
    </div>
    <div class="cards">{case_cards}
    </div>
  </section>

  <section class="sec">
    <div class="sec-head">
      <h2><span class="en">SCORE BOARDS</span>四张评分榜</h2>
    </div>
    <div class="cards">{board_cards}
    </div>
  </section>

  <section class="sec">
    <div class="notebox">
      <b>口径说明</b>：总分榜/用例榜百分位 = 得分 ÷ 该榜榜首得分（榜首恒 100%）；六维雷达默认排名换算百分位（该维第一名恒 100%）。TC-07 总分允许超过 100（基础 100 + 冲突处理 ±15）。
      本站只公开排名与分数；逐题评分备注、扣分判例与评语录留存在内部评分档案。
    </div>
  </section>
</main>

{footer(site)}
<script src="assets/app.js" defer></script>
<script type="module" src="assets/hero.js"></script>
</body>
</html>
"""


# ---------- 提示词页 ----------

def render_prompt_lines(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    for i, l in enumerate(lines):
        cls = "tline"
        if re.match(r"^#{1,6}\s", l):
            cls += " md-h"
        elif re.match(r"^\s*(?:-{3,}|\*{3,})\s*$", l):
            cls += " md-sep"
        out.append(f'<div class="{cls}"><span class="ln">{i + 1:03d}</span><span class="tx">{esc(l) or " "}</span></div>')
    return "\n".join(out)


def case_body(c: dict, site: dict) -> str:
    md = (PROMPTS_DIR / f"{c['id']}.md").read_text(encoding="utf-8")
    n = len(md)
    idx = next(i for i, x in enumerate(CASES) if x["id"] == c["id"])
    prev_c, next_c = CASES[idx - 1], CASES[(idx + 1) % len(CASES)]
    dim_chips = "".join(f'<span class="dk">{esc(x.strip())}</span>' for x in c["dims"].split("·"))
    return f"""{head(f"{c['id']} · {c['name']} — 提示词全库", f"{c['id']} {c['name']} 完整提示词 · AI 能力专项测试")}
<body class="page-case">
{bg_layers()}
{topnav("")}

<main class="wrap">
  <div class="pagehead">
    <div class="crumb">PROMPT LIBRARY / {c['id']} · FULL TEXT · {n} CHARS</div>
    <h1>{esc(c['name'])}<span class="en">{esc(c['en'])}</span></h1>
    <p class="lede">{esc(c['desc'])}</p>
    <div class="meta-chips">
      <span class="mc">{c['id']}</span>
      <span class="mc">考察维度 · <b>{esc(c['dim'])}</b></span>
      <span class="mc">来源 · prompts/提示词/{c['id']}.md</span>
    </div>
  </div>

  <div class="term">
    <div class="term-bar"><span>// PROMPT — {c['id']} · {n} CHARS</span><span class="dots">●●●</span></div>
    <div class="term-body">
{render_prompt_lines(md)}
    </div>
    <div class="term-end">// END OF PROMPT</div>
  </div>

  <div class="dims">{dim_chips}</div>

  <div class="caseswitch">
    <a class="btn btn-g" href="{prev_c['id'].lower()}.html">← {prev_c['id']} {esc(prev_c['name'])}</a>
    <a class="btn btn-g" href="{next_c['id'].lower()}.html">{next_c['id']} {esc(next_c['name'])} →</a>
  </div>
</main>

{footer(site)}
</body>
</html>
"""


# ---------- 评分榜页 ----------

def board_body(b: dict, site: dict) -> str:
    m = site["meta"]
    return f"""{head(f"{b['no']} {b['title']} — 评分榜 · AI 能力专项测试", b['lede'])}
<body class="page-board">
{bg_layers()}
{topnav(f"board-{b['no']}.html")}

<main class="wrap">
  <div class="pagehead">
    <div class="crumb">SCORE BOARDS / {b['no']} · {b['en']}</div>
    <h1>{b['title']}<span class="en">{b['en']}</span></h1>
    <p class="lede">{esc(b['lede'])}</p>
    <div class="meta-chips">
      <span class="mc"><b data-stat="runs">{m['N_total']}</b> runs</span>
      <span class="mc"><b data-stat="complete">{m['N_complete']}</b> 完整八用例</span>
      <span class="mc">更新 <b data-stat="updated">{esc(m['latest'])}</b></span>
      <span class="mc">数据源 · scores.yaml</span>
    </div>
  </div>

  <div data-site="{b['no']}"></div>
</main>

{footer(site)}
<script src="assets/app.js" defer></script>
</body>
</html>
"""


# ---------- main ----------

def main() -> None:
    ensure_scores_fresh()
    site = build_site_json()
    (ROOT / "index.html").write_text(index_body(site), encoding="utf-8")
    for c in CASES:
        (ROOT / f"{c['id'].lower()}.html").write_text(case_body(c, site), encoding="utf-8")
    for b in BOARDS:
        (ROOT / f"board-{b['no']}.html").write_text(board_body(b, site), encoding="utf-8")
    print("generated: index.html, tc-01~08.html, board-01~04.html, data/site.json")


if __name__ == "__main__":
    main()
