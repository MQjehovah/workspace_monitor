# 重大项目全景监控看板

基于 Vue3 + FastAPI 的项目监控看板系统

## 快速开始

### 开发模式

```bash
# 启动后端
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up --build
```

访问: http://localhost

## 功能

- PC 大屏看板 (1440px)
- 移动端看板 (390px)
- 14 个专项监控
- WebSocket 实时更新