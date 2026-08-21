# 提示词全库 × 评分榜 · GitHub Pages

清透玻璃拟态静态站点：Three.js 琉璃流体球 Hero + 数据驱动四榜，展示：

- AI 能力专项测试的完整 8 则提示词（TC-01 ~ TC-08）
- 四张评分榜：01 总分榜 / 02 用例榜 / 03 单项榜 / 04 六维雷达（交互式）

## 目录

```
pages/
├── index.html               # 首页：Hero + 总榜速览 Top5 + 8 用例 + 4 榜入口
├── tc-01.html … tc-08.html  # 各用例完整提示词（玻璃终端展示）
├── board-01.html … board-04.html  # 四张评分榜（外壳，正文由 app.js 渲染）
├── data/
│   └── site.json            # 公开版站点数据（自动生成，禁止手改）
├── assets/
│   ├── style.css            # 设计系统（清透玻璃拟态令牌）
│   ├── hero.js              # Three.js Hero（CDN 加载，失败自动退化为纯 CSS 极光）
│   ├── app.js               # 读 data/site.json 渲染四榜 + 雷达图 + 首页速览
│   └── fonts/               # Helvetica Now Display ExtBlk Ita
├── build.py                 # 生成脚本（数据 + 页面一条命令）
├── .nojekyll
└── README.md
```

## 日常维护（唯一入口）

数据唯一事实源是 `../评分数据/scores.yaml`。**改分 / 加模型 / 改提示词后，只需一条命令**：

```
cd pages && python build.py
```

它会自动：

1. 检测 `scores.yaml` 是否比 `out/board-data.json` 新——是则先重跑 `../评分数据/build.py` 全量重算；
2. 派生公开版 `data/site.json`（剥离内部字段，见下）；
3. 重新渲染全部 HTML。

然后把 `pages/` 提交推送即可，GitHub Pages 自动更新。

> 注意：`../评分数据/build.py` 依赖 `pyyaml`，请用装了 pyyaml 的 Python 跑整条链
>（例如系统 Python `py build.py`，或先 `pip install pyyaml`）。

## 公开 vs 内部（数据分层）

站点只公开"看得懂"的结果数据：

- 排名、合计分、百分位、百分制、逐用例得分、考察点得分、六维数值
- 单项榜只公开每考察点**前三名（含并列）**

以下内容留在 `../评分数据/*.md` 内部档案，**不进站点**：

- 逐行评分备注、扣分判例、合计核对（重算记录）
- 画像与金句（用户定稿，视频备用）
- 取数规则、迁移期标注等内部工作流说明

`pages/build.py` 的 `build_site_json()` 是公开/内部的唯一分界线：字段在那里显式挑选，
新增字段默认不会上站。

## 本地预览

```
python -m http.server 8080 --directory pages
# 打开 http://localhost:8080
```

榜单页通过 `fetch("data/site.json")` 取数，请用 http 服务预览（`file://` 直接双击打开会因浏览器安全策略取不到数据）。

## 发布到 GitHub Pages

1. 把 `pages/` 提交到 Git 仓库并推到 GitHub；
2. 仓库 → **Settings → Pages** → Source 选 **Deploy from a branch**，Branch 选 `main`、目录 `/ (root)`；
3. 等 1~2 分钟，访问 `https://<用户名>.github.io/<仓库>/`。

全站相对路径，仓库根部署或子路径部署均可；Three.js 走 jsdelivr CDN，加载失败时 Hero 自动退化为 CSS 极光背景，不影响任何内容展示。
