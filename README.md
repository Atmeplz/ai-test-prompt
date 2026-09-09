# AI 能力专项测试 · GitHub Pages

七题四方向公开站。保留 cards 的米白纸面、近黑文字、蓝色强调、等宽元数据和斜体成绩；网页采用自适应内容流，首页保留蓝色主入口，内页用细蓝线和紧凑页头组织榜单。

手机端的分数表可左右滑动，模型与名次固定在左侧；检查点同分名单默认展示三个测评，其余可展开，模型同时标注运行配置。支持键盘操作、减少动态效果设置和加载失败重试。

## 页面结构

```text
pages/
├── index.html                  # 首页：总榜速览、四方向与方法说明
├── board-01.html              # 总分榜
├── board-02.html              # 七道题逐题榜
├── board-03.html              # 检查点前三档
├── board-04.html              # 文字 / 前端 / 后端 / 知识四方向榜
├── data/site.json             # 公开版站点数据（生成物）
├── assets/style.css           # 全站设计系统
├── assets/app.js              # 榜单与首页数据渲染
└── build.py                   # 唯一生成入口
```

## 全站公告

顶部导航下方的浅色公告带会出现在所有页面。访客关闭后，浏览器会用 Cookie 记住当前公告编号一年；编辑 `build.py` 顶部的 `ANNOUNCEMENT` 并更新 `id`，即可让下一条公告重新出现。重新运行构建后，公告标签、标题和说明文字会一次同步到全站。

## 数据口径

- 当前体系：7 个题目、4 个能力方向、总分参考 400。
- 题目分先按全库基准归一，再按 `tasks.yaml` 的固定权重合成方向分。
- `build.py` 只读取 `../评分数据/out/board-data.json`。
- 生成器只写 `pages/`，不会刷新或修改站外评分数据。
- 公开数据包含模型身份、排名、分数、方向分、逐题分和检查点分；提示词、评语、金句、扣分备注、内部裁决与视频配置不会写入站点。

## 更新站点

在项目根目录运行：

```powershell
python pages/build.py
```

若评分登记已经更新但上游 JSON 尚未生成，先运行 `python -X utf8 评分数据/build.py`，再构建本站。页面数据请求每次校验缓存；修改 CSS / JS 时同步递增 `build.py` 的 `ASSET_VERSION`。

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
