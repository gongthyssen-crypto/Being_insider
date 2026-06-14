# 身在局中

一个以中国历史关键节点为题材的互动推演项目。

你选择一个历史人物和局势切口，输入自己的决策，系统会结合剧本种子、当前世界状态、历史回合记录和模型裁定，生成下一轮局势演化结果。当前仓库提供 3 个可直接体验的剧本：

- `朝鲜风云：袁世凯与甲午前夜`
- `万历新政前夜：张居正的第一盘棋`
- `山东红袄：李全的扩张与归附`

项目目前采用前后端分离结构：

- `frontend/`：React + Vite 前端，负责剧本选择页、详情推演页、回合历史时间轴展示
- `backend/`：FastAPI 后端，负责剧本 seed、会话状态、回合裁定、模型接入与 fallback
- `scripts/`：Windows PowerShell 启停脚本，方便本地一键试用

## 技术栈

- `Frontend`：React 18、Vite 5
- `Backend`：FastAPI、Pydantic、httpx、uvicorn
- `Python`：`3.11`
- `Node.js`：建议使用当前 LTS 版本
- `环境管理`：`uv`

## 目录结构

```text
.
├─ backend/
│  └─ app/
│     ├─ main.py                 # FastAPI 入口
│     ├─ routers/story.py        # 核心接口、会话与回合推进
│     ├─ deepseek_service.py     # 模型 prompt 和外部 API 请求
│     ├─ content.py              # 三个历史剧本的种子数据
│     ├─ schemas.py              # 请求/响应数据结构
│     └─ session_store.py        # 会话与历史记录的内存存储
├─ frontend/
│  ├─ src/App.jsx                # 前端主要页面逻辑
│  ├─ src/styles.css             # 样式
│  └─ vite.config.js             # 本地代理配置
└─ scripts/
   ├─ setup.ps1                  # 初始化 Python/前端依赖
   ├─ start-all.ps1              # 一次启动前后端
   ├─ stop-all.ps1               # 一次停止前后端
   ├─ start-backend.ps1          # 单独启动后端
   └─ start-frontend.ps1         # 单独启动前端
```

## 快速开始

### 1. 安装依赖

在项目根目录执行：

```powershell
.\scripts\setup.ps1
```

这个脚本会完成三件事：

1. 创建 `.venv`
2. 用 `uv sync` 安装后端依赖
3. 用 `npm install --prefix frontend` 安装前端依赖

### 2. 启动项目

```powershell
.\scripts\start-all.ps1
```

默认端口：

- 前端：`http://127.0.0.1:18422`
- 后端：`http://127.0.0.1:18421`

启动后直接打开前端地址即可体验。

### 3. 停止项目

```powershell
.\scripts\stop-all.ps1
```

## 本地试用原理

这一部分是给上传 GitHub 后别人第一次拉下来就能理解“这个项目本地到底怎么跑起来”的说明。

### 1. 启动链路

- `setup.ps1` 只负责准备环境，不启动服务
- `start-all.ps1` 先启动后端，再等 2 秒，然后启动前端
- `start-backend.ps1` 用 `.venv\Scripts\python.exe` 拉起 `uvicorn app.main:app --host 127.0.0.1 --port 18421`
- `start-frontend.ps1` 在 `frontend/` 目录下执行 `npm run dev -- --host 127.0.0.1 --port 18422 --strictPort`

### 2. 前后端如何连起来

前端代码在 `frontend/src/App.jsx` 里把接口根路径写成了：

```js
const API_ROOT = "/api";
```

这意味着前端开发环境下不会直接把请求写死成 `http://127.0.0.1:18421/api`，而是统一请求 `/api/...`。

真正把请求转发给后端的是 `frontend/vite.config.js`：

```js
proxy: {
  "/api": {
    target: "http://127.0.0.1:18421",
    changeOrigin: true,
  },
}
```

也就是说，本地试用时的链路是：

```text
浏览器 -> Vite 前端开发服务器 18422 -> 代理转发 /api -> FastAPI 后端 18421
```

这样做的好处是：

- 前端不用到处写死后端域名
- 本地开发时不容易碰到跨域问题
- 后面如果要改后端地址，只需要改代理配置或部署配置

### 3. 一次回合是怎么完成的

用户在前端输入行动后，主要会经过下面这条链路：

1. 前端调用 `POST /api/sessions/{session_id}/turns`
2. 后端在 `backend/app/routers/story.py` 中读取当前 session 和历史回合
3. 后端把当前剧本 seed、世界状态、最近历史和玩家输入交给 `backend/app/deepseek_service.py`
4. 如果前端运行时设置里填了可用的聊天 `API key / base URL / model`，就请求外部模型 API
5. 如果没有配置 key，或者外部请求报错，就自动走本地 fallback
6. 后端把新的回合结果、阶段性结局、世界变化写回 session store
7. 前端刷新页面状态，显示本轮推演结果和时间轴记录

### 4. 为什么没配 API 也能本地试

因为这个项目内置了本地裁定器。

在 `backend/app/routers/story.py` 里，后端会先尝试调用 `request_turn_resolution(...)`。如果：

- 没有在前端运行时设置中填写聊天 `API key`
- 外部模型请求超时
- 外部模型返回空内容
- 外部模型返回的 JSON 无法解析

系统就会自动退回本地逻辑，继续生成一轮可用结果，而不是让整个流程直接报错。

所以：

- 你要做前端联调，不一定非要先配真实模型 key
- 你要演示完整流程，也可以先用 fallback 跑通
- 你要看真实大模型效果，再在前端运行时设置里补聊天配置即可

### 5. 当前会话数据存在哪里

当前项目使用的是内存级会话存储，不接数据库。

也就是说：

- 重启后端后，历史 session 会丢失
- 这更适合课堂项目、Demo 展示和快速迭代
- 如果后续要做长期保存，可以继续把 `session_store.py` 换成 SQLite / Postgres / Redis

## 单独启动前后端

如果你不想用一键脚本，也可以分开启动：

### 只启后端

```powershell
.\scripts\start-backend.ps1
```

后端健康检查：

- 根路径：`http://127.0.0.1:18421/`
- Swagger 文档：`http://127.0.0.1:18421/docs`
- 健康接口：`http://127.0.0.1:18421/api/health`

### 只启前端

```powershell
.\scripts\start-frontend.ps1
```

## 后端接口概览

目前前端主要依赖下面这些接口：

- `GET /api/health`：查看服务状态和当前模型模式
- `GET /api/scenarios`：读取剧本卡片列表
- `GET /api/scenarios/{scenario_id}`：读取某个剧本 seed
- `POST /api/sessions`：创建一局新的推演 session
- `GET /api/sessions/{session_id}`：读取当前 session 快照
- `GET /api/sessions/{session_id}/history`：读取历史回合
- `POST /api/sessions/{session_id}/turns`：提交一轮玩家决策并推进剧情

其中最关键的是：

- `POST /api/sessions`
- `POST /api/sessions/{session_id}/turns`

这两个接口基本决定了“开局”和“继续推演”的主流程。

## 在哪里调 API

如果你上传到 GitHub 后，别人要接自己的模型、换供应商、改 prompt，最常用的是下面这几个文件。

### 1. 改运行时模型配置

模型配置入口在：

- `frontend/src/App.jsx`
- `backend/app/runtime_settings.py`

当前默认配置来源如下：

- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`

推荐方式是直接在首页的 Runtime Settings 面板里填写：

- `Chat API base URL`
- `Chat model`
- `API key`

这些设置保存后会立即进入后端运行时内存，下一回合直接生效，不需要重启。

注意：

- 当前项目没有自动加载 `.env` 文件
- 也就是说，把变量写进一个 `.env` 文本文件本身不会自动生效
- 现在的实现是 `os.getenv(...)` 直接读取系统环境变量或当前 PowerShell 会话环境变量

### 2. 改 prompt

模型系统提示词在：

- `backend/app/deepseek_service.py`

重点函数：

- `_system_prompt(seed)`
- `build_messages(seed, session, history, action_text)`

你要改“模型怎么理解任务”，通常改这两个地方：

- `_system_prompt(seed)`：定义全局规则，比如输出 JSON、不要复述输入、多少回合后允许结局
- `build_messages(...)`：决定把哪些上下文喂给模型，比如最近几轮历史、当前局势、玩家动作

### 3. 改外部请求格式

如果你想把 DeepSeek 换成别的兼容接口，主要改这里：

- `backend/app/deepseek_service.py` 中的 `request_turn_resolution(...)`

这个函数里定义了：

- 请求 URL：`{DEEPSEEK_BASE_URL}/chat/completions`
- 请求头：`Authorization: Bearer ...`
- 请求体：`model`、`messages`、`response_format`、`max_tokens`
- 返回解析：从 `choices[0].message.content` 取出 JSON

也就是说，换供应商一般有两种方式：

1. 兼容 OpenAI / DeepSeek 风格接口：多数情况下只改 `DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL`
2. 不兼容当前返回格式：需要连 `request_turn_resolution(...)` 的请求和解析一起改

### 4. 改本地 fallback 规则

如果你想改“没走模型时，本地应该怎么判”，主要在：

- `backend/app/routers/story.py`

重点函数：

- `_classify_action(...)`
- `_summarize_action(...)`
- `_build_turn_result(...)`
- `_build_stage_ending(...)`
- `_build_stage_ending_summary(...)`

这里决定了：

- 本地 fallback 如何概括玩家动作
- fallback 下每轮叙事怎么写
- 什么时候允许阶段性结局
- 结局卡里显示哪些字段

### 5. 改剧本内容

如果你想新增剧本或改历史背景，在：

- `backend/app/content.py`

这里维护每个剧本的：

- 标题
- 时代
- 剧情摘要
- 玩家角色
- 历史锚点
- 核心目标
- 失败风险
- 开局选项

## 推荐的 API 调整流程

如果你是第一次接自己的模型，建议按这个顺序改：

1. 先在前端运行时设置里填 `API key / base URL / model`，确认 `/api/health` 里模型模式不是 fallback
2. 再打一轮实际推演，确认 `POST /api/sessions/{session_id}/turns` 能正常返回
3. 如果想调风格，先改 `_system_prompt(seed)`
4. 如果想让模型看到更多上下文，再改 `build_messages(...)`
5. 如果接口供应商不同，再改 `request_turn_resolution(...)`
6. 最后再决定是否保留 fallback 逻辑

## GitHub 上传前注意事项

### 1. 不要提交真实 API Key

本仓库现在不会再内置默认的真实 key，但你仍然要注意：

- 不要把真实聊天 `API key` 写死进代码
- 不要把带 key 的启动脚本提交到仓库
- 不要把本机环境导出文件提交到仓库

### 2. 当前忽略项

`.gitignore` 已忽略：

- `.venv/`
- `.runtime/`
- `node_modules/`
- `dist/`

这些目录通常都不需要上传。

### 3. 如果你想给别人更友好地演示

可以后续继续补这些内容：

- README 截图
- 项目演示 GIF
- 常见问题 FAQ
- 新增剧本指南
- 模型接入模板

## 开发说明

### 后端依赖

`pyproject.toml` 当前核心依赖包括：

- `fastapi`
- `httpx`
- `uvicorn[standard]`
- `pydantic`

### 前端依赖

`frontend/package.json` 当前核心依赖包括：

- `react`
- `react-dom`
- `vite`
- `@vitejs/plugin-react`

## 适合继续扩展的方向

- 接数据库，保存用户历史对局
- 增加更多历史人物与剧本
- 把单段结局改成多维评分
- 支持不同模型供应商切换
- 增加管理员配置页，直接在前端填写模型参数

## License

如需开源，请按你的课程或项目要求自行补充许可证文件。
