# AI 能力专项测试 · GitHub Pages

七题四方向公开站。视觉与测评视频统一为「瑞士排版 × 蓝图信息密度」：米白纸面、近黑文字、系统蓝强调色、垂直栏线、等宽元数据与大字号成绩展示。

## 页面结构

```text
pages/
├── index.html                  # 首页：总榜速览、四方向、七题索引
├── tc-01.html … tc-07.html    # 七道题：档案、排名、完整题面
├── tc-08.html                 # 旧八题制归档说明
├── board-01.html              # 总分榜
├── board-02.html              # 七道题逐题榜
├── board-03.html              # 检查点前三档
├── board-04.html              # 文字 / 前端 / 后端 / 知识四方向榜
├── data/site.json             # 公开版站点数据（生成物）
├── assets/style.css           # 全站设计系统
├── assets/app.js              # 榜单与首页数据渲染
└── build.py                   # 唯一生成入口
```

## 数据口径

- 当前体系：7 个题目、4 个能力方向、总分参考 400。
- 题目分先按全库基准归一，再按 `tasks.yaml` 的固定权重合成方向分。
- `build.py` 只读取 `../评分数据/out/board-data.json` 和 `../prompts/提示词/`。
- 生成器只写 `pages/`，不会刷新或修改站外评分数据。
- 公开数据包含模型身份、排名、分数、方向分、逐题分和检查点分；评语、金句、扣分备注、内部裁决与视频配置不会写入站点。

## 更新站点

在项目根目录运行：

```powershell
python pages/build.py
```

或在 `pages/` 内运行：

```powershell
python build.py
```

## 本地预览

```powershell
python -m http.server 8080 --directory pages
```

打开 `http://localhost:8080/`。榜单通过 `fetch("data/site.json")` 读取数据，因此不要用 `file://` 直接双击预览。

## 发布

`pages/` 是独立 Git 仓库，继续使用现有 GitHub Pages 发布方式即可。全站使用相对路径，仓库根部署和子路径部署均可。
