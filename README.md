# 智能旅行助手 (HelloAgents Trip Planner)

基于 **LangChain 多智能体架构**的 AI 旅行规划应用。用户只需输入目的地和偏好，4 个专门化 Agent 自动协作，调用高德地图 API 获取真实数据，由 LLM 整合生成包含景点、天气、酒店、餐饮和预算的完整旅行计划。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangChain-0.3+-orange?logo=langchain" alt="LangChain">
  <img src="https://img.shields.io/badge/Vue-3.5+-brightgreen?logo=vue.js" alt="Vue 3">
  <img src="https://img.shields.io/badge/TypeScript-5.6-blue?logo=typescript" alt="TypeScript">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 📑 目录

- [项目架构](#项目架构)
- [核心特性](#核心特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [用户输入说明](#用户输入说明)
- [API 接口](#api-接口)
- [项目亮点](#项目亮点)
- [常见问题](#常见问题)
- [开发指南](#开发指南)

---

## 项目架构

```
helloagents-trip-planner/
├── backend/                          # Python 后端 (FastAPI + LangChain)
│   ├── app/
│   │   ├── agents/                   # 🤖 多智能体核心
│   │   │   ├── trip_planner.py       #     Agent 编排器（4 个 Agent 协作）
│   │   │   └── prompts.py            #     各 Agent 的系统提示词
│   │   ├── api/                      # 🌐 API 层
│   │   │   ├── main.py               #     FastAPI 应用入口，CORS 配置
│   │   │   └── routes/
│   │   │       └── trip.py           #     旅行规划路由 (POST /api/trip/plan)
│   │   ├── models/                   # 📦 数据模型
│   │   │   └── schemas.py            #     Pydantic 请求/响应模型（含校验器）
│   │   ├── services/                 # 🔌 外部服务封装
│   │   │   ├── amap_service.py       #     高德地图 API（POI 搜索 + 天气查询）
│   │   │   └── unsplash_service.py   #     Unsplash 图片服务（景点配图）
│   │   └── config.py                 # ⚙️ 应用配置（pydantic-settings 加载 .env）
│   ├── .env                          # 🔑 环境变量（不入库，需自行创建）
│   ├── requirements.txt              # Python 依赖清单
│   └── run.py                        # 🚀 启动脚本（uvicorn + hot-reload）
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue              # 首页（旅行需求表单，含所有输入项）
│   │   │   └── Result.vue            # 结果页（行程展示 + 高德地图 + 导出 + 编辑）
│   │   ├── services/
│   │   │   └── api.ts                # Axios API 封装（类型安全的请求层）
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript 类型定义（与后端 Pydantic 对齐）
│   │   ├── router/
│   │   │   └── index.ts              # Vue Router 路由配置
│   │   ├── App.vue                   # 根组件
│   │   └── main.ts                   # 应用入口（注册 Ant Design Vue + Router）
│   ├── vite.config.ts                # Vite 配置（含 /api → localhost:8000 代理）
│   └── package.json                  # Node 依赖 & 脚本
├── .env.example                      # 环境变量模板（可提交到 Git）
└── .gitignore                        # Git 忽略规则
```

---

## 核心特性

### 🤖 多智能体协作

项目采用 **4 个专门化 Agent** 协同工作的架构，基于 LangChain 的 **Tool Calling** 机制实现。每个 Agent 有独立的系统提示词，由 `TripPlannerAgent` 编排器统一调度：

| Agent | 职责 | 工具 | 模型温度 |
|-------|------|------|----------|
| **AttractionSearchAgent** | 景点搜索 | `search_attractions`（高德 POI 搜索） | 0.2 |
| **WeatherQueryAgent** | 天气查询 | `query_weather`（高德天气 API） | 0.2 |
| **HotelAgent** | 酒店推荐 | `search_hotels`（高德 POI 搜索） | 0.2 |
| **PlannerAgent** | 行程整合规划 | 无（纯 LLM 推理，结构化 JSON 输出） | 0.7 |

**工作流程：**

```
用户输入 → AttractionSearchAgent → WeatherQueryAgent → HotelAgent
                ↓                        ↓                  ↓
           景点数据（JSON）         天气数据（JSON）      酒店数据（JSON）
                ↓                        ↓                  ↓
                └────────────────────────┼──────────────────┘
                                         ↓
                                  PlannerAgent（LLM 推理整合）
                                         ↓
                                  TripPlan（Pydantic 模型）
                                         ↓
                              → 景点图片补充（Unsplash）
                                         ↓
                              返回前端完整旅行计划
```

**设计亮点：**
- 🔀 前 3 个 Agent 使用 **低温度 (0.2)** 确保工具调用的准确性和数据可靠性
- 🎨 PlannerAgent 使用 **高温度 (0.7)** 激发 LLM 创造力，生成更丰富的行程描述
- 🛡️ 最多 **3 轮**工具调用循环，防止无限对话
- 📐 输出经过 **Pydantic 严格校验**，确保前后端数据一致性

### 🗺️ 高德地图集成

通过 [高德地图 Web 服务 API](https://lbs.amap.com/api/webservice/summary) 提供真实的地理数据：

| 功能 | API | 说明 |
|------|-----|------|
| **POI 搜索** | `text_search` | 按关键词搜索景点/酒店，返回名称、地址、经纬度、评分 |
| **天气查询** | `weather_info` | 获取城市未来天气预报（温度、天气状况、风力风向） |
| **地图展示** | JS API 2.0 | 前端通过 `@amap/amap-jsapi-loader` 加载，在地图上标记所有景点 |

### 🖼️ Unsplash 图片服务

自动为每个景点搜索配图，提升行程展示效果：
- 优先使用 **"景点名称 + 城市名"** 搜索
- 失败后自动回退到 **"城市名 + 旅游"** 通用关键词
- 图片获取失败**不影响主流程**，仅记录警告日志

### 📋 完整的行程展示

结果页 (`Result.vue`) 提供结构化、可交互的行程展示：

| 板块 | 内容 |
|------|------|
| 📋 行程概览 | 目的地、日期、天数、景点总数 |
| 💰 预算明细 | 门票 / 酒店 / 餐饮 / 交通分项 + 总计 |
| 🗺️ 景点地图 | 高德地图标注所有景点位置（含信息窗） |
| 📅 每日行程 | 景点详情、餐饮安排、住宿信息（可编辑） |
| 🌤️ 天气信息 | 每日天气、温度、风力（表格展示） |
| 💡 旅行建议 | LLM 生成的实用旅行贴士 |

### 📥 行程导出 & 编辑

- **PNG 导出**：基于 `html2canvas` 将行程区域渲染为高清截图
- **PDF 导出**：基于 `jsPDF` 将行程内容转为可打印的 PDF 文档
- **在线编辑**：支持在结果页直接编辑每日行程描述，无需重新生成

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | ≥0.115.0 | 高性能异步 Web 框架，自动生成 OpenAPI 文档 |
| [LangChain](https://www.langchain.com/) | ≥0.3.0 | LLM 编排框架，Agent + Tool Calling |
| [LangChain OpenAI](https://python.langchain.com/docs/integrations/llms/openai/) | ≥0.3.0 | OpenAI 兼容模型接入（支持 DeepSeek 等） |
| [Pydantic](https://docs.pydantic.dev/) | ≥2.0.0 | 数据校验与序列化，含自定义校验器 |
| [Pydantic-Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | ≥2.0.0 | 环境变量加载与管理 |
| [httpx](https://www.python-httpx.org/) | ≥0.27.0 | 异步 HTTP 客户端（调用高德/Unsplash API） |
| [Uvicorn](https://www.uvicorn.org/) | ≥0.34.0 | ASGI 服务器，支持 hot-reload |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| [Vue 3](https://vuejs.org/) | ^3.5.13 | 渐进式前端框架（Composition API） |
| [TypeScript](https://www.typescriptlang.org/) | ~5.6.3 | 类型安全，与后端 Pydantic 模型对齐 |
| [Ant Design Vue](https://antdv.com/) | ^4.2.6 | 企业级 UI 组件库 |
| [Vue Router](https://router.vuejs.org/) | ^4.5.0 | SPA 路由管理 |
| [Vite](https://vitejs.dev/) | ^6.0.5 | 极速构建工具，HMR 热更新 |
| [Axios](https://axios-http.com/) | ^1.7.9 | HTTP 请求封装，类型安全 |
| [高德 JSAPI Loader](https://lbs.amap.com/api/jsapi-v2/guide/abc/load) | ^1.0.1 | 高德地图 JS API 2.0 加载器 |
| [html2canvas](https://html2canvas.hertzen.com/) | ^1.4.1 | 页面区域截图（PNG 导出） |
| [jsPDF](https://github.com/parallax/jsPDF) | ^2.5.2 | PDF 文档生成 |
| [dayjs](https://day.js.org/) | ^1.11.13 | 轻量级日期处理库 |

---

## 快速开始

### 前置条件

| 依赖 | 版本/说明 | 获取方式 |
|------|-----------|----------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ (LTS 推荐) | [nodejs.org](https://nodejs.org/) |
| **LLM API Key** | 支持 OpenAI / DeepSeek 等兼容接口 | [OpenAI](https://platform.openai.com/) / [DeepSeek](https://platform.deepseek.com/) |
| **高德地图 Key** | Web 服务 API Key | [高德开放平台](https://console.amap.com/) |
| **Unsplash Key** | Access Key（可选，用于景点配图） | [Unsplash Developers](https://unsplash.com/developers) |

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example backend/.env
```

编辑 `backend/.env`，填入你的 API Key：

```env
# ── LLM API 配置 ──
# 支持 OpenAI、DeepSeek、通义千问等兼容接口
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# ── 高德地图 Web 服务 Key ──
# 申请地址：https://console.amap.com/
AMAP_API_KEY=your_amap_api_key_here

# ── Unsplash Access Key（可选）──
# 申请地址：https://unsplash.com/developers
# 不填则跳过图片获取
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
```

> 💡 **使用 DeepSeek 示例：**
> ```env
> LLM_API_KEY=sk-your-deepseek-key
> LLM_BASE_URL=https://api.deepseek.com/v1
> LLM_MODEL=deepseek-chat
> ```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（自带 hot-reload）
python run.py
```

后端服务运行在 `http://localhost:8000`，可访问：
- API 文档（Swagger UI）：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`，Vite 自动将 `/api` 请求代理到后端 `http://localhost:8000`。

### 4. 使用

1. 打开浏览器访问 `http://localhost:5173`
2. 填写目的地城市、日期、偏好等信息
3. 点击「生成旅行计划」
4. 等待约 30-60 秒（取决于 LLM 响应速度）
5. 查看完整行程，支持编辑和导出

---

## 用户输入说明

首页表单支持以下选项，灵活组合可生成高度个性化的旅行计划：

| 字段 | 可选值 | 说明 |
|------|--------|------|
| **目的地城市** | 任意中国城市名 | 如：北京、上海、杭州、成都、大理… |
| **旅行天数** | 1 ~ 14 天 | 天数越长，生成时间越久 |
| **旅行偏好** | 🏛️ 历史文化 / 🏔️ 自然风光 / 🍜 美食探索 / 🛍️ 休闲购物 / 👨‍👩‍👧 亲子游乐 / 🎯 综合体验 | 决定景点搜索关键词和行程风格 |
| **预算范围** | 💡 经济实惠 / 💰 中等 / 👑 豪华旅行 | 影响酒店、餐饮推荐档次 |
| **交通方式** | 🚇 公共交通 / 🚗 自驾 / 🚕 出租车·网约车 / 🚗+🚇 混合 | 影响每日交通安排建议 |
| **住宿类型** | 🏨 经济型酒店 / 🏩 舒适型酒店 / 🏰 豪华酒店 / 🏡 民宿 | 决定酒店搜索关键词 |

---

## API 接口

### `POST /api/trip/plan` — 生成旅行计划

**请求体：**

```json
{
  "city": "北京",
  "start_date": "2025-07-01",
  "end_date": "2025-07-03",
  "days": 3,
  "preferences": "历史文化",
  "budget": "中等",
  "transportation": "公共交通",
  "accommodation": "经济型酒店"
}
```

**响应体（TripPlan 结构）：**

```json
{
  "city": "北京",
  "start_date": "2025-07-01",
  "end_date": "2025-07-03",
  "days": [
    {
      "date": "2025-07-01",
      "day_index": 0,
      "description": "上午抵达北京，前往天安门广场...",
      "transportation": "地铁 + 步行",
      "accommodation": "汉庭酒店（前门店）",
      "hotel": {
        "name": "汉庭酒店（前门店）",
        "address": "北京市东城区...",
        "location": { "longitude": 116.40, "latitude": 39.90 },
        "price_range": "200-400元",
        "rating": "4.5",
        "estimated_cost": 300
      },
      "attractions": [
        {
          "name": "故宫博物院",
          "address": "北京市东城区景山前街4号",
          "location": { "longitude": 116.397, "latitude": 39.918 },
          "visit_duration": 180,
          "description": "中国明清两代的皇家宫殿...",
          "rating": 4.8,
          "image_url": "https://images.unsplash.com/...",
          "ticket_price": 60
        }
      ],
      "meals": [
        {
          "type": "lunch",
          "name": "全聚德烤鸭店（前门店）",
          "estimated_cost": 150
        }
      ]
    }
  ],
  "budget": {
    "total_attractions": 180,
    "total_hotels": 900,
    "total_meals": 450,
    "total_transportation": 200,
    "total": 1730
  },
  "weather_info": [
    {
      "date": "2025-07-01",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 32,
      "night_temp": 22,
      "wind_direction": "南",
      "wind_power": "≤3级"
    }
  ]
}
```

> 📖 完整的 API 文档（含 Schema 说明）请访问 Swagger UI：`http://localhost:8000/docs`

### `GET /` — 根路径

```json
{ "message": "智能旅行助手 API", "docs": "/docs" }
```

### `GET /health` — 健康检查

```json
{ "status": "ok" }
```

---

## 项目亮点

### 🏗️ 架构设计

- **关注点分离**：后端分 `agents` / `api` / `models` / `services` 四层，职责清晰
- **单例模式**：Agent 实例和服务实例全局复用，避免重复初始化 LLM 连接
- **前后端类型对齐**：Pydantic 模型 ↔ TypeScript 接口，数据结构完全一致
- **非侵入式图片获取**：Unsplash 图片在行程生成后异步补充，失败不影响主流程

### 🔧 工程实践

- **环境变量管理**：`.env.example` 提供模板，`.env` 不入库，敏感信息不泄露
- **CORS 配置**：后端仅允许前端开发服务器跨域，生产环境需调整
- **Vite 代理**：开发时前端自动代理 API 请求，无需手动配置 CORS 或完整 URL
- **Hot Reload**：前后端均支持热重载，开发体验流畅

### 🤖 LLM 使用技巧

- **温度分层**：工具调用 Agent 低温度保准确性，创意规划 Agent 高温度增多样性
- **结构化输出**：PlannerAgent 被要求输出严格 JSON，配合 Pydantic 校验确保可用性
- **工具描述即文档**：LangChain `@tool` 装饰器的 docstring 直接被 LLM 理解，无需额外配置
- **多轮工具调用**：Agent 可在单次对话中多次调用工具，逐步获取所需数据

---

## 常见问题

### Q1: 前端页面打开后，点击生成一直转圈？

**可能原因：**
1. 后端未启动 —— 确认终端中 `python run.py` 正在运行
2. LLM API Key 无效 —— 检查 `backend/.env` 中的 Key 是否正确
3. 高德地图 Key 无效或未配置 —— 检查 `AMAP_API_KEY`
4. LLM 接口超时 —— 网络问题或模型响应慢，可尝试切换模型

### Q2: 生成的行程中景点信息不准确？

高德地图 POI 搜索返回的是真实地理位置数据，但 PlannerAgent（LLM）在整合时可能会对景点描述、游览时间等进行推理补充。如果偏差较大，可以：
- 在提示词 `prompts.py` 中增加更明确的约束
- 更换更强的 LLM 模型（如 `gpt-4o` → `gpt-4-turbo`）

### Q3: 为什么景点没有图片？

Unsplash 图片服务是可选的。确认：
1. `UNSPLASH_ACCESS_KEY` 已正确配置在 `backend/.env` 中
2. Unsplash API 额度未用完（免费版每小时 50 次请求）
3. 查看后端日志，确认是否有 `未能获取图片` 的警告

### Q4: 如何更换 LLM 模型？

编辑 `backend/.env` 中的 `LLM_MODEL` 和 `LLM_BASE_URL` 即可。常用配置：

```env
# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 通义千问（通过兼容接口）
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

### Q5: 生成旅行计划需要多长时间？

取决于 LLM 模型和旅行天数：
- **3 天行程**：约 30-60 秒
- **7 天行程**：约 60-120 秒
- **更长时间**：LLM 输出 token 更多，时间相应增加

### Q6: 部署到生产环境需要注意什么？

1. 修改 `backend/app/api/main.py` 中的 CORS `allow_origins` 为实际域名
2. 前端 `vite.config.ts` 中的代理仅用于开发，生产环境需用 Nginx 反向代理
3. 关闭后端的 `reload=True`
4. 使用 `npm run build` 构建前端静态文件，用 Nginx 托管
5. 考虑使用 Docker 容器化部署

---

## 开发指南

### 项目脚本

```bash
# ── 后端 ──
cd backend
python run.py              # 启动开发服务器（hot-reload）
pip install -r requirements.txt  # 安装依赖

# ── 前端 ──
cd frontend
npm run dev                # 启动开发服务器（HMR）
npm run build              # 生产构建
npm run preview            # 预览生产构建
```

### 添加新的 Agent

1. 在 `backend/app/agents/prompts.py` 中添加新 Agent 的系统提示词
2. 在 `backend/app/agents/trip_planner.py` 的 `_make_amap_tools()` 中添加新工具（如需要）
3. 在 `TripPlannerAgent.plan_trip()` 中添加调用步骤
4. 更新 `schemas.py` 中的 Pydantic 模型（如需要）

### 代码规范

- **Python**：遵循 PEP 8，使用 type hints
- **TypeScript**：使用 strict mode，类型与后端 Pydantic 模型对齐
- **提交信息**：建议使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范

---

<p align="center">
  <sub>Built with ❤️ using LangChain · FastAPI · Vue 3 · 高德地图</sub>
</p>
