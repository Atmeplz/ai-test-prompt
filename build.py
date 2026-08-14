#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 pages/ 静态站点（与视频模板同风格：瑞士风格 × 蓝图信息密度）。

从 ../prompts/提示词/TC-XX.md 读取完整提示词 → 生成 index.html + tc-XX.html。
提示词有更新时重跑本脚本即可：python build.py
"""

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PROMPTS_DIR = ROOT.parent / "prompts" / "提示词"

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


def esc(s: str) -> str:
    return html.escape(s, quote=False)


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


def index_body() -> str:
    meta = "".join(
        f'<div class="row"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in (
            ("// PROJECT", "AI 能力专项测试"),
            ("// SUITE", "TC-01 ~ TC-08 · 8 CASES"),
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
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>提示词全库 · AI 能力专项测试</title>
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
    <span class="sub rv d1">AI 能力专项测试 · 完整提示词八则</span>
  </div>

  <section class="cards">
{cards}
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

<div class="foot">PROMPT.LIB // 8 CASES · {DATE}</div>

<span class="cross c-tl"></span>
<span class="cross c-br"></span>

</body>
</html>
"""


def main() -> None:
    (ROOT / "index.html").write_text(index_body(), encoding="utf-8")
    for c in CASES:
        (ROOT / f"{c['id'].lower()}.html").write_text(case_body(c), encoding="utf-8")
    print("generated:", [p.name for p in ROOT.glob("*.html")])


if __name__ == "__main__":
    main()
