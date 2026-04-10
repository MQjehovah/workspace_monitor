from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
from app.database import get_db, engine, Base
from app.models import Project
from app.schemas import ProjectCreate, Project as ProjectSchema, StatsResponse
from app.websocket import manager

app = FastAPI(title="Big Screen Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "Big Screen API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "heartbeat", "status": "ok"}))
    except Exception:
        manager.disconnect(websocket)


@app.post("/api/broadcast")
async def broadcast_update(message: dict):
    """Manual trigger for broadcasting updates to all clients"""
    await manager.broadcast(message)
    return {"status": "broadcasted"}


@app.get("/api/projects", response_model=list[ProjectSchema])
async def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@app.get("/api/projects/{project_id}", response_model=ProjectSchema)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    if not projects:
        return {"total_projects": 0, "avg_progress": 0, "avg_achievement": 0, "avg_score": 0, "risk_count": 0}
    
    risk_count = sum(1 for p in projects if p.status == "risk")
    return {
        "total_projects": len(projects),
        "avg_progress": sum(p.progress for p in projects) / len(projects),
        "avg_achievement": sum(p.achievement_rate for p in projects) / len(projects),
        "avg_score": sum(p.score for p in projects) / len(projects),
        "risk_count": risk_count
    }


@app.post("/api/seed")
async def seed_projects(db: Session = Depends(get_db)):
    if db.query(Project).first():
        return {"message": "Data already seeded"}
    
    projects_data = [
        {"name": "MTPF提升专项", "owner": "张总", "department": "技术部", "progress": 78, "achievement_rate": 76, "score": 76, "status": "warning"},
        {"name": "\"8H\"部署专项", "owner": "李副总", "department": "运维部", "progress": 85, "achievement_rate": 88, "score": 88, "status": "healthy"},
        {"name": "数字中台专项", "owner": "王总监", "department": "技术部", "progress": 62, "achievement_rate": 65, "score": 65, "status": "warning"},
        {"name": "质量提升专项", "owner": "陈主任", "department": "质量部", "progress": 91, "achievement_rate": 92, "score": 92, "status": "healthy"},
        {"name": "渠道管理有效性提升", "owner": "刘总监", "department": "商务部", "progress": 55, "achievement_rate": 62, "score": 62, "status": "warning"},
        {"name": "Marketing整体能力提升", "owner": "赵总监", "department": "市场部", "progress": 43, "achievement_rate": 55, "score": 55, "status": "risk"},
        {"name": "政府资金", "owner": "孙主任", "department": "财务部", "progress": 70, "achievement_rate": 72, "score": 72, "status": "healthy"},
        {"name": "消独&产品降本", "owner": "吴总监", "department": "采购部", "progress": 48, "achievement_rate": 54, "score": 54, "status": "risk"},
        {"name": "生产成本专项", "owner": "郑经理", "department": "生产部", "progress": 66, "achievement_rate": 68, "score": 68, "status": "warning"},
        {"name": "库存周转专项", "owner": "冯总监", "department": "物流部", "progress": 82, "achievement_rate": 84, "score": 84, "status": "healthy"},
        {"name": "预算/现金流管理提升", "owner": "周总监", "department": "财务部", "progress": 74, "achievement_rate": 76, "score": 76, "status": "healthy"},
        {"name": "财务核算", "owner": "杨总监", "department": "财务部", "progress": 89, "achievement_rate": 90, "score": 90, "status": "healthy"},
        {"name": "万元人力成本收入", "owner": "钱总监", "department": "人力部", "progress": 58, "achievement_rate": 61, "score": 61, "status": "warning"},
        {"name": "人力费用节约", "owner": "石经理", "department": "人力部", "progress": 71, "achievement_rate": 73, "score": 73, "status": "healthy"},
    ]
    
    for p_data in projects_data:
        db.add(Project(**p_data))
    db.commit()
    return {"message": f"Seeded {len(projects_data)} projects"}