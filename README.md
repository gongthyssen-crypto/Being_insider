# AI Chinese History Sandbox

一个用于“人工智能导论”课程大作业的前后端分离项目骨架：

- `backend/`: FastAPI API，负责历史章节、会话状态和模型裁定接入点
- `frontend/`: React + Vite 界面，负责历史剧情交互
- `scripts/`: Windows PowerShell 启停脚本

默认端口：

- 前端: `18422`
- 后端: `18421`

## 快速开始

1. 运行 `.\scripts\setup.ps1`
2. 运行 `.\scripts\start-all.ps1`
3. 打开 `http://127.0.0.1:18422`
4. 停止服务时运行 `.\scripts\stop-all.ps1`

## 当前历史章节

- `山东红袄：李全的扩张与归附`
- `万历新政前夜：张居正的第一盘棋`
- `朝鲜风云：袁世凯与甲午前夜`

## 模型 API 接入位置

后端当前已经切到“背景种子 + 会话状态 + 自由输入回合”的结构，接模型时主要扩展以下位置：

- `backend/app/routers/story.py`
- `backend/app/content.py`
- `backend/app/deepseek_service.py`

可以把章节背景、历史锚点、当前局势摘要、回合历史和用户自然语言行动拼成 prompt，再请求外部模型 API 生成下一段剧情。

## DeepSeek 配置

当前后端已经接入 DeepSeek 官方 `chat/completions` 接口，配置位于：

- `backend/app/deepseek_service.py`

默认会先读取环境变量：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`

如果没有配置真实 `DEEPSEEK_API_KEY`，系统会自动回退到本地裁定器，方便继续开发前端和流程。

前端界面会明确显示：

- 当前服务配置使用的是 DeepSeek 官方模型还是本地 fallback
- 每一回合实际采用的是 DeepSeek 官方模型还是本地 fallback
