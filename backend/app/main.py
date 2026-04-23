from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
from app.database import get_db, engine, Base
from app.models import Project, Goal, GoalScore
from app.schemas import (
    ProjectCreate, Project as ProjectSchema, StatsResponse,
    GoalCreate, GoalUpdate, GoalOut,
    GoalScoreCreate, GoalScoreOut, ProjectWithGoals, GoalWithLatestScore,
)
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


def recompute_project_score(db: Session, project_id: int):
    goals = db.query(Goal).filter(Goal.project_id == project_id).all()
    project = db.query(Project).filter(Project.id == project_id).first()
    if not goals or not project:
        if project:
            project.score = 0.0
            db.commit()
        return

    all_scores = db.query(GoalScore).filter(
        GoalScore.goal_id.in_([g.id for g in goals])
    ).order_by(GoalScore.year.desc(), GoalScore.month.desc()).all()

    if not all_scores:
        project.score = 0.0
        db.commit()
        return

    latest_year = all_scores[0].year
    latest_month = all_scores[0].month

    current_month_scores = [s for s in all_scores if s.year == latest_year and s.month == latest_month]

    if current_month_scores:
        project.score = round(sum(s.score for s in current_month_scores) / len(current_month_scores), 1)
    else:
        project.score = 0.0
    db.commit()


def build_goal_with_latest(goal: Goal) -> GoalWithLatestScore:
    latest_score = None
    latest_year = None
    latest_month = None
    if goal.scores:
        s = goal.scores[0]
        latest_score = s.score
        latest_year = s.year
        latest_month = s.month
    return GoalWithLatestScore(
        id=goal.id,
        name=goal.name,
        description=goal.description,
        latest_score=latest_score,
        latest_year=latest_year,
        latest_month=latest_month,
    )


def build_project_with_goals(project: Project) -> ProjectWithGoals:
    goals_data = [build_goal_with_latest(g) for g in project.goals]
    return ProjectWithGoals(
        id=project.id,
        name=project.name,
        owner=project.owner,
        department=project.department,
        progress=project.progress,
        achievement_rate=project.achievement_rate,
        score=project.score,
        status=project.status,
        target_date=project.target_date,
        goals=goals_data,
    )


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
    await manager.broadcast(message)
    return {"status": "broadcasted"}


@app.get("/api/projects", response_model=list[ProjectSchema])
async def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@app.get("/api/projects/{project_id}", response_model=ProjectWithGoals)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_project_with_goals(project)


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    if not projects:
        return {"total_projects": 0, "avg_progress": 0, "avg_achievement": 0, "avg_score": 0, "risk_count": 0}

    risk_count = sum(1 for p in projects if p.status == "risk")
    return {
        "total_projects": len(projects),
        "avg_progress": round(sum(p.progress for p in projects) / len(projects), 1),
        "avg_achievement": round(sum(p.achievement_rate for p in projects) / len(projects), 1),
        "avg_score": round(sum(p.score for p in projects) / len(projects), 1),
        "risk_count": risk_count,
    }


@app.get("/api/projects/{project_id}/goals", response_model=list[GoalOut])
async def list_goals(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Goal).filter(Goal.project_id == project_id).all()


@app.post("/api/projects/{project_id}/goals", response_model=GoalOut, status_code=201)
async def create_goal(project_id: int, goal_data: GoalCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    goal = Goal(project_id=project_id, **goal_data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@app.put("/api/goals/{goal_id}", response_model=GoalOut)
async def update_goal(goal_id: int, goal_data: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    update_data = goal_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(goal, key, value)
    db.commit()
    db.refresh(goal)
    return goal


@app.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    project_id = goal.project_id
    db.delete(goal)
    db.commit()
    recompute_project_score(db, project_id)
    return {"status": "deleted"}


@app.delete("/api/scores/{score_id}")
async def delete_score(score_id: int, db: Session = Depends(get_db)):
    score = db.query(GoalScore).filter(GoalScore.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    goal = db.query(Goal).filter(Goal.id == score.goal_id).first()
    project_id = goal.project_id if goal else None
    db.delete(score)
    db.commit()
    if project_id:
        recompute_project_score(db, project_id)
    return {"status": "deleted"}


@app.get("/api/goals/{goal_id}/scores", response_model=list[GoalScoreOut])
async def list_goal_scores(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return db.query(GoalScore).filter(
        GoalScore.goal_id == goal_id
    ).order_by(GoalScore.year.desc(), GoalScore.month.desc()).all()


@app.post("/api/goals/{goal_id}/scores", response_model=GoalScoreOut)
async def upsert_goal_score(goal_id: int, score_data: GoalScoreCreate, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    existing = db.query(GoalScore).filter(
        GoalScore.goal_id == goal_id,
        GoalScore.year == score_data.year,
        GoalScore.month == score_data.month,
    ).first()

    if existing:
        existing.score = score_data.score
        existing.comment = score_data.comment
        db.commit()
        db.refresh(existing)
        result = existing
    else:
        new_score = GoalScore(goal_id=goal_id, **score_data.model_dump())
        db.add(new_score)
        db.commit()
        db.refresh(new_score)
        result = new_score

    recompute_project_score(db, goal.project_id)
    return result


PROJECTS_SEED = [
    {"name": "MTPF提升专项", "owner": "徐融", "department": "技术部"},
    {"name": "8H部署专项", "owner": "崔凯旋", "department": "运维部"},
    {"name": "数字中台专项", "owner": "季明清", "department": "技术部"},
    {"name": "质量提升专项", "owner": "吴赛", "department": "质量部"},
    {"name": "渠道管理能力提升", "owner": "张海滨", "department": "商务部"},
    {"name": "Marketing能力提升", "owner": "张海滨", "department": "市场部"},
    {"name": "政府资金专项", "owner": "何波", "department": "财务部"},
    {"name": "降本专项", "owner": "巴路瑶", "department": "采购部"},
    {"name": "生产提效降费专项", "owner": "夏文昊", "department": "生产部"},
    {"name": "库存周转专项", "owner": "张珂铜", "department": "物流部"},
    {"name": "预算管理能力提升专项", "owner": "袭丽丽", "department": "财务部"},
    {"name": "核算能力提升专项", "owner": "袭丽丽", "department": "财务部"},
    {"name": "人力提效专项", "owner": "杨帆", "department": "人力部"},
    {"name": "人力降费专项", "owner": "杨帆", "department": "人力部"},
]

GOALS_SEED = {
    "MTPF提升专项": [
        "SWGT MTPF平均故障间隔时间（小时）",
        "SW50 MTPF平均故障间隔时间（小时）",
        "Titan810 MTPF平均故障间隔时间（小时）",
        'SWGT "1460"指标（小时）',
        'SW50 "1460"指标（小时）',
        'Titan810 "1460"指标（小时）',
    ],
    "8H部署专项": [
        "SWGT 部署时长（小时）",
        "Titan810 部署时长（小时）",
    ],
    "数字中台专项": [
        "MES上线",
        "三流合一",
        "0号员工上线",
    ],
    "质量提升专项": [
        "合同质量-异常率",
        "合同质量-非正常优惠率",
        "研发质量-SWGT测试泄漏率",
        "研发质量-Titan810测试泄漏率",
        "研发质量-JIRA及时关闭率",
        "采购质量-来料批次不良",
        "生产过程质量-SWGT 开箱合格率",
        "生产过程质量-SW50 开箱合格率",
        "生产过程质量-Titan810 开箱合格率",
        "生产过程质量-SWGT 90天内维修率",
        "生产过程质量-SW50 90天内维修率",
        "生产过程质量-Titan810 90天内维修率",
        "售后质量-问题一次性解决率",
        "售后质量-平均解决时效（一线城市）（小时）",
        "售后质量-平均解决时效（二线城市）（小时）",
        "售后质量-平均解决时效（海外核心国家）（小时）",
        "售后质量-平均解决时效（海外其他国家）（小时）",
    ],
    "渠道管理能力提升": [
        "经销商收入（累计）",
        "新增经销商数量（月新增）",
        "经销商存销比",
        "经销商复购率",
        "国际累计收费服务经销商占比",
        "国内累计收费服务经销商占比",
    ],
    "Marketing能力提升": [
        "毛利率",
        "应收周转天数",
    ],
    "政府资金专项": [
        "政府资金到账额（万元）",
        "新增政府资金获批（万元）",
    ],
    "降本专项": [
        "GT非独家物料占比",
        "T810非独家物料占比",
        "GT BOM成本降低（元）",
        "GT包装成本降低（元）",
        "810 BOM成本降低（元）",
        "810包装成本降低（元）",
    ],
    "生产提效降费专项": [
        "全年生产成本占比",
    ],
    "库存周转专项": [
        "库存周转天数",
        "SWGT发货预测准确率-1周",
        "SW50发货预测准确率-1周",
        "Titan810发货预测准确率-1周",
        "SWGT发货预测准确率-4周",
        "SW50发货预测准确率-4周",
        "Titan810发货预测准确率-4周",
        "SWGT发货预测准确率-5周",
        "SW50发货预测准确率-5周",
        "Titan810发货预测准确率-5周",
    ],
    "预算管理能力提升专项": [
        "主营业务经营性现金流",
    ],
    "核算能力提升专项": [
        "财务报表出具时效",
    ],
    "人力提效专项": [
        "万元人力成本收入",
    ],
    "人力降费专项": [
        "人力相关费用节约",
    ],
}

MARCH_SCORES = {
    "MTPF提升专项": {
        "SWGT MTPF平均故障间隔时间（小时）": {"score": 47.36, "comment": "目标达成率34.2%，月度目标5h，实际1.71h"},
        "SW50 MTPF平均故障间隔时间（小时）": {"score": 60.24, "comment": "目标达成率50.6%，月度目标5h，实际2.53h"},
        "Titan810 MTPF平均故障间隔时间（小时）": {"score": 100, "comment": "目标达成率176.8%，超额完成，月度目标5h，实际8.84h"},
        'SWGT "1460"指标（小时）': {"score": 20, "comment": "目标达成率0%，月度目标570h，暂无数据"},
        'SW50 "1460"指标（小时）': {"score": 100, "comment": "目标达成率194.7%，超额完成，月度目标570h，实际1110h"},
        'Titan810 "1460"指标（小时）': {"score": 100, "comment": "目标达成率179.6%，超额完成，月度目标570h，实际1024h"},
    },
    "8H部署专项": {
        "SWGT 部署时长（小时）": {"score": 85.96, "comment": "目标达成率114.9%，月度目标27h，实际23.5h"},
        "Titan810 部署时长（小时）": {"score": 79.84, "comment": "目标达成率99.6%，月度目标50h，实际50.2h"},
    },
    "数字中台专项": {
        "MES上线": {"score": 20, "comment": "4月上线目标，3月尚未达成"},
        "三流合一": {"score": 20, "comment": "6月上线目标，3月尚未达成"},
        "0号员工上线": {"score": 20, "comment": "8月上线目标，3月尚未达成"},
    },
    "质量提升专项": {
        "合同质量-异常率": {"score": 20, "comment": "数据待提供"},
        "合同质量-非正常优惠率": {"score": 20, "comment": "数据待提供"},
        "研发质量-SWGT测试泄漏率": {"score": 69.12, "comment": "目标达成率72.8%，目标≤0.3，实际0.3272"},
        "研发质量-Titan810测试泄漏率": {"score": 100, "comment": "目标达成率150.3%，超额完成，目标≤0.3，实际0.2497"},
        "研发质量-JIRA及时关闭率": {"score": 56.04, "comment": "目标达成率45.1%，目标≥0.6，实际0.4961"},
        "采购质量-来料批次不良": {"score": 80, "comment": "目标达成率100%，无来料批次不良"},
        "生产过程质量-SWGT 开箱合格率": {"score": 63.53, "comment": "目标达成率58.8%，目标≥0.85，实际0.5"},
        "生产过程质量-SW50 开箱合格率": {"score": 76.60, "comment": "目标达成率91.5%，目标≥0.85，实际0.7778"},
        "生产过程质量-Titan810 开箱合格率": {"score": 20, "comment": "目标达成率0%，无数据"},
        "生产过程质量-SWGT 90天内维修率": {"score": 39.60, "comment": "目标达成率24.5%，目标≤0.07，实际0.2857"},
        "生产过程质量-SW50 90天内维修率": {"score": 53.59, "comment": "目标达成率42.0%，目标≤0.07，实际0.1667"},
        "生产过程质量-Titan810 90天内维修率": {"score": 42.40, "comment": "目标达成率28.0%，目标≤0.07，实际0.25"},
        "售后质量-问题一次性解决率": {"score": 20, "comment": "数据待提供"},
        "售后质量-平均解决时效（一线城市）（小时）": {"score": 20, "comment": "数据待提供"},
        "售后质量-平均解决时效（二线城市）（小时）": {"score": 20, "comment": "数据待提供"},
        "售后质量-平均解决时效（海外核心国家）（小时）": {"score": 20, "comment": "数据待提供"},
        "售后质量-平均解决时效（海外其他国家）（小时）": {"score": 20, "comment": "数据待提供"},
    },
    "渠道管理能力提升": {
        "经销商收入（累计）": {"score": 20, "comment": "数据待提供"},
        "新增经销商数量（月新增）": {"score": 20, "comment": "数据待提供"},
        "经销商存销比": {"score": 20, "comment": "数据待提供"},
        "经销商复购率": {"score": 20, "comment": "数据待提供"},
        "国际累计收费服务经销商占比": {"score": 20, "comment": "数据待提供"},
        "国内累计收费服务经销商占比": {"score": 20, "comment": "数据待提供"},
    },
    "Marketing能力提升": {
        "毛利率": {"score": 20, "comment": "数据待提供"},
        "应收周转天数": {"score": 20, "comment": "数据待提供"},
    },
    "政府资金专项": {
        "政府资金到账额（万元）": {"score": 20, "comment": "数据待提供"},
        "新增政府资金获批（万元）": {"score": 20, "comment": "数据待提供"},
    },
    "降本专项": {
        "GT非独家物料占比": {"score": 71.07, "comment": "目标达成率77.7%，目标≥30%，实际23.3%"},
        "T810非独家物料占比": {"score": 80.02, "comment": "目标达成率100.0%，目标≥25%，实际25.01%"},
        "GT BOM成本降低（元）": {"score": 97.51, "comment": "目标达成率143.8%，超额完成，目标1454元，实际2090.43元"},
        "GT包装成本降低（元）": {"score": 45.94, "comment": "目标达成率32.4%，目标330元，实际107元"},
        "810 BOM成本降低（元）": {"score": 73.82, "comment": "目标达成率84.5%，目标1351元，实际1142.12元"},
        "810包装成本降低（元）": {"score": 36.94, "comment": "目标达成率21.2%，目标707元，实际149.7元"},
    },
    "生产提效降费专项": {
        "全年生产成本占比": {"score": 60.44, "comment": "目标达成率51.1%，目标≤10%，实际19.57%"},
    },
    "库存周转专项": {
        "库存周转天数": {"score": 20, "comment": "无明确月度目标，实际348天"},
        "SWGT发货预测准确率-1周": {"score": 36.0, "comment": "目标达成率20%，目标100%，实际20%"},
        "SW50发货预测准确率-1周": {"score": 36.0, "comment": "目标达成率20%，目标100%，实际20%"},
        "Titan810发货预测准确率-1周": {"score": 36.0, "comment": "目标达成率20%，目标100%，实际20%"},
        "SWGT发货预测准确率-4周": {"score": 20, "comment": "数据待提供"},
        "SW50发货预测准确率-4周": {"score": 20, "comment": "数据待提供"},
        "Titan810发货预测准确率-4周": {"score": 20, "comment": "数据待提供"},
        "SWGT发货预测准确率-5周": {"score": 20, "comment": "数据待提供"},
        "SW50发货预测准确率-5周": {"score": 20, "comment": "数据待提供"},
        "Titan810发货预测准确率-5周": {"score": 20, "comment": "数据待提供"},
    },
    "预算管理能力提升专项": {
        "主营业务经营性现金流": {"score": 20, "comment": "数据待提供"},
    },
    "核算能力提升专项": {
        "财务报表出具时效": {"score": 20, "comment": "数据待提供"},
    },
    "人力提效专项": {
        "万元人力成本收入": {"score": 20, "comment": "数据待提供"},
    },
    "人力降费专项": {
        "人力相关费用节约": {"score": 20, "comment": "数据待提供"},
    },
}


@app.post("/api/seed")
async def seed_projects(db: Session = Depends(get_db)):
    if db.query(Project).first():
        return {"message": "Data already seeded"}

    for p_data in PROJECTS_SEED:
        project = Project(
            name=p_data["name"],
            owner=p_data["owner"],
            department=p_data["department"],
            progress=0.0,
            achievement_rate=0.0,
            score=0.0,
            status="healthy",
        )
        db.add(project)
        db.flush()

        goal_names = GOALS_SEED.get(p_data["name"], [])
        for gn in goal_names:
            goal = Goal(project_id=project.id, name=gn)
            db.add(goal)
            db.flush()

            march = MARCH_SCORES.get(p_data["name"], {}).get(gn)
            if march:
                db.add(GoalScore(
                    goal_id=goal.id,
                    year=2026,
                    month=3,
                    score=march["score"],
                    comment=march.get("comment"),
                ))

    db.commit()

    for p in db.query(Project).all():
        recompute_project_score(db, p.id)

    for p in db.query(Project).all():
        if p.score >= 70:
            p.status = "healthy"
        elif p.score >= 40:
            p.status = "warning"
        else:
            p.status = "risk"
        p.achievement_rate = round(p.score, 1)
        p.progress = round(min(100, p.score * 1.15), 1)
    db.commit()

    count = db.query(Project).count()
    goal_count = db.query(Goal).count()
    score_count = db.query(GoalScore).count()
    return {
        "message": f"Seeded {count} projects, {goal_count} goals, {score_count} scores",
    }
