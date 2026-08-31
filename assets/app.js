(function () {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
  const fmt = (value, digits = 2) => Number(value).toFixed(digits).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
  const pct = (value) => `${Number(value).toFixed(1)}%`;

  setupAnnouncement();

  fetch("data/site.json?v=20260901-1")
    .then((response) => response.json())
    .then((data) => boot(data));

  function setupAnnouncement() {
    const notice = $(".site-notice");
    const cookie = `ai_test_notice=${notice.dataset.notice}`;

    if (document.cookie.split("; ").includes(cookie)) {
      notice.remove();
      return;
    }

    $(".notice-close", notice).addEventListener("click", () => {
      document.cookie = `${cookie}; Max-Age=31536000; Path=/; SameSite=Lax`;
      notice.classList.add("is-leaving");
      notice.addEventListener("animationend", () => notice.remove(), { once: true });
    });
  }

  function boot(data) {
    const rows = data.rows.filter((row) => row.complete).sort((a, b) => a.rank - b.rank);

    if ($("#top-preview")) renderTopPreview(data, rows);
    if ($("#direction-preview")) renderDirectionPreview(data, rows);
    const board = $("[data-site]");
    if (board) {
      const renderers = {
        "01": renderTotalBoard,
        "02": renderTaskBoard,
        "03": renderCheckpointBoard,
        "04": renderDirectionBoard,
      };
      renderers[board.dataset.site](board, data, rows);
    }

    animateNumbers();
    requestAnimationFrame(() => document.body.classList.add("is-ready"));
  }

  function vendorStyle(row) {
    const background = row.gradient
      ? `linear-gradient(135deg,${row.gradient.join(",")})`
      : row.color || "#0d0d0d";
    return `--vendor:${row.color || "#0d0d0d"};--vendor-bg:${background}`;
  }

  function vendorMark(row) {
    return `<i class="vendor-mark" style="${vendorStyle(row)}"></i>`;
  }

  function modelCell(row) {
    return `<span class="model-cell">${vendorMark(row)}<span><b>${esc(row.model)}</b><small>${esc(row.effort || "default")} · ${esc(row.platform || row.source || "direct")}</small></span></span>`;
  }

  function count(value, suffix = "", digits = 1) {
    return `<span class="countup" data-count="${Number(value)}" data-digits="${digits}" data-suffix="${esc(suffix)}">${fmt(value, digits)}${suffix}</span>`;
  }

  function renderTopPreview(data, rows) {
    $("#top-preview").innerHTML = rows.slice(0, 5).map((row) => `
      <a class="preview-row drop" href="board-01.html" style="${vendorStyle(row)}">
        <span class="preview-rank">No. ${String(row.rank).padStart(2, "0")}</span>
        <span class="preview-model">${vendorMark(row)}<b>${esc(row.model)}</b><small>${esc(row.vendor_display)}</small></span>
        <span class="preview-score">${count(row.total, "", 1)}<small>/ ${data.meta.total_ref}</small></span>
        <span class="preview-pct">${pct(row.pct100)}</span>
        <i class="score-rule"><i style="--w:${Math.min(row.pct100, 100) / 100}"></i></i>
      </a>
    `).join("");
  }

  function renderDirectionPreview(data, rows) {
    $("#direction-preview").innerHTML = Object.entries(data.directions).map(([key, direction], index) => {
      const ranking = rows.slice().sort((a, b) => a.directions[key].rank - b.directions[key].rank);
      const leader = ranking[0];
      return `<a class="direction-card drop" style="--delay:${index * 80}ms;${vendorStyle(leader)}" href="board-04.html#${key}">
        <span class="direction-index">0${index + 1} / 04</span>
        <h3>${esc(direction.zh)}</h3>
        <em>${esc(direction.en)}</em>
        <div class="direction-leader">${vendorMark(leader)}<span><small>LEADER</small><b>${esc(leader.model)}</b></span></div>
        <strong>${count(leader.directions[key].value, "", 1)}</strong>
        <span class="direction-arrow">↗</span>
      </a>`;
    }).join("");
  }

  function boardIntro(code, en, title, note) {
    return `<header class="content-head"><span>// ${esc(code)}</span><div><h2>${esc(title)}</h2><p>${esc(note)}</p></div><b>${esc(en)}</b></header>`;
  }

  function renderTotalBoard(target, data, rows) {
    const podium = rows.slice(0, 3).map((row, index) => `
      <article class="podium-card rank-${index + 1} drop" style="${vendorStyle(row)}">
        <span>No. ${String(row.rank).padStart(2, "0")}</span>
        <div>${vendorMark(row)}<b>${esc(row.model)}</b><small>${esc(row.vendor_display)} · ${esc(row.effort || "default")}</small></div>
        <strong>${count(row.total, "", 1)}</strong>
        <em>/ ${data.meta.total_ref}</em>
        <i><i style="--w:${Math.min(row.pct100, 100) / 100}"></i></i>
        <p>${pct(row.pct100)} OF REFERENCE</p>
      </article>
    `).join("");

    const directionHeads = Object.values(data.directions).map((direction) => `<th>${esc(direction.en)}</th>`).join("");
    const tableRows = rows.map((row) => `
      <tr style="${vendorStyle(row)}">
        <td class="rank-cell">${String(row.rank).padStart(2, "0")}</td>
        <td>${modelCell(row)}</td>
        ${Object.keys(data.directions).map((key) => `<td>${fmt(row.directions[key].value, 1)}</td>`).join("")}
        <td class="total-cell">${fmt(row.total, 1)}</td>
        <td>${pct(row.pct100)}</td>
      </tr>
    `).join("");

    target.innerHTML = `
      ${boardIntro("FINAL", "REFERENCE 400", "总榜名次", "总分 = 文字 + 前端 + 后端 + 知识")}
      <div class="podium-grid">${podium}</div>
      <div class="table-shell">
        <table class="report-table total-table">
          <thead><tr><th>NO.</th><th>MODEL / RUN</th>${directionHeads}<th>TOTAL</th><th>REF.</th></tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div>`;
  }

  function taskTabs(data, active) {
    return `<div class="report-tabs">${Object.entries(data.tasks).map(([key, task]) =>
      `<button type="button" data-key="${esc(key)}" class="${key === active ? "on" : ""}"><span>${String(task.order).padStart(2, "0")}</span><b>${esc(task.zh)}</b></button>`
    ).join("")}</div>`;
  }

  function taskTable(data, rows, key) {
    const task = data.tasks[key];
    const caseMeta = data.cases[key];
    const ranking = rows.filter((row) => row.cases[key]).sort((a, b) => a.cases[key].rank - b.cases[key].rank);
    const itemCodes = Object.keys(caseMeta.items);

    return `<div class="task-board-head">
        <div><span>// TASK.${String(task.order).padStart(2, "0")}</span><h3>${esc(task.name)}</h3><p>${esc(task.domain)}</p></div>
        <div><b>${task.ref}</b><span>RAW REFERENCE</span></div>
      </div>
      <div class="table-shell"><table class="report-table task-table">
        <thead><tr><th>NO.</th><th>MODEL / RUN</th><th>NORM.</th><th>RAW</th>${itemCodes.map((code) => `<th>${esc(code)}<small>${esc(caseMeta.items[code])}</small></th>`).join("")}</tr></thead>
        <tbody>${ranking.map((row) => {
          const result = row.cases[key];
          return `<tr style="${vendorStyle(row)}"><td class="rank-cell">${String(result.rank).padStart(2, "0")}</td><td>${modelCell(row)}</td><td class="total-cell">${fmt(result.total, 1)}</td><td>${fmt(result.raw_total, 2)}</td>${itemCodes.map((code) => `<td>${fmt(result.items[code], 1)}</td>`).join("")}</tr>`;
        }).join("")}</tbody>
      </table></div>`;
  }

  function renderTaskBoard(target, data, rows) {
    const first = Object.keys(data.tasks)[0];
    target.innerHTML = `${boardIntro("TASKS", "07 TASKS", "逐题排名", "归一分与原始分同时保留")}${taskTabs(data, first)}<div class="tab-pane">${taskTable(data, rows, first)}</div>`;
    bindTabs(target, (key) => taskTable(data, rows, key));
  }

  function checkpointCards(data, rows, key) {
    const task = data.tasks[key];
    const meta = data.cases[key];
    const cards = Object.entries(meta.items).map(([code, label], itemIndex) => {
      const ranking = rows
        .filter((row) => row.cases[key] && row.cases[key].items[code] !== undefined)
        .sort((a, b) => b.cases[key].items[code] - a.cases[key].items[code]);
      const levels = [...new Set(ranking.map((row) => row.cases[key].items[code]))].slice(0, 3);
      const places = levels.map((value, index) => {
        const tied = ranking.filter((row) => row.cases[key].items[code] === value);
        return `<li><span>0${index + 1}</span><div>${tied.map((row) => `<b style="${vendorStyle(row)}">${vendorMark(row)}${esc(row.model)}</b>`).join("")}</div><strong>${fmt(value, 1)}</strong></li>`;
      }).join("");
      return `<article class="checkpoint-card drop" style="--delay:${itemIndex * 70}ms"><header><span>${esc(code)}</span><h3>${esc(label)}</h3><b>REF ${fmt(meta.item_max[code], 1)}</b></header><ol>${places}</ol></article>`;
    }).join("");
    return `<div class="checkpoint-task-head"><span>// TASK.${String(task.order).padStart(2, "0")}</span><h3>${esc(task.name)}</h3></div><div class="checkpoint-grid">${cards}</div>`;
  }

  function renderCheckpointBoard(target, data, rows) {
    const first = Object.keys(data.tasks)[0];
    target.innerHTML = `${boardIntro("POINTS", "TOP 3 LEVELS", "检查点索引", "同分并列显示；每个检查点公开前三个分数档")}${taskTabs(data, first)}<div class="tab-pane">${checkpointCards(data, rows, first)}</div>`;
    bindTabs(target, (key) => checkpointCards(data, rows, key));
  }

  function directionTable(data, rows, key) {
    const direction = data.directions[key];
    const ranking = rows.slice().sort((a, b) => a.directions[key].rank - b.directions[key].rank);
    const weights = Object.entries(direction.weight).map(([taskKey, weight]) => `<span><b>${esc(data.tasks[taskKey].zh)}</b>${fmt(weight * 100, 0)}%</span>`).join("");
    return `<div class="direction-board-head">
        <div><span>// DIRECTION</span><h3>${esc(direction.zh)}</h3><p>${esc(direction.en)}</p></div>
        <div class="weight-map">${weights}</div>
      </div>
      <div class="direction-ranking">${ranking.map((row) => {
        const score = row.directions[key];
        return `<div class="direction-row drop" style="${vendorStyle(row)}"><span class="result-rank">${String(score.rank).padStart(2, "0")}</span>${modelCell(row)}<strong>${fmt(score.value, 1)}</strong><span>${pct(score.pct)}</span><i><i style="--w:${Math.min(score.value, 100) / 100}"></i></i></div>`;
      }).join("")}</div>`;
  }

  function renderDirectionBoard(target, data, rows) {
    const keys = Object.keys(data.directions);
    const hashKey = location.hash.slice(1);
    const first = keys.includes(hashKey) ? hashKey : keys[0];
    const tabs = `<div class="direction-tabs">${keys.map((key, index) => `<button type="button" data-key="${esc(key)}" class="${key === first ? "on" : ""}"><span>0${index + 1}</span><b>${esc(data.directions[key].zh)}</b><small>${esc(data.directions[key].en)}</small></button>`).join("")}</div>`;
    target.innerHTML = `${boardIntro("DIRECTIONS", "04 BOARDS", "四方向能力", "方向分天然以 100 为参考")}${tabs}<div class="tab-pane">${directionTable(data, rows, first)}</div>`;
    bindTabs(target, (key) => {
      history.replaceState(null, "", `#${key}`);
      return directionTable(data, rows, key);
    });
  }

  function bindTabs(root, renderer) {
    const pane = $(".tab-pane", root);
    $$('[data-key]', root).forEach((button) => {
      button.addEventListener("click", () => {
        $$('[data-key]', root).forEach((item) => item.classList.toggle("on", item === button));
        pane.innerHTML = renderer(button.dataset.key);
        animateNumbers(pane);
        requestAnimationFrame(() => pane.classList.add("is-ready"));
      });
    });
  }

  function animateNumbers(root = document) {
    $$(".countup", root).forEach((node) => {
      const target = Number(node.dataset.count);
      const digits = Number(node.dataset.digits);
      const suffix = node.dataset.suffix || "";
      const started = performance.now();
      const duration = 900;
      function tick(now) {
        const progress = Math.min(1, (now - started) / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        node.textContent = `${fmt(target * eased, digits)}${suffix}`;
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }
})();
