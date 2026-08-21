/* 站点数据渲染层 —— 读取 data/site.json（由 build.py 从 scores.yaml 派生，禁止手改）
   公开口径：只渲染排名 / 分数 / 百分位 / 六维；评分备注、金句、判例等审计内容不上站。 */
(function () {
  "use strict";

  const esc = (s) =>
    String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmt = (x) => {
    if (x === null || x === undefined || Number.isNaN(x)) return "—";
    const r = Math.round(x * 100 + 1e-9) / 100;
    return Math.abs(r - Math.round(r)) < 1e-9 ? String(Math.round(r)) : String(r).replace(/0+$/, "").replace(/\.$/, "");
  };
  const pct = (x) => (x === null || x === undefined ? "—" : x.toFixed(1) + "%");

  const TCS = ["tc-01", "tc-02", "tc-03", "tc-04", "tc-05", "tc-06", "tc-07", "tc-08"];
  const TC_SHORT = TCS.map((t) => t.toUpperCase());

  /* 当前页导航高亮 */
  const file = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".topnav nav a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === file) a.classList.add("on");
  });

  const needData = document.querySelector("[data-site]") || document.getElementById("top-preview");
  if (!needData) return;

  fetch("data/site.json")
    .then((r) => { if (!r.ok) throw new Error("site.json " + r.status); return r.json(); })
    .then((data) => {
      fillStats(data);
      const el = document.querySelector("[data-site]");
      if (document.getElementById("top-preview")) renderTopPreview(data);
      if (!el) return;
      const board = el.getAttribute("data-site");
      if (board === "01") renderBoard01(el, data);
      if (board === "02") renderBoard02(el, data);
      if (board === "03") renderBoard03(el, data);
      if (board === "04") renderBoard04(el, data);
    })
    .catch((e) => {
      const el = document.querySelector("[data-site]");
      if (el) el.innerHTML = `<div class="notebox">数据加载失败：${esc(e.message)}。请先运行 <b>python build.py</b> 生成 data/site.json。</div>`;
    });

  /* ---------- 通用 ---------- */
  function vendorDot(data, key) {
    const v = data.vendors[key];
    const bg = v && v.gradient
      ? `background:linear-gradient(135deg,${v.gradient.join(",")})`
      : `background:${(v && v.color) || "#94a3b8"}`;
    return `<i class="vd" style="${bg}" title="${esc((v && v.display) || key)}"></i>`;
  }

  function fillStats(data) {
    document.querySelectorAll("[data-stat]").forEach((n) => {
      const k = n.getAttribute("data-stat");
      const v =
        k === "runs" ? data.meta.N_total :
        k === "complete" ? data.meta.N_complete :
        k === "updated" ? data.meta.latest :
        k === "cases" ? "8" : "";
      if (v !== "") n.textContent = v;
    });
  }

  function medal(rk) { return rk === 1 ? "🥇" : rk === 2 ? "🥈" : rk === 3 ? "🥉" : ""; }

  /* ---------- 首页 Top5 速览 ---------- */
  function renderTopPreview(data) {
    const box = document.getElementById("top-preview");
    const full = data.rows.filter((r) => r.complete).sort((a, b) => a.rank - b.rank).slice(0, 5);
    box.innerHTML = `<div class="topbar-card">` + full.map((r) => `
      <a class="toprow" href="board-01.html">
        <span class="rk">${r.rank}</span>
        <span class="nm">${vendorDot(data, r.vendor)}<span class="t">${esc(r.board)}</span></span>
        <span class="bar"><i data-w="${r.pct}"></i></span>
        <span class="sc">${fmt(r.total)}</span>
      </a>`).join("") + `</div>`;
    requestAnimationFrame(() =>
      box.querySelectorAll(".bar i").forEach((i) => (i.style.width = i.getAttribute("data-w") + "%")));
  }

  /* ---------- 01 总分榜 ---------- */
  function renderBoard01(el, data) {
    const full = data.rows.filter((r) => r.complete).sort((a, b) => a.rank - b.rank);
    const caseSum = (r) => TCS.reduce((s, tc) => s + (r.cases[tc] ? r.cases[tc].total : 0), 0);
    const pend = data.rows.filter((r) => !r.complete)
      .sort((a, b) => caseSum(b) - caseSum(a) || a.board.localeCompare(b.board));

    const top3 = [full[1], full[0], full[2]].filter(Boolean);
    const podium = `<div class="podium">` + top3.map((r) => `
      <div class="pod ${r.rank === 1 ? "p1" : ""}">
        <div class="halo"></div>
        <div class="medal">${medal(r.rank)}</div>
        <div class="nm">${vendorDot(data, r.vendor)}${esc(r.board)}</div>
        <div class="sc">${fmt(r.total)}</div>
        <div class="pc">百分位 ${pct(r.pct)} · 百分制 ${pct(r.pct100)}</div>
      </div>`).join("") + `</div>`;

    const rows = full.map((r) => {
      const chips = TCS.map((tc, i) => {
        const c = r.cases[tc];
        return c ? `<span class="casechip">${TC_SHORT[i]} <b>${fmt(c.total)}</b> · ${pct(c.pct)}</span>` : "";
      }).join("");
      return `
      <tr class="tp${r.rank <= 3 ? r.rank : ""}">
        <td><span class="rk">${r.rank}</span></td>
        <td><span class="nm">${vendorDot(data, r.vendor)}${esc(r.board)}</span></td>
        <td class="num strong">${fmt(r.total)} <span style="color:var(--ink-3);font-weight:400">/ ${data.meta.total_max}</span></td>
        <td><span class="mini-bar"><i style="width:${r.pct}%"></i></span><span class="pct">${pct(r.pct)}</span></td>
        <td class="num">${pct(r.pct100)}</td>
        <td class="pct">${esc(r.tested || "—")}</td>
        <td><button class="rowbtn" data-x>＋</button></td>
      </tr>
      <tr class="detail"><td colspan="7"><div class="casechips">${chips}</div></td></tr>`;
    }).join("");

    /* 配置维度对比（同模型多配置） */
    const byModel = {};
    full.forEach((r) => (byModel[r.model] = byModel[r.model] || []).push(r));
    const multi = Object.entries(byModel).filter(([, rs]) => rs.length > 1);
    let cmp = "";
    if (multi.length) {
      cmp = `<div class="sec-sub">CONFIG COMPARE · 配置维度对比</div>` + multi.map(([m, rs]) => {
        rs = rs.slice().sort((a, b) => b.total - a.total);
        const head = `<tr><th>配置</th>${TCS.map((t) => `<th>${t.toUpperCase()}</th>`).join("")}<th>合计</th></tr>`;
        const body = rs.map((r) => `<tr>
          <td class="nm">${vendorDot(data, r.vendor)}${esc(r.effort || r.platform || "?")}</td>
          ${TCS.map((tc) => `<td class="num">${fmt(r.cases[tc] && r.cases[tc].total)}</td>`).join("")}
          <td class="num strong">${fmt(r.total)}</td></tr>`).join("");
        const win = `<tr><td style="color:var(--ink-3);font-weight:700">胜方</td>
          ${TCS.map((tc) => {
            const a = rs[0].cases[tc] && rs[0].cases[tc].total, b = rs[1] && rs[1].cases[tc] && rs[1].cases[tc].total;
            const w = a === b ? "平" : a > b ? rs[0].effort || rs[0].platform : (rs[1].effort || rs[1].platform);
            return `<td class="pct">${esc(w)}</td>`;
          }).join("")}<td></td></tr>`;
        return `<h3 style="margin:0 0 12px;font-size:15px">${esc(m)} <span style="color:var(--ink-3);font-weight:500;font-size:12px">${esc(rs[0].effort || rs[0].platform)} vs ${esc(rs[1].effort || rs[1].platform)}</span></h3>
        <div class="btable"><div class="scroll"><table><thead>${head}</thead><tbody>${body}${win}</tbody></table></div></div>`;
      }).join("");
    }

    /* 迁移期参考排名 */
    let ref = "";
    if (pend.length) {
      const rows2 = pend.map((r, i) => {
        const done = TCS.filter((tc) => r.cases[tc]).length;
        return `<tr>
          <td><span class="rk">${i + 1}</span></td>
          <td><span class="nm">${vendorDot(data, r.vendor)}${esc(r.board)}</span></td>
          <td class="num strong">${fmt(caseSum(r))}</td>
          <td><span class="tag ${done >= 5 ? "mint" : ""}">${done}/8</span></td>
          ${TCS.map((tc) => `<td class="num">${r.cases[tc] ? fmt(r.cases[tc].total) : '<span style="color:var(--ink-3)">—</span>'}</td>`).join("")}
        </tr>`;
      }).join("");
      ref = `<div class="sec-sub">REFERENCE · 迁移期参考排名（非完整总分）</div>
        <div class="notebox">以下 run 尚未集齐 8 个用例，按<b>已评用例合计</b>排序，仅供参考，不参与正式总分榜。</div>
        <div class="btable"><div class="scroll"><table>
          <thead><tr><th>排名</th><th>模型 × 配置</th><th>已评合计</th><th>完成度</th>${TCS.map((t) => `<th>${t.toUpperCase()}</th>`).join("")}</tr></thead>
          <tbody>${rows2}</tbody></table></div></div>`;
    }

    el.innerHTML = `
      ${podium}
      <div class="sec-sub">FULL RANKING · 完整排名（${full.length} 个 run 八用例全齐）</div>
      <div class="btable"><div class="scroll"><table>
        <thead><tr><th>排名</th><th>模型 × 配置</th><th>合计分</th><th>百分位</th><th>百分制</th><th>评分日期</th><th></th></tr></thead>
        <tbody>${rows}</tbody></table></div></div>
      ${cmp}${ref}`;

    el.querySelectorAll("[data-x]").forEach((b) =>
      b.addEventListener("click", () => {
        const tr = b.closest("tr");
        tr.classList.toggle("open");
        b.textContent = tr.classList.contains("open") ? "－" : "＋";
      }));
  }

  /* ---------- 02 用例榜 ---------- */
  function renderBoard02(el, data) {
    const tabs = TCS.map((tc, i) => `<button data-tc="${tc}" class="${i === 0 ? "on" : ""}">${TC_SHORT[i]}</button>`).join("");
    el.innerHTML = `<div class="tabs">${tabs}</div><div id="case-pane"></div>`;
    const pane = el.querySelector("#case-pane");

    function paneFor(tc) {
      const meta = data.cases[tc];
      const have = data.rows.filter((r) => r.cases[tc]).sort((a, b) => a.cases[tc].rank - b.cases[tc].rank);
      if (!have.length) return `<div class="notebox">该用例暂无评分数据。</div>`;

      let head, rowHtml;
      if (tc === "tc-05") {
        head = `<tr><th>排名</th><th>模型 × 配置</th><th>呈现分</th><th>百分位</th><th>对账分(50)</th></tr>`;
        rowHtml = (r, c) => `
          <td><span class="rk">${c.rank}</span></td>
          <td><span class="nm">${vendorDot(data, r.vendor)}${esc(r.board)}</span></td>
          <td class="num strong">${fmt(c.total)}</td>
          <td><span class="mini-bar"><i style="width:${c.pct}%"></i></span><span class="pct">${pct(c.pct)}</span></td>
          <td class="num">${fmt(c.raw)}</td>`;
      } else if (tc === "tc-07") {
        const keys = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"];
        head = `<tr><th>排名</th><th>模型 × 配置</th><th>总分</th><th>百分位</th>${keys.map((k) => `<th>${k}</th>`).join("")}<th>冲突</th></tr>`;
        rowHtml = (r, c) => `
          <td><span class="rk">${c.rank}</span></td>
          <td><span class="nm">${vendorDot(data, r.vendor)}${esc(r.board)}</span></td>
          <td class="num strong">${fmt(c.total)}</td>
          <td><span class="mini-bar"><i style="width:${c.pct}%"></i></span><span class="pct">${pct(c.pct)}</span></td>
          ${keys.map((k) => `<td class="num">${fmt(c.items[k])}</td>`).join("")}
          <td class="num">${c.conflict > 0 ? "+" : ""}${fmt(c.conflict)}</td>`;
      } else {
        const keys = Object.keys(meta.items);
        head = `<tr><th>排名</th><th>模型 × 配置</th><th>总分</th><th>百分位</th>${keys.map((k) => `<th title="${esc(meta.items[k])}">${k}</th>`).join("")}<th></th></tr>`;
        rowHtml = (r, c) => {
          const marks = [c.x1 ? `<span class="tag mint">X1 +${fmt(c.x1)}</span>` : "",
                         c.adjust ? `<span class="tag rose">调整 ${fmt(c.adjust)}</span>` : ""].join("");
          return `
          <td><span class="rk">${c.rank}</span></td>
          <td><span class="nm">${vendorDot(data, r.vendor)}${esc(r.board)}</span></td>
          <td class="num strong">${fmt(c.total)}</td>
          <td><span class="mini-bar"><i style="width:${c.pct}%"></i></span><span class="pct">${pct(c.pct)}</span></td>
          ${keys.map((k) => `<td class="num">${fmt(c.items[k])}</td>`).join("")}
          <td>${marks}</td>`;
        };
      }
      const body = have.map((r) => {
        const c = r.cases[tc];
        return `<tr class="${c.rank <= 3 ? "tp" + c.rank : ""}">${rowHtml(r, c)}</tr>`;
      }).join("");
      return `<div class="btable"><div class="scroll"><table><thead>${head}</thead><tbody>${body}</tbody></table></div></div>
        <p style="font-size:12px;color:var(--ink-3);margin:-18px 0 34px 6px">${esc(meta.name)} · 满分 ${meta.max} · ${have.length} 个 run 参评 · 百分位 = 得分 ÷ 本用例榜首</p>`;
    }

    pane.innerHTML = paneFor("tc-01");
    el.querySelectorAll(".tabs button").forEach((b) =>
      b.addEventListener("click", () => {
        el.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("on", x === b));
        pane.innerHTML = paneFor(b.getAttribute("data-tc"));
      }));
  }

  /* ---------- 03 单项榜（领奖台化：每考察点只公开 Top 3 组） ---------- */
  function renderBoard03(el, data) {
    const tabs = TCS.map((tc, i) => `<button data-tc="${tc}" class="${i === 0 ? "on" : ""}">${TC_SHORT[i]}</button>`).join("");
    el.innerHTML = `<div class="tabs">${tabs}</div><div id="item-pane"></div>`;
    const pane = el.querySelector("#item-pane");

    function podiumRows(pairs, keep1) {
      /* pairs: [{board, vendor, v}] → 按分数分组取前 3 档 */
      const sorted = pairs.slice().sort((a, b) => b.v - a.v || a.board.localeCompare(b.board));
      const groups = [];
      for (const p of sorted) {
        if (groups.length && Math.abs(groups[groups.length - 1].v - p.v) < 1e-9) groups[groups.length - 1].list.push(p);
        else groups.push({ v: p.v, list: [p] });
      }
      const top = sorted.length ? sorted[0].v : 0;
      return groups.slice(0, 3).map((g, gi) => {
        const names = g.list.map((p) => esc(p.board)).join(" / ");
        const pc = top ? Math.round(g.v / top * 1000 + 1e-9) / 10 : 0;
        return `<div class="row r${gi + 1}">
          <span class="md">${["1st", "2nd", "3rd"][gi]}</span>
          <span class="who" title="${names}">${names}${g.list.length > 1 ? ` <span style="color:var(--ink-3)">×${g.list.length}</span>` : ""}</span>
          <span class="val">${keep1 || !Number.isInteger(g.v) ? fmt(g.v) : g.v}</span>
          <span class="pc">${pc.toFixed(1)}%</span>
        </div>`;
      }).join("");
    }

    function paneFor(tc) {
      const meta = data.cases[tc];
      const have = data.rows.filter((r) => r.cases[tc]);
      if (!have.length) return `<div class="notebox">该用例暂无评分数据。</div>`;
      const cards = [];

      const items = [];
      if (tc === "tc-05") items.push({ k: "__raw", label: "对账总分（→呈现 ×0.4）", max: 50 });
      Object.entries(meta.items).forEach(([k, nm]) =>
        items.push({ k, label: `${k} ${nm}`, max: meta.item_max[k] }));
      if (tc === "tc-07") {
        items.push({ k: "__conflict", label: "冲突处理（±）", max: "±" });
        items.push({ k: "__total", label: "总分（100 + 冲突）", max: 100 });
      }

      for (const it of items) {
        const pairs = [];
        for (const r of have) {
          const c = r.cases[tc];
          let v;
          if (it.k === "__raw") v = c.raw;
          else if (it.k === "__conflict") v = c.conflict;
          else if (it.k === "__total") v = c.total;
          else v = c.items[it.k];
          if (v !== undefined && v !== null) pairs.push({ board: r.board, vendor: r.vendor, v });
        }
        if (!pairs.length) continue;
        cards.push(`<div class="itemcard">
          <div class="ih"><b>${esc(it.label)}</b><span>满分 ${it.max} · ${pairs.length} 参评</span></div>
          ${podiumRows(pairs, tc !== "tc-07")}
        </div>`);
      }
      return `<div class="itemgrid">${cards.join("")}</div>
        <p style="font-size:12px;color:var(--ink-3);margin:-20px 0 40px 6px">每考察点公开前三名（含并列）；完整逐行记录与评分备注留存在内部评分档案。</p>`;
    }

    pane.innerHTML = paneFor("tc-01");
    el.querySelectorAll(".tabs button").forEach((b) =>
      b.addEventListener("click", () => {
        el.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("on", x === b));
        pane.innerHTML = paneFor(b.getAttribute("data-tc"));
      }));
  }

  /* ---------- 04 六维雷达（交互 SVG，排名换算百分位口径） ---------- */
  function renderBoard04(el, data) {
    const full = data.rows.filter((r) => r.complete && r.radar).sort((a, b) => a.rank - b.rank);
    if (!full.length) { el.innerHTML = `<div class="notebox">暂无完整六维数据。</div>`; return; }
    const dims = data.radar_dims;

    let sel = full[0].board, cmp = null, mode = "pct";

    el.innerHTML = `
      <div class="radar-wrap">
        <div class="radar-card">
          <div class="seg">
            <button data-m="pct" class="on">百分位（排名换算）</button>
            <button data-m="val">原始值（10 分制）</button>
          </div>
          <svg id="radar" viewBox="0 0 560 520" role="img" aria-label="六维雷达图"></svg>
          <div class="radar-legend" id="radar-legend"></div>
        </div>
        <div class="panel">
          <h3>选择模型</h3>
          <p class="hint">单击为主选（蓝），再点另一个为对比（薄荷绿），重复点击取消对比。</p>
          <div class="model-list" id="model-list"></div>
          <div class="dimvals" id="dimvals"></div>
        </div>
      </div>`;

    const svg = el.querySelector("#radar");
    const list = el.querySelector("#model-list");
    const dimvals = el.querySelector("#dimvals");
    const legend = el.querySelector("#radar-legend");

    list.innerHTML = full.map((r) => `
      <button data-b="${esc(r.board)}" class="${r.board === sel ? "on" : ""}">
        ${vendorDot(data, r.vendor)}<span class="mn">${esc(r.board)}</span>
        <span class="mv">均值 ${fmt(r.radar_mean)}</span>
      </button>`).join("");

    /* 几何 */
    const CX = 280, CY = 262, R = 168;
    const N = dims.length;
    const ang = (i) => -Math.PI / 2 + (i * 2 * Math.PI) / N;
    const pt = (i, ratio) => [CX + R * ratio * Math.cos(ang(i)), CY + R * ratio * Math.sin(ang(i))];
    const valuesOf = (r) => r.radar.map((d) => (mode === "pct" ? d.pct / 100 : d.value / 10));

    let cur = null, curCmp = null; // 动画插值
    function poly(vals) { return vals.map((v, i) => pt(i, Math.max(0, Math.min(1, v))).join(",")).join(" "); }

    function draw(selVals, cmpVals) {
      const rings = [0.25, 0.5, 0.75, 1].map((r) =>
        `<polygon points="${Array.from({ length: N }, (_, i) => pt(i, r).join(",")).join(" ")}"
          fill="${r === 1 ? "rgba(91,140,255,.05)" : "none"}" stroke="rgba(14,23,38,.1)" stroke-width="1"/>`).join("");
      const axes = dims.map((d, i) => {
        const [x, y] = pt(i, 1);
        const [lx, ly] = pt(i, 1.17);
        return `<line x1="${CX}" y1="${CY}" x2="${x}" y2="${y}" stroke="rgba(14,23,38,.09)"/>
          <text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle"
            font-size="13.5" font-weight="700" fill="#44506a">${esc(d.no)} ${esc(d.name)}</text>`;
      }).join("");
      const mkDots = (vals, color) => vals.map((v, i) => {
        const [x, y] = pt(i, Math.max(0, Math.min(1, v)));
        return `<circle cx="${x}" cy="${y}" r="4.5" fill="${color}" stroke="#fff" stroke-width="2"/>`;
      }).join("");
      svg.innerHTML = `
        <defs>
          <linearGradient id="rgA" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#5b8cff" stop-opacity=".38"/><stop offset="1" stop-color="#54c8f4" stop-opacity=".3"/>
          </linearGradient>
          <linearGradient id="rgB" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#2fd4b6" stop-opacity=".3"/><stop offset="1" stop-color="#9b8cff" stop-opacity=".24"/>
          </linearGradient>
        </defs>
        ${rings}${axes}
        ${cmpVals ? `<polygon points="${poly(cmpVals)}" fill="url(#rgB)" stroke="#2fd4b6" stroke-width="2" stroke-linejoin="round"/>${mkDots(cmpVals, "#2fd4b6")}` : ""}
        <polygon points="${poly(selVals)}" fill="url(#rgA)" stroke="#4a7bff" stroke-width="2.5" stroke-linejoin="round"/>
        ${mkDots(selVals, "#4a7bff")}`;
    }

    function tweenTo(selVals, cmpVals) {
      const from = cur || selVals.map(() => 0);
      const fromC = cmpVals ? curCmp || cmpVals.map(() => 0) : null;
      const t0 = performance.now();
      (function step(t) {
        const k = Math.min(1, (t - t0) / 420);
        const e = 1 - Math.pow(1 - k, 3);
        const v = selVals.map((s, i) => from[i] + (s - from[i]) * e);
        const vc = cmpVals ? cmpVals.map((s, i) => fromC[i] + (s - fromC[i]) * e) : null;
        draw(v, vc);
        if (k < 1) requestAnimationFrame(step);
        else { cur = selVals; curCmp = cmpVals || null; }
      })(t0);
    }

    function refresh() {
      const a = full.find((r) => r.board === sel);
      const b = cmp ? full.find((r) => r.board === cmp) : null;
      tweenTo(valuesOf(a), b ? valuesOf(b) : null);
      legend.innerHTML =
        `<span><i style="background:#4a7bff"></i>${esc(a.board)}</span>` +
        (b ? `<span><i style="background:#2fd4b6"></i>${esc(b.board)}</span>` : "");
      dimvals.innerHTML = a.radar.map((d, i) => {
        const v = mode === "pct" ? d.pct : d.value;
        const ratio = mode === "pct" ? d.pct / 100 : d.value / 10;
        const cv = b ? (mode === "pct" ? b.radar[i].pct : b.radar[i].value) : null;
        return `<div class="dimval">
          <div class="dn">${esc(d.no)} ${esc(d.name)} · ${esc(d.domain)}</div>
          <div class="dv">${mode === "pct" ? pct(v) : v.toFixed(2)}${cv !== null ? ` <span style="font-size:11px;color:#15977f">vs ${mode === "pct" ? pct(cv) : cv.toFixed(2)}</span>` : ""}</div>
          <div class="db"><i style="width:${Math.max(0, Math.min(100, ratio * 100))}%"></i></div>
        </div>`;
      }).join("");
      list.querySelectorAll("button").forEach((btn) => {
        const bb = btn.getAttribute("data-b");
        btn.classList.toggle("on", bb === sel);
        btn.classList.toggle("cmp", bb === cmp);
      });
    }

    list.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const b = btn.getAttribute("data-b");
      if (b === sel) { if (cmp) { sel = cmp; cmp = null; } }
      else if (b === cmp) cmp = null;
      else if (!cmp && b !== sel) cmp = b;
      else cmp = b;
      refresh();
    });
    el.querySelectorAll(".seg button").forEach((b) =>
      b.addEventListener("click", () => {
        mode = b.getAttribute("data-m");
        el.querySelectorAll(".seg button").forEach((x) => x.classList.toggle("on", x === b));
        cur = null; curCmp = null;
        refresh();
      }));
    refresh();
  }
})();
