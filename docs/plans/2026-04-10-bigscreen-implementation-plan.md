# 重大项目全景监控看板 - 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个完整的 PC + 移动端双屏监控看板系统，包含 Vue3 前端 + FastAPI 后端，支持实时数据推送

**Architecture:** 
- 前端：Vue3 + Vite + Pinia + ECharts，实现 PC 大屏（1440px）和手机看板（390px）
- 后端：FastAPI + WebSocket，支持实时推送和定时刷新
- 设计稿：bigscreen.pen 中的 5 个页面（PC 看板 + 4 个移动页面）

**Tech Stack:** 
- Frontend: Vue3 3.4+, Vite 5.x, Pinia, ECharts 5.x, Vue Router 4.x
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.x, WebSocket (websockets)
- Deployment: Docker + Nginx

---

## 阶段一：项目初始化

### Task 1: 创建项目结构

**Step 1: 创建前端项目**

```bash
# 使用 npm create vue@latest 创建项目
cd E:\workspace_monitor
npm create vue@latest frontend -- --typescript --router --pinia
cd frontend
npm install
npm install echarts vue-echarts @vueuse/core dayjs
```

**Step 2: 创建后端项目**

```bash
cd E:\workspace_monitor
mkdir backend
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
# source venv/bin/activate
pip install fastapi uvicorn sqlalchemy websockets pydantic python-multipart
```

**Step 3: 验证空项目运行**

```bash
# Frontend
cd frontend && npm run dev
# 预期：http://localhost:5173 可访问

# Backend
uvicorn main:app --reload --port 8000
# 预期：http://localhost:8000/docs 可访问
```

---

## 阶段二：后端 API 开发

### Task 2: 数据模型和基础 API

**Files:**
- Create: `backend/app/models.py` - SQLAlchemy 数据模型
- Create: `backend/app/schemas.py` - Pydantic 响应模型
- Create: `backend/app/database.py` - 数据库配置
- Create: `backend/app/routes/projects.py` - 项目 CRUD API
- Create: `backend/app/main.py` - FastAPI 主应用

**Step 1: 创建数据模型**

```python
# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner = Column(String(50))
    department = Column(String(50))
    progress = Column(Float, default=0.0)  # 0-100
    achievement_rate = Column(Float, default=0.0)  # 目标达成率
    score = Column(Float, default=0.0)  # 考核得分
    status = Column(String(20), default="healthy")  # healthy/warning/risk
    target_date = Column(Date)
    created_at = Column(Date)
```

**Step 2: 创建项目路由**

```python
# backend/app/routes/projects.py
@router.get("/")
async def list_projects():
    return db.query(Project).all()

@router.get("/stats")
async def get_stats():
    # 返回 KPI 统计数据
    pass
```

**Step 3: 启动并测试**

```bash
curl http://localhost:8000/api/projects
# 预期：返回空数组 []
```

### Task 3: WebSocket 实时推送

**Files:**
- Create: `backend/app/websocket.py` - WebSocket 连接管理
- Modify: `backend/app/main.py` - 集成 WebSocket

**Step 1: 创建 WebSocket 管理器**

```python
# backend/app/websocket.py
from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)
```

**Step 2: 集成到主应用**

```python
# backend/app/main.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket)
```

---

## 阶段三：前端 PC 看板开发

### Task 4: 基础框架搭建

**Step 1: 配置路由**

```typescript
// frontend/src/router/index.ts
const routes = [
  { path: '/', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/project/:id', name: 'ProjectDetail', component: () => import('@/views/ProjectDetail.vue') },
]
```

**Step 2: 创建布局组件**

```vue
<!-- frontend/src/views/Dashboard.vue -->
<template>
  <div class="dashboard">
    <KpiCards :data="kpiData" />
    <ChartsSection :projects="projects" />
    <ProjectTable :projects="projects" />
    <AiInsights :insights="insights" />
  </div>
</template>
```

### Task 5: PC 看板核心组件

**Files:**
- Create: `frontend/src/components/KpiCard.vue` - KPI 卡片组件
- Create: `frontend/src/components/ProjectProgressChart.vue` - 进度对比图
- Create: `frontend/src/components/QuadrantChart.vue` - 四象限分析图
- Create: `frontend/src/components/AchievementChart.vue` - 目标达成率图
- Create: `frontend/src/components/ScoreRadar.vue` - 考核得分图
- Create: `frontend/src/components/ProjectTable.vue` - 项目明细表格
- Create: `frontend/src/components/AiInsights.vue` - 智能洞察面板

**Step 1: KPI 卡片组件**

```vue
<!-- frontend/src/components/KpiCard.vue -->
<template>
  <div class="kpi-card" :class="type">
    <div class="kpi-header">
      <span class="kpi-label">{{ label }}</span>
      <div class="kpi-icon">
        <slot name="icon"></slot>
      </div>
    </div>
    <div class="kpi-value">{{ value }}</div>
    <div class="kpi-trend" :class="trendType">
      <span>{{ trend }}</span>
    </div>
  </div>
</template>
```

**Step 2: 进度对比图（条形图）**

```vue
<!-- frontend/src/components/ProjectProgressChart.vue -->
<script setup>
import * as echarts from 'echarts'
// 按 PRD 设计：X轴=项目名，Y轴=进度%，颜色<50%红/50-75%橙/>=75%蓝
</script>
```

**Step 3: 四象限散点图**

```vue
<!-- frontend/src/components/QuadrantChart.vue -->
<script setup>
// 气泡图：X=进度，Y=达成率，大小=考核分
// 四象限标注：优秀/执行滞后/严重风险/虚假繁荣
</script>
```

---

## 阶段四：前端移动端开发

### Task 6: 移动端主看板

**Files:**
- Create: `frontend/src/views/mobile/Dashboard.vue` - 移动端首页
- Create: `frontend/src/views/mobile/ProjectDetail.vue` - 专项详情
- Create: `frontend/src/views/mobile/Alerts.vue` - 预警中心
- Create: `frontend/src/views/mobile/Analysis.vue` - 智能分析

**Step 1: 移动端框架**

```vue
<!-- frontend/src/views/mobile/Dashboard.vue -->
<template>
  <div class="mobile-dashboard">
    <header>项目全景看板</header>
    <KpiRow :data="stats" />
    <ProjectList :projects="projects" />
    <BottomNav />
  </div>
</template>
```

**Step 2: 底部导航栏**

```vue
<!-- frontend/src/components/mobile/BottomNav.vue -->
<template>
  <nav class="bottom-nav">
    <router-link to="/mobile">总览</router-link>
    <router-link to="/mobile/projects">专项</router-link>
    <router-link to="/mobile/analysis">分析</router-link>
    <router-link to="/mobile/alerts">预警</router-link>
  </nav>
</template>
```

### Task 7: 移动端二级页面

**Files:**
- Create: `frontend/src/views/mobile/ProjectList.vue` - 14 个专项列表
- Create: `frontend/src/views/mobile/ProjectDetail.vue` - 详情页含 Tab（进度/里程碑/考核/建议）
- Create: `frontend/src/views/mobile/WarningList.vue` - 预警列表
- Create: `frontend/src/views/mobile/AiAnalysis.vue` - AI 洞察页

---

## 阶段五：前后端集成

### Task 8: API 对接

**Step 1: 创建 API 服务**

```typescript
// frontend/src/api/index.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
})

export const getProjects = () => api.get('/api/projects')
export const getStats = () => api.get('/api/stats')
export const getInsights = () => api.get('/api/insights')
```

**Step 2: WebSocket 连接**

```typescript
// frontend/src/composables/useWebSocket.ts
import { ref, onMounted } from 'vue'

export function useWebSocket(url: string) {
  const data = ref(null)
  const ws = new WebSocket(url)
  
  ws.onmessage = (event) => {
    data.value = JSON.parse(event.data)
  }
  
  return { data }
}
```

---

## 阶段六：Docker 部署配置

### Task 9: 部署文件

**Files:**
- Create: `Dockerfile` - 前端构建
- Create: `backend/Dockerfile` - 后端构建
- Create: `docker-compose.yml` - 编排文件
- Create: `nginx.conf` - Nginx 配置

**Step 1: 前端 Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Step 2: 后端 Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]
```

**Step 3: docker-compose.yml**

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
```

---

## 开发顺序总结

```
Phase 1: 项目初始化
  Task 1: 创建前后端项目结构 ✓

Phase 2: 后端开发
  Task 2: 数据模型和基础 API
  Task 3: WebSocket 实时推送

Phase 3: PC 看板
  Task 4: 基础框架
  Task 5: 核心组件

Phase 4: 移动端
  Task 6: 移动端主看板
  Task 7: 移动端二级页面

Phase 5: 集成
  Task 8: 前后端 API 对接

Phase 6: 部署
  Task 9: Docker 配置
```

---

## 关键设计参数（来自 bigscreen.pen）

**颜色变量：**
```css
--bg-primary: #0F1623
--bg-secondary: #1A2332
--bg-card: #1E2A3A
--accent-blue: #3B82F6
--accent-green: #10B981
--accent-orange: #F59E0B
--accent-red: #EF4444
--accent-purple: #8B5CF6
--text-primary: #F1F5F9
--text-secondary: #94A3B8
```

**页面尺寸：**
- PC 看板：1440 × 1638px
- 手机：390 × 2198px（主）/ 1380px（详情）/ 1343px（预警）/ 1825px（分析）

**14 个专项数据：**
| 专项 | 进度 | 达成率 | 考核分 | 状态 |
|------|------|--------|--------|------|
| MTPF提升 | 78% | 76% | 76 | 需关注 |
| "8H"部署 | 85% | 88% | 88 | 健康 |
| 数字中台 | 62% | 65% | 65 | 需关注 |
| 质量提升 | 91% | 92% | 92 | 健康 |
| 渠道管理 | 55% | 62% | 62 | 需关注 |
| Marketing | 43% | 55% | 55 | 高风险 |
| 政府资金 | 70% | 72% | 72 | 健康 |
| 消��降本 | 48% | 54% | 54 | 高风险 |
| 生产成本 | 66% | 68% | 68 | 需关注 |
| 库存周转 | 82% | 84% | 84 | 健康 |
| 预算现金流 | 74% | 76% | 76 | 健康 |
| 财务核算 | 89% | 90% | 90 | 健康 |
| 万元人力 | 58% | 61% | 61 | 需关注 |
| 人力费用 | 71% | 73% | 73 | 健康 |

---

## 运行命令

**开发模式：**
```bash
# 前端
cd frontend && npm run dev

# 后端
cd backend && uvicorn app:app --reload
```

**生产构建：**
```bash
# 前后端构建
docker-compose build

# 启动
docker-compose up -d
```

---

**Plan complete and saved to `docs/plans/2026-04-10-bigscreen-implementation-plan.md`.**

**两个执行选项：**

**1. Subagent-Driven (Recommended)** - 我在此会话中为每个任务分配子代理，快速迭代

**2. Parallel Session** - 您在新会话中自行执行，需要时找我

**选择哪个方式？**