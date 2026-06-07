# AI 中国古代历史情景推演项目开发文档

## 1. 项目定位

### 1.1 项目名称

AI 中国古代历史情景推演系统

### 1.2 项目目标

本项目面向“人工智能导论”课程大作业，目标是实现一个以中国古代历史事件为背景的交互式推演系统。玩家将扮演历史关键节点中的决策者，在给定背景、身份、局势和初始参考选项的前提下做出自己的判断，随后由 AI 根据玩家输入继续推演历史走向。

### 1.3 核心设计原则

1. 开局结构化，后续推演自由化。
2. 玩家不只点击预设选项，还可以自己写决策。
3. AI 负责裁定和续写，但历史背景与主约束仍由系统控制。
4. 项目首先保证“能稳定演示”，其次再提升“生成自由度”。

## 2. 技术栈

### 2.1 后端

- Python 3.11
- FastAPI
- Pydantic v2
- Uvicorn
- `uv`

### 2.2 前端

- React 18
- Vite 5
- 原生 CSS

### 2.3 当前端口

- 后端：`18421`
- 前端：`18422`

## 3. 当前项目状态

当前仓库已经有一个可运行的基础版本：

1. 后端可以返回历史场景列表。
2. 后端已经支持按章节创建会话、记录回合状态并接收自由输入。
3. 前端可以展示章节背景、局势摘要、自然语言决策输入框和回合历史。
4. 已经具备大模型接入前的前后端骨架，并支持本地 fallback 与 DeepSeek 官方接口切换。

### 3.1 当前目录结构

```text
d:\lishi2
├─ backend
│  └─ app
│     ├─ main.py
│     ├─ content.py
│     ├─ schemas.py
│     └─ routers
│        └─ story.py
├─ frontend
│  ├─ package.json
│  ├─ vite.config.js
│  └─ src
│     ├─ App.jsx
│     ├─ main.jsx
│     └─ styles.css
├─ scripts
│  ├─ setup.ps1
│  ├─ start-all.ps1
│  ├─ start-backend.ps1
│  ├─ start-frontend.ps1
│  ├─ stop-all.ps1
│  ├─ stop-backend.ps1
│  └─ stop-frontend.ps1
├─ docs
│  └─ development-plan.md
├─ pyproject.toml
├─ requirements.txt
└─ uv.lock
```

### 3.2 当前实现局限

当前版本已经基本进入目标玩法，但仍有一些结构工作要继续收敛：

1. 路由层仍集中在单个 `story.py` 中，后续可以继续拆分。
2. 会话当前仍是内存存储，服务重启后不会保留。
3. 本地裁定器仍然存在，主要用于 DeepSeek 不可用时 fallback。
4. Prompt 组装、模型调用和持久化层还可以进一步解耦。

## 4. 总体架构设计

### 4.1 当前架构

```text
React 前端
   │
   │ HTTP / JSON
   ▼
FastAPI 后端
   │
   ├─ 路由层（story.py）
   ├─ 数据模型层（schemas.py）
   └─ 剧情内容层（content.py，固定剧情图）
```

### 4.2 目标架构

```text
React 前端
   │
   │ HTTP / JSON
   ▼
FastAPI 后端
   │
   ├─ 路由层
   ├─ 会话状态层
   ├─ 历史背景种子层
   ├─ Prompt 组装层
   ├─ LLM 调用层
   └─ 推演结果归档层
```

### 4.3 目标玩法架构

方案一的核心不是“完整预设剧情树”，而是“开局提供历史背景种子，后续由玩家和 AI 共同推进”。

具体逻辑：

1. 系统给出一个历史事件背景。
2. 系统给出玩家身份、当前局势、目标和几个参考起手选项。
3. 玩家可以点击参考起手选项，也可以直接输入自己的开局决策。
4. 从第二回合开始，玩家主要通过自然语言描述行动。
5. AI 根据当前历史局势、玩家身份、既有行动记录和约束条件返回推演结果。

## 5. 后端路由架构

### 5.1 当前后端路由

当前后端主路由位于 `backend/app/routers/story.py`，统一挂载在 `/api` 前缀下。

| 方法 | 路径 | 作用 | 当前状态 |
|---|---|---|---|
| GET | `/` | 服务说明 | 已实现 |
| GET | `/api/health` | 健康检查与模型模式 | 已实现 |
| GET | `/api/scenarios` | 获取历史章节列表 | 已实现 |
| GET | `/api/scenarios/{scenario_id}` | 获取章节背景种子 | 已实现 |
| POST | `/api/sessions` | 创建会话 | 已实现 |
| GET | `/api/sessions/{session_id}` | 获取会话快照 | 已实现 |
| GET | `/api/sessions/{session_id}/history` | 获取回合历史 | 已实现 |
| POST | `/api/sessions/{session_id}/turns` | 提交自然语言行动并裁定 | 已实现 |

### 5.2 目标后端路由

方案一需要把“固定场景推进”改成“开局种子 + 自由输入推演”。

建议重构为：

```text
backend/app
├─ main.py
├─ routers
│  ├─ health.py
│  ├─ scenarios.py
│  ├─ sessions.py
│  └─ turns.py
├─ schemas
│  ├─ scenario.py
│  ├─ session.py
│  └─ turn.py
├─ services
│  ├─ scenario_service.py
│  ├─ session_service.py
│  ├─ prompt_service.py
│  └─ llm_service.py
└─ content
   └─ scenario_seeds.json
```

### 5.3 推荐路由设计

| 方法 | 路径 | 作用 | 阶段 |
|---|---|---|---|
| GET | `/api/health` | 健康检查 | 第一阶段 |
| GET | `/api/scenarios` | 获取历史章节列表 | 第一阶段 |
| GET | `/api/scenarios/{scenario_id}` | 获取某个章节的背景种子 | 第一阶段 |
| POST | `/api/sessions` | 创建会话并返回 `session_id` | 第二阶段 |
| GET | `/api/sessions/{session_id}` | 获取当前会话快照 | 第二阶段 |
| GET | `/api/sessions/{session_id}/history` | 获取回合历史 | 第二阶段 |
| POST | `/api/sessions/{session_id}/turns` | 提交玩家自然语言行动，生成 AI 推演结果 | 第二阶段 |
| POST | `/api/sessions/{session_id}/restart` | 重开当前历史章节 | 可选 |

### 5.4 推荐路由职责

- `scenarios.py`
  - 返回历史章节列表
  - 返回开局背景、身份、目标、参考起手选项
- `sessions.py`
  - 创建和查询会话
  - 维护当前局势摘要
- `turns.py`
  - 接收玩家自然语言输入
  - 调用 prompt 组装逻辑
  - 调用模型
  - 保存这一回合记录

## 6. API 数据类型设计

本节以方案一为准，数据类型围绕“历史背景种子、当前会话、玩家行动、AI 裁定结果”四个核心对象展开。

### 6.1 章节基础类型

#### `ScenarioCard`

用于历史章节列表。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `str` | 章节 ID |
| `title` | `str` | 标题 |
| `era` | `str` | 历史时期 |
| `summary` | `str` | 摘要 |

#### `OpeningOption`

用于开局参考选项。注意：它只是参考，不是强制分支。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `str` | 参考选项 ID |
| `label` | `str` | 选项标题 |
| `brief` | `str` | 选项说明 |
| `strategic_hint` | `str` | 该策略可能带来的方向性影响 |

#### `ScenarioSeed`

这是方案一的核心类型，取代原来的完整剧情图。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `str` | 章节 ID |
| `title` | `str` | 标题 |
| `era` | `str` | 历史时期 |
| `summary` | `str` | 背景摘要 |
| `player_role` | `str` | 玩家扮演身份 |
| `opening_situation` | `str` | 开局局势说明 |
| `historical_anchor` | `str` | 历史锚点 |
| `primary_goal` | `str` | 主目标 |
| `failure_risk` | `str` | 失败风险说明 |
| `initial_options` | `OpeningOption[]` | 开局参考选项 |

### 6.2 会话类型

#### `WorldSummary`

用于描述当前世界状态的简短摘要，不要求数值化，只要求稳定可读。

| 字段 | 类型 | 说明 |
|---|---|---|
| `time_label` | `str` | 当前时间阶段 |
| `location` | `str` | 当前主要地点 |
| `situation` | `str` | 当前局势摘要 |
| `pressure_points` | `list[str]` | 当前几个主要风险点 |
| `recent_shift` | `str` | 最近一轮造成的变化 |

#### `SessionState`

表示一局真实推演。

| 字段 | 类型 | 说明 |
|---|---|---|
| `session_id` | `str` | 会话 ID |
| `scenario_id` | `str` | 所属章节 |
| `status` | `"active" \| "ended"` | 当前状态 |
| `turn_index` | `int` | 当前第几回合 |
| `created_at` | `datetime` | 创建时间 |
| `updated_at` | `datetime` | 更新时间 |
| `world_summary` | `WorldSummary` | 当前局势摘要 |

#### `SessionSnapshot`

这是前端最常用的读取对象。

| 字段 | 类型 | 说明 |
|---|---|---|
| `session` | `SessionState` | 当前会话基础信息 |
| `scenario_seed` | `ScenarioSeed` | 当前章节背景种子 |
| `latest_narration` | `str` | 最近一轮 AI 叙事结果 |
| `next_prompt_hint` | `str` | 提示玩家下一步可以如何输入 |

### 6.3 回合类型

#### `PlayerTurnRequest`

玩家每回合提交一次自由文本行动。

| 字段 | 类型 | 说明 |
|---|---|---|
| `action_text` | `str` | 玩家本回合自然语言决策 |
| `source_option_id` | `str \| null` | 若来自参考起手选项则记录 ID，否则为空 |

示例：

```json
{
  "action_text": "我先派心腹去联络宫中宿卫，同时命人观察东宫的动静，不急于立刻摊牌。",
  "source_option_id": null
}
```

#### `TurnLog`

用于记录每一轮发生了什么。

| 字段 | 类型 | 说明 |
|---|---|---|
| `turn_index` | `int` | 第几回合 |
| `player_action` | `str` | 玩家原始输入 |
| `ai_narration` | `str` | AI 推演结果 |
| `outcome_summary` | `str` | 本轮结果摘要 |
| `world_update` | `str` | 局势如何变化 |
| `timestamp` | `datetime` | 回合时间 |

#### `TurnResult`

提交一轮行动后返回给前端的响应。

| 字段 | 类型 | 说明 |
|---|---|---|
| `session` | `SessionState` | 更新后的会话状态 |
| `turn` | `TurnLog` | 本轮完整记录 |
| `next_prompt_hint` | `str` | 下一轮输入提示 |
| `ending` | `str \| null` | 若进入结局，则返回结局描述 |

### 6.4 当前阶段与目标阶段的关系

当前代码已经进入方案一主线，核心接口模型已经切换为：

- `ScenarioSeed`
- `SessionState`
- `SessionSnapshot`
- `PlayerTurnRequest`
- `TurnResult`

后续剩余工作主要是把这些模型从“内存演示版”继续推进到“可持久化、可扩展的模型裁定版”。

## 7. 剧情数据结构设计

### 7.1 当前结构

当前 `backend/app/content.py` 已经不再保存完整剧情树，而是保存章节起点数据 `SCENARIO_SEEDS`。每个章节只定义：

1. 玩家身份
2. 开局局势
3. 历史锚点
4. 主目标与失败风险
5. 初始参考选项

回合推进不再依赖 `next_scene_id`，而是依赖：

1. `SessionState` 保存当前局势摘要
2. `TurnLog` 保存每轮玩家输入与 AI 裁定
3. `PlayerTurnRequest` 接收自由输入
4. `TurnResult` 返回新局势与下一轮提示

这个结构已经符合“开局结构化，后续自由推演”的目标。

### 7.2 新的目标结构：历史背景种子

方案一中，内容层不再保存完整分支树，而是保存“章节起点数据”。

推荐结构如下：

```json
{
  "id": "li_quan_red_turban",
  "title": "山东红袄：李全的扩张与归附",
  "era": "金末 宋金蒙角力时期",
  "summary": "你将扮演李全，在山东、淮海与南宋之间周旋，决定这支红袄军究竟是做乱世枭雄、地方军阀，还是借势而起的政治力量。",
  "player_role": "红袄军首领李全",
  "opening_situation": "金廷压榨日重，山东流民与溃兵持续汇集。李全的旗号已经打响，但真正的问题不是能不能拉起队伍，而是这支队伍今后靠什么活、对谁借势、又要不要把自己交给更大的政权。",
  "historical_anchor": "李全并不是单纯的流民军头领，他的处境始终夹在金、宋、蒙古与地方豪强之间。他的每一步都不只是打仗，更是结盟、投名、试探与反噬。",
  "primary_goal": "让李全与其部众在乱局中站稳脚跟，并为后续扩张争取最大主动权。",
  "failure_risk": "若扩张过快、归附过深或内部控制失衡，这支队伍很快就会在围剿、离心和外部利用中被撕裂。",
  "initial_options": [
    {
      "id": "secure_grain_routes",
      "label": "先夺粮道，再稳人心",
      "brief": "优先控制粮仓、河渡与集市，把最基本的军粮和流民秩序抓在手里。",
      "strategic_hint": "偏向先固根基，再图声势。"
    },
    {
      "id": "approach_southern_song",
      "label": "先向南宋递话",
      "brief": "尝试借南宋名义与贸易通道，为自己争取合法性和外部空间。",
      "strategic_hint": "偏向借势保身，但会带来身份和忠诚问题。"
    },
    {
      "id": "swallow_local_militias",
      "label": "先吞并地方武装",
      "brief": "优先拉拢盐枭、寨主与团练，让李全迅速做大兵力规模。",
      "strategic_hint": "偏向抢速度，但内部整合风险极高。"
    }
  ]
}
```

### 7.3 新结构的核心思想

新结构只有“起点”，没有完整后续树。

它提供的是：

1. 历史背景
2. 玩家身份
3. 开局局势
4. 历史锚点
5. 初始参考选项

它不提供的是：

1. 第二回合以后所有固定节点
2. 全部预设结局
3. 所有 `next_scene_id`

### 7.4 为什么这样更适合项目目标

这样设计后，系统会从“剧情播放器”变成“历史推演主持器”：

1. 玩家自由度更高。
2. 大模型真正参与每一轮推演。
3. 不需要手工写大量分支树。
4. 更符合“选择影响历史走向”的课程主题。

### 7.5 仍然需要保留的约束

虽然改成自由输入，但系统仍然要保留基础约束：

1. 每个章节必须有历史锚点。
2. 每个章节必须有玩家身份。
3. 每个章节必须有开局目标与失败风险。
4. 每个回合必须保留局势摘要，防止模型失忆。
5. 每一轮都要保存玩家原始输入和 AI 输出。

## 8. 前端架构设计

### 8.1 当前前端结构

当前前端主要逻辑都在 `frontend/src/App.jsx` 中，适合原型验证，但不适合自由输入推演。

当前功能包括：

1. 获取场景列表
2. 初始化场景
3. 点击预设选项推进剧情
4. 展示已选择的路径

### 8.2 目标前端结构

方案一的前端不再以“选项按钮列表”为核心，而是以“背景阅读 + 自由输入 + AI 返回结果”为核心。

建议拆分为：

```text
frontend/src
├─ api
│  ├─ client.js
│  ├─ scenarios.js
│  └─ sessions.js
├─ components
│  ├─ ScenarioCardList.jsx
│  ├─ ScenarioSeedPanel.jsx
│  ├─ SessionHeader.jsx
│  ├─ TurnTimeline.jsx
│  ├─ PlayerActionBox.jsx
│  └─ NarrationPanel.jsx
├─ pages
│  ├─ ScenarioSelectPage.jsx
│  └─ SessionPlayPage.jsx
├─ hooks
│  └─ useSessionPlay.js
├─ App.jsx
└─ main.jsx
```

### 8.3 推荐页面路由

| 路径 | 页面 | 作用 |
|---|---|---|
| `/` | 章节选择页 | 展示历史章节列表 |
| `/scenario/:scenarioId` | 开局页 | 展示背景、身份、目标、参考选项 |
| `/play/:sessionId` | 推演页 | 玩家输入行动，AI 返回结果 |

### 8.4 推演页的核心 UI

推演页建议包含：

1. 顶部状态栏：章节名、身份、当前回合、局势摘要
2. 中部叙事区：AI 最近返回的历史推演文本
3. 右侧或下方时间线：所有回合记录
4. 底部输入区：玩家输入决策文字
5. 开局阶段附加“参考起手选项”按钮

## 9. 前后端交互流程

### 9.1 当前流程

当前流程是：

1. 前端请求场景列表
2. 前端请求固定起始节点
3. 用户点击预设选项
4. 后端返回下一个固定节点

### 9.2 目标流程

方案一的目标流程如下：

#### 阶段一：选择章节

1. 前端请求 `GET /api/scenarios`
2. 用户点击某一历史章节
3. 前端请求 `GET /api/scenarios/{scenario_id}`
4. 后端返回 `ScenarioSeed`

#### 阶段二：创建会话

1. 用户点击“开始推演”
2. 前端请求 `POST /api/sessions`
3. 后端创建 `session_id`
4. 后端返回 `SessionSnapshot`
5. 前端进入 `/play/{session_id}`

#### 阶段三：提交第一轮行动

1. 用户可点击参考起手选项填充输入框，或自行输入文本
2. 前端请求 `POST /api/sessions/{session_id}/turns`
3. 请求体提交 `action_text`
4. 后端读取章节背景、当前局势、历史记录
5. 后端组装 prompt
6. 后端调用模型
7. 后端保存本轮 `TurnLog`
8. 后端返回 `TurnResult`

#### 阶段四：持续推演

1. 玩家继续输入自然语言决策
2. 后端每回合重复“读取状态 -> 调用模型 -> 更新摘要 -> 保存结果”
3. 直到后端判断进入结局，或用户主动结束

## 10. 大模型接入方案

### 10.1 模型在方案一中的职责

模型在方案一中不再只是“润色预设剧情”，而是承担每一轮的推演任务。

模型主要负责：

1. 根据玩家行动生成一轮历史结果
2. 描述局势变化
3. 输出下一轮可继续行动的局面
4. 在需要时生成结局判断

### 10.2 模型不应独占的部分

即使采用自由输入，以下部分仍建议由后端把控：

1. 章节背景与历史锚点
2. 会话上下文保存
3. 回合记录
4. 最大回合数或结束条件
5. 输出结构约束

### 10.3 推荐调用结构

```text
ScenarioSeed
  + SessionState
  + TurnHistory
  + PlayerAction
  ↓
Prompt Builder
  ↓
LLM API
  ↓
Structured Parse
  ↓
TurnResult
```

### 10.4 推荐 Prompt 组成

每轮 prompt 建议包括：

1. 章节标题与历史时期
2. 玩家身份
3. 开局背景摘要
4. 历史锚点
5. 当前局势摘要
6. 最近几轮关键行动
7. 玩家本轮输入
8. 输出格式要求

### 10.5 推荐模型输出结构

建议要求模型输出结构化 JSON，至少包含：

```json
{
  "ai_narration": "......",
  "outcome_summary": "......",
  "world_update": "......",
  "next_prompt_hint": "......",
  "ending": null
}
```

这样做的原因：

1. 前端渲染稳定
2. 便于保存历史记录
3. 降低模型自由发挥导致的解析失败

## 11. 数据持久化规划

### 11.1 推荐持久化对象

| 对象 | 是否建议持久化 | 原因 |
|---|---|---|
| `ScenarioSeed` | 是 | 历史章节会逐渐变多 |
| `SessionState` | 是 | 刷新页面后应能恢复 |
| `TurnLog` | 是 | 需要回放和答辩展示 |
| 模型原始输出 | 可选 | 便于调试和复盘 |

### 11.2 推荐演进路径

1. 第一阶段：继续使用内存结构
2. 第二阶段：把章节种子迁移到 JSON 文件
3. 第三阶段：把会话和回合记录落到 SQLite
4. 第四阶段：如有需要再迁移到 PostgreSQL

### 11.3 为什么暂时不急着上数据库

课程大作业首先要保证玩法跑通。对当前项目来说，最重要的是先让：

1. 开局背景种子稳定
2. 玩家自由输入稳定
3. AI 返回结构稳定

数据库是第二阶段的增强，而不是第一阶段的前提。

## 12. 开发阶段计划

### 12.1 第一阶段：结构切换

目标：从“固定分支树”切换到“背景种子 + 自由输入”。

任务：

1. 把 `content.py` 从完整场景图改成 `ScenarioSeed`
2. 删除对 `next_scene_id` 的强依赖
3. 重新设计 `schemas.py`
4. 在文档中明确新的 API 契约

交付标准：

- 每个章节能返回背景、身份、目标和参考起手选项
- 不再要求后续剧情必须预先写完

### 12.2 第二阶段：真实会话版

目标：让每一局推演都有自己的状态和历史。

任务：

1. 新增 `session_id`
2. 增加会话查询接口
3. 增加回合历史接口
4. 维护 `world_summary`

交付标准：

- 每个会话都能持续推进
- 玩家刷新后可恢复当前局势

### 12.3 第三阶段：模型接入版

目标：由 AI 承担每轮推演生成。

任务：

1. 增加模型配置
2. 新增 `llm_service.py`
3. 设计结构化 prompt
4. 约束模型输出 JSON
5. 保存回合日志

交付标准：

- 玩家每次输入一句话，都能得到一轮新的历史推演结果
- 返回结构稳定，可直接给前端渲染

### 12.4 第四阶段：展示优化版

目标：提升课程展示效果。

任务：

1. 加入章节介绍页
2. 加入回合时间线视图
3. 加入“你的策略路径”总结页
4. 加入“真实历史对照”模块
5. 加入一键重开和导出本局记录功能

交付标准：

- 页面适合答辩展示
- AI 推演逻辑清楚可讲

## 13. 测试计划

### 13.1 后端测试

建议增加：

1. 获取章节列表测试
2. 获取章节背景种子测试
3. 创建会话测试
4. 获取会话快照测试
5. 提交自然语言行动测试
6. 模型输出结构校验测试
7. 历史记录保存测试

### 13.2 前端测试

建议增加：

1. 章节选择页加载测试
2. 开局页渲染测试
3. 自然语言输入提交流程测试
4. AI 返回结果渲染测试
5. 回合历史显示测试
6. 错误态和加载态测试

## 14. 风险与注意事项

### 14.1 历史准确性风险

自由输入后，模型更容易偏离历史背景。因此必须保留：

1. 历史锚点
2. 玩家身份约束
3. 局势摘要
4. 输出结构要求

### 14.2 模型失控风险

方案一最容易出现的问题是模型越写越散。解决办法：

1. 每轮只提供必要上下文
2. 保留 `world_summary`
3. 要求输出简洁且结构化
4. 必要时限制最大回合数

### 14.3 演示稳定性风险

答辩时不能把一切押在模型质量上。因此建议保留降级方案：

1. 若模型调用失败，返回“系统裁定失败，请重试”
2. 保留最少量的本地 fallback 文本
3. 至少保证章节选择、开局展示、会话创建能正常工作

## 15. 建议近期实施顺序

建议你接下来按这个顺序推进：

1. 修复当前项目中的中文乱码
2. 把 `content.py` 改成 `ScenarioSeed` 结构
3. 重新设计后端 `schemas.py`
4. 新增 `sessions` 和 `turns` 路由
5. 改前端为“自由输入 + AI 返回”的页面结构
6. 最后接入模型 API

## 16. 总结

方案一的本质是把项目从“固定剧情分支系统”转成“AI 主持的历史推演系统”。

新的核心不再是：

- `scene`
- `choice`
- `next_scene_id`

而是：

- `ScenarioSeed`
- `SessionState`
- `TurnLog`
- `PlayerTurnRequest`
- `TurnResult`

这样设计以后，项目会更符合你的原始目标：

1. 开局有明确历史背景
2. 玩家不只是点按钮，而是真正写出自己的策略
3. AI 根据玩家决策继续推演历史
4. 项目既有课程展示效果，也有继续扩展的空间
