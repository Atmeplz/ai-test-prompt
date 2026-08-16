# 提示词全库 + 评分榜 · GitHub Pages

与 `视频模板/` 同风格（瑞士风格 × 蓝图信息密度，米白 `#F4F0E6` / 近黑 `#0D0D0D` / 主题色 `#10A37F`）的静态站点，展示：

- AI 能力专项测试的完整 8 则提示词（TC-01 ~ TC-08，2026-08-13 检查点体系升级后同步）
- 四张评分榜：01 总分榜 / 02 用例榜 / 03 单项榜 / 04 六维数据（由 `评分数据/` 生成）

## 目录

```
pages/
├── index.html           # 首页：8 用例入口 + 4 评分榜入口
├── tc-01.html … tc-08.html   # 各用例完整提示词（终端窗展示）
├── board-01.html … board-04.html  # 四张评分榜（由 评分数据/*.md 渲染）
├── build.py             # 生成脚本（提示词 + 评分榜全部生成）
├── assets/
│   ├── style.css        # 设计令牌（换主题色只改 --blue 一处）
│   └── fonts/           # Helvetica Now Display ExtBlk Ita（来自视频模板资产）
├── .nojekyll
└── README.md
```

## 更新提示词

编辑 `../prompts/提示词/TC-XX.md` 后重跑：

```
python build.py
```

## 更新评分榜

数据唯一事实源是 `../评分数据/scores.yaml`，两条 build 链：

```
cd ../评分数据 && python build.py   # 重算 01~04.md + out/board-data.json（禁止手改）
cd ../pages && python build.py      # 重新渲染 board-01~04.html + index.html
```

`board-01~04.html` 直接读取 `../评分数据/0X-*.md` 渲染，无需手工维护。

## 本地预览

```
python -m http.server 8080 --directory pages
# 或 npx serve pages
# 打开 http://localhost:8080
```

## 发布到 GitHub Pages

1. 把 `pages/` 提交到 Git 仓库并推到 GitHub：
   ```
   cd pages
   git add .
   git commit -m "提示词全库 + 评分榜站点"
   git remote add origin https://github.com/<用户名>/<仓库>.git
   git push -u origin main
   ```
2. GitHub 仓库 → **Settings → Pages** → Source 选 **Deploy from a branch**，Branch 选 `main`、目录 `/ (root)` → Save。
3. 等 1~2 分钟构建，访问 `https://<用户名>.github.io/<仓库>/`（如果仓库名不是 `<用户名>.github.io`，站点在子路径下，所有链接均为相对路径，可直接访问）。

> 注：若仓库根目录就是本 `pages/` 内容（把站点文件直接放仓库根），则无需子路径；本目录内全部使用相对链接，两种部署方式均可正常工作。
