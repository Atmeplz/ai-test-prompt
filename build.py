#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 pages/ 静态站点（与视频模板同风格：瑞士风格 × 蓝图信息密度）。

从 ../prompts/提示词/TC-XX.md 读取完整提示词 → 生成 index.html + tc-XX.html；
从 ../评分数据/0X-*.md 读取四张评分榜       → 生成 board-01~04.html。
提示词/评分有更新时重跑本脚本即可：python build.py
"""

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PROMPTS_DIR = ROOT.parent / "prompts" / "提示词"
SCORES_DIR = ROOT.parent / "评分数据"

# —— 用例元数据（与 测试项目.md 保持一致） ——
CASES = [
    dict(
        id="TC-01",
        name="3D 体素中国古典建筑群",
        en="VOXEL CLASSIC ARCHITECTURE",
        dim="空间建模",
        dims="A1 空间想象 · A2 提示词复现 · A3 事实准确 · A4 主次与叙事 · A5 环境与光影 · A6 性能与代码",
        desc="Three.js 生成 Minecraft 风格中式古建群：主殿/配殿/山门/宝塔，中轴对称院落 + 飞檐翘角 + 光影氛围。",
    ),
    dict(
        id="TC-02",
        name="3D 体素自然景观 · 山瀑布穿云",
        en="VOXEL LANDSCAPE · FALL & CLOUD",
        dim="世界理解与知识储备（Addon）",
        dims="B1 地貌常识 · B2 水体物理 · B3 云雾层次 · B4 生态与光环境",
        desc="体素山脉 + 瀑布倾泻 + 穿云遮挡关系，考察模型对自然地貌与水体物理的世界知识。",
    ),
    dict(
        id="TC-03",
        name="前端落地页 · 户外机能风",
        en="LANDING PAGE · OUTDOOR GEAR",
        dim="视觉与交互设计",
        dims="C1 提示词服从 · C2 视觉与交互 · C3 工程完备 · C4 代码质量",
        desc="不给风格约束的商业落地页：由模型自主设计一套自洽、有辨识度的视觉方案。",
    ),
    dict(
        id="TC-04",
        name="童话改编创作 · 小红帽反套路",
        en="FAIRY TALE REWRITE · LITTLE RED RIDING HOOD",
        dim="文本创作",
        dims="D1 提示词服从 · D2 过拟合程度 · D3 故事逻辑性 · D4 文学性",
        desc="以《小红帽》人设为基础创作全新故事：情节必须与原作截然不同，考察过拟合/创意/文本能力（500~2000 字）。",
    ),
    dict(
        id="TC-05",
        name="公文理解提炼",
        en="OFFICIAL DOCUMENT MINING",
        dim="结构化理解",
        dims="E1 议定事项 · E2 关键限定 · E3 格式 · E4 公文表达 · E5 约束遵守",
        desc="从会议纪要中提炼议定事项要点：限 7 条、限 500 字、按时间节点排序、零幻觉。",
    ),
    dict(
        id="TC-06",
        name="论文解读 · 小众论文问答",
        en="PAPER READING · Q&A",
        dim="文本理解与信息提取",
        dims="F1~F3 知识点覆盖 · F4 语风分析",
        desc="阅读随附的小众科学论文（PDF），解答 3 个问题（每答 ≤1000 字）——考察 PDF 解析、要点提取与幻觉抑制。",
    ),
    dict(
        id="TC-07",
        name="库存服务 · 规格陷阱题",
        en="INVENTORY SERVICE · TRAP SPEC",
        dim="后端能力",
        dims="G1 状态码 · G2 无锁原子 · G3 重试一致 · G4 审计脱敏 · G5 幂等 · G6 回滚合并 · G7 自证 + 冲突处理",
        desc="内存版库存服务接入外部合作方：幂等 + 并发 + 回滚 + 自证，标准 vs 实践冲突 + 蜜罐陷阱逐项拦截。",
    ),
    dict(
        id="TC-08",
        name="黑洞模拟 · 广义相对论",
        en="BLACK HOLE · GENERAL RELATIVITY",
        dim="物理知识",
        dims="H1 提示词服从 · H2 物理知识 · H3 科学逻辑 · H4 主观视觉",
        desc="HTML 真实物理黑洞模拟：广义相对论光线追踪 + 物理公式 + OrbitControls，考察物理理解与保真度（不评代码）。",
    ),
]

DATE = "2026-08-13"

# —— 评分榜元数据（编号/巨字/标签由 build.py 定，标题与正文从 评分数据/*.md 解析） ——
BOARD_FILES = ["01-总分榜.md", "02-用例榜.md", "03-单项榜.md", "04-六维数据.md"]
BOARD_EN = {
    "01": ("TOTAL", "SCORE"),
    "02": ("CASE", "RANKING"),
    "03": ("ITEM", "RANKING"),
    "04": ("SIX-DIM", "DATA"),
}
BOARD_TAG = {
    "01": "TOTAL SCORE",
    "02": "PER CASE",
    "03": "PER ITEM",
    "04": "SIX DIMENSIONS",
}
BOARD_DESC = {
    "01": "模型 × 配置合计分排名：百分位 + 百分制 + 逐用例得分，含配置维度对比与迁移期参考排名。",
    "02": "TC-01~08 每用例一张排名表：考察点明细、渠道平均与逐行备注（评分人记录）。",
    "03": "考察点级排行：每个考察点 1st~5th 最高分与百分位（含并列与全量名单）。",
    "04": "六维雷达数据：① 前端开发 ② 后端代码 ③ 逻辑理解 ④ 科学研究 ⑤ 文学创作 ⑥ 审美视觉，区间数据表 + 百分位换算。",
}


def esc(s: str) -> str:
    return html.escape(s, quote=False)


# ---------- 提示词页 ----------

def render_prompt_lines(text: str) -> str:
    """终端窗口内逐行渲染：行号 + md 标题/分隔线高亮（与模板 prompt.html 同规则）。"""
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    for i, l in enumerate(lines):
        cls = "tline"
        if re.match(r"^#{1,6}\s", l):
            cls += " md-h"
        elif re.match(r"^\s*(?:-{3,}|\*{3,})\s*$", l):
            cls += " md-sep"
        out.append(
            f'<div class="{cls}"><span class="ln">{i + 1:03d}</span>'
            f'<span class="tx">{esc(l) or " "}</span></div>'
        )
    return "\n".join(out)


def case_body(c: dict) -> str:
    md = (PROMPTS_DIR / f"{c['id']}.md").read_text(encoding="utf-8")
    n = len(md)
    meta_rows = [
        ("// PROMPT", f"{c['id']} · v1 · FULL TEXT"),
        ("// SOURCE", f"prompts/提示词/{c['id']}.md"),
        ("// CHARS", f"{n} CHARS"),
    ]
    meta = "".join(
        f'<div class="row"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in meta_rows
    )
    nav = "".join(
        f'<a class="n{" on" if x["id"] == c["id"] else ""}" href="{x["id"].lower()}.html">{x["id"][-2:]}</a>'
        for x in CASES
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c['id']} · {esc(c['name'])} — 提示词全库</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="page-detail">

<div class="vlines"><i></i><i></i><i></i><i></i><i></i></div>

<header class="nav">
  <a class="brand" href="index.html">← PROMPT.LIB</a>
  <nav class="tc-nav">{nav}</nav>
</header>

<main class="wrap">
  <div class="meta">
    {meta}
  </div>

  <div class="hero">
    <span class="line rv">{c['id']}<span class="b">.</span></span>
    <span class="sub rv d1">{esc(c['name'])}</span>
    <span class="tag rv d2">{esc(c['dim'])}</span>
  </div>

  <div class="term">
    <div class="term-bar">
      <span>// PROMPT — {c['id']} v1 · {n} CHARS</span>
      <span class="dots">●●●</span>
    </div>
    <div class="term-body">
      {render_prompt_lines(md)}
    </div>
    <div class="term-end">// END OF PROMPT</div>
  </div>

  <div class="dims">
    <span class="k">考察维度</span><span class="v">{esc(c['dims'])}</span>
  </div>
</main>

<div class="band">
  <div class="band-in">
    <span class="band-title">{c['id']} · {esc(c['name'])}</span>
    <span class="band-tag">{esc(c['dim'])}</span>
  </div>
</div>

<div class="foot">PROMPT.FULL // {c['id']}</div>

<span class="cross c-tl"></span>
<span class="cross c-br"></span>

</body>
</html>
"""


# ---------- 评分榜页 ----------

def inline_md(s: str) -> str:
    """行内 md：`code` → **bold** → *em*（先转义再替换，code 优先防误伤）。"""
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def is_table_sep(row: str) -> bool:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def render_table(lines, i):
    """从 lines[i] 起收集连续表格行 → (HTML, 下一行下标)。"""
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(lines[i].strip())
        i += 1

    def cells(r):
        return [c.strip() for c in r.strip().strip("|").split("|")]

    header = cells(rows[0])
    body_start = 2 if len(rows) > 1 and is_table_sep(rows[1]) else 1
    thead = "<tr>" + "".join(f"<th>{inline_md(h)}</th>" for h in header) + "</tr>"
    trs = []
    for r in rows[body_start:]:
        cs = cells(r)
        cls = ' class="tp1"' if cs and cs[0].replace("*", "").strip() == "1" else ""
        trs.append(f"<tr{cls}>" + "".join(f"<td>{inline_md(c)}</td>" for c in cs) + "</tr>")
    return (f'<div class="btable"><table><thead>{thead}</thead><tbody>'
            + "".join(trs) + "</tbody></table></div>"), i


def render_md_body(text: str) -> str:
    """评分榜 md → 站内板式 HTML（h2/h3、引用说明块、表格、列表、段落）。"""
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            block, i = render_table(lines, i)
            out.append(block)
            continue
        if s.startswith(">"):
            block = []
            while i < n and lines[i].startswith(">"):
                block.append(inline_md(lines[i][1:].strip()))
                i += 1
            out.append(f'<div class="note">{"<br>".join(block)}</div>')
            continue
        if s.startswith("### "):
            out.append(f"<h3>{inline_md(s[4:])}</h3>")
            i += 1
            continue
        if s.startswith("## "):
            out.append(f"<h2>{inline_md(s[3:])}</h2>")
            i += 1
            continue
        if s.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(f"<li>{inline_md(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s", s):
            items = []
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                txt = re.sub(r"^\d+\.\s", "", lines[i].strip())
                items.append(f"<li>{inline_md(txt)}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        out.append(f"<p>{inline_md(s)}</p>")
        i += 1
    return "\n".join(out)


def parse_board(fname: str):
    """读取一张榜 md → (编号, 中文标题, 正文 HTML)。"""
    text = (SCORES_DIR / fname).read_text(encoding="utf-8")
    first, rest = text.split("\n", 1)
    m = re.match(r"^#\s*(\d+)\s*—\s*(.+)$", first.strip())
    no = m.group(1) if m else fname[:2]
    title = m.group(2).strip() if m else fname
    return no, title, render_md_body(rest)


def board_stats():
    """从 board-data.json 取模型数/最新评分日期（由 评分数据/build.py 生成）。"""
    try:
        data = json.loads((SCORES_DIR / "out" / "board-data.json").read_text(encoding="utf-8"))
        dates = [r.get("tested") for r in data.get("rows", []) if r.get("tested")]
        return data.get("N_total", "—"), data.get("N_complete", "—"), max(dates) if dates else "—"
    except OSError:
        return "—", "—", "—"


def board_nav(on_no: str) -> str:
    return "".join(
        f'<a class="n{" on" if no == on_no else ""}" href="board-{no}.html">{no} {BOARD_EN[no][0]}</a>'
        for no in BOARD_EN
    )


def board_body(fname: str, stats) -> str:
    no, title, body = parse_board(fname)
    en1, en2 = BOARD_EN[no]
    tag = BOARD_TAG[no]
    n_total, n_complete, latest = stats
    meta = "".join(
        f'<div class="row"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in (
            ("// PROJECT", "AI 能力专项测试"),
            ("// BOARD", f"{no} · {title}"),
            ("// SOURCE", f"评分数据/{fname} ← scores.yaml"),
            ("// DATA", f"{n_total} RUNS · {n_complete} COMPLETE · UPDATED {latest}"),
        )
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{no} · {esc(title)} — 评分榜 · AI 能力专项测试</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="page-board">

<div class="vlines"><i></i><i></i><i></i><i></i><i></i></div>

<header class="nav">
  <a class="brand" href="index.html">← PROMPT.LIB + SCORE.BOARDS</a>
  <nav class="tc-nav">{board_nav(no)}</nav>
</header>

<main class="wrap">
  <div class="meta">
    {meta}
  </div>

  <div class="hero">
    <span class="line rv">{en1}</span>
    <span class="line rv">{en2}<span class="b">.</span></span>
    <span class="sub rv d1">{esc(title)}</span>
    <span class="tag rv d2">{tag}</span>
  </div>

  <div class="board">
{body}
  </div>
</main>

<div class="band">
  <div class="band-in">
    <span class="band-title">{no} · {esc(title)}</span>
    <span class="band-tag">{tag}</span>
  </div>
</div>

<div class="foot">SCORE.BOARD // {no} · {en1} {en2}.</div>

<span class="cross c-tl"></span>
<span class="cross c-br"></span>

</body>
</html>
"""


# ---------- 首页 ----------

def index_body() -> str:
    meta = "".join(
        f'<div class="row"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in (
            ("// PROJECT", "AI 能力专项测试"),
            ("// SUITE", "TC-01 ~ TC-08 · 8 CASES"),
            ("// BOARDS", "4 SCORE BOARDS · 总分 / 用例 / 单项 / 六维"),
            ("// DATE", DATE),
        )
    )
    cards = ""
    for c in CASES:
        cards += f"""
    <a class="card" href="{c['id'].lower()}.html">
      <div class="card-no">{c['id'][-2:]}</div>
      <div class="card-en">{esc(c['en'])}</div>
      <h3>{esc(c['name'])}</h3>
      <p>{esc(c['desc'])}</p>
      <div class="card-foot"><span>{esc(c['dim'])}</span><span class="go">→</span></div>
    </a>"""
    board_cards = ""
    for fname in BOARD_FILES:
        no, title, _ = parse_board(fname)
        en1, en2 = BOARD_EN[no]
        board_cards += f"""
    <a class="card" href="board-{no}.html">
      <div class="card-no">{no}</div>
      <div class="card-en">BOARD · {en1} {en2}.</div>
      <h3>{esc(title)}</h3>
      <p>{esc(BOARD_DESC[no])}</p>
      <div class="card-foot"><span>{BOARD_TAG[no]}</span><span class="go">→</span></div>
    </a>"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>提示词全库 + 评分榜 · AI 能力专项测试</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>

<div class="vlines"><i></i><i></i><i></i><i></i><i></i></div>

<main class="wrap">
  <div class="meta">
    {meta}
  </div>

  <div class="vf"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i><div class="lock">TEST SUITE LOCKED</div></div>

  <div class="hero">
    <span class="line rv">PROMPT</span>
    <span class="line rv">LIBRARY<span class="b">.</span></span>
    <span class="sub rv d1">AI 能力专项测试 · 提示词八则 + 评分四榜</span>
  </div>

  <section class="cards">
{cards}
  </section>

  <section class="sec">
    <div class="sec-title">SCORE BOARDS</div>
    <div class="cards">
{board_cards}
    </div>
  </section>
</main>

<div class="band">
  <div class="band-in">
    <span class="band-title">前端 / 后端 / 自然语言 能力测试</span>
    <div class="cols">
      <div class="col"><span><b>|</b>Frontend scene &amp; UI.</span><span><b>|</b>Backend trap spec.</span></div>
      <div class="col"><span><b>|</b>Natural language mastery.</span><span><b>|</b>World knowledge.</span></div>
      <div class="col"><span><b>|</b>Benchmarking.</span><span><b>|</b>Six-dimension scoring.</span></div>
    </div>
  </div>
</div>

<div class="foot">PROMPT.LIB + SCORE.BOARDS // 8 CASES + 4 BOARDS</div>

<span class="cross c-tl"></span>
<span class="cross c-br"></span>

</body>
</html>
"""


def main() -> None:
    stats = board_stats()
    (ROOT / "index.html").write_text(index_body(), encoding="utf-8")
    for c in CASES:
        (ROOT / f"{c['id'].lower()}.html").write_text(case_body(c), encoding="utf-8")
    for fname in BOARD_FILES:
        no, _, _ = parse_board(fname)
        (ROOT / f"board-{no}.html").write_text(board_body(fname, stats), encoding="utf-8")
    print("generated:", sorted(p.name for p in ROOT.glob("*.html")))


if __name__ == "__main__":
    main()
