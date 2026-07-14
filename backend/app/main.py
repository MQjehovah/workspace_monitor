from fastapi import FastAPI, Depends, HTTPException, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
import json
import os
import uuid
from app.database import get_db, engine, Base, DATA_DIR
from app.models import Project, Goal, GoalScore, Milestone, MonthlyReport, SubTeam, SubTeamMember, SubTeamRating, MemberMonthlyScore, KeyProject
from pydantic import BaseModel
from typing import Optional, Union
from app.schemas import (
    ProjectCreate, ProjectUpdate, Project as ProjectSchema, StatsResponse,
    GoalCreate, GoalUpdate, GoalOut,
    GoalScoreCreate, GoalScoreOut, ProjectWithGoals, GoalWithLatestScore,
    MilestoneCreate, MilestoneUpdate, MilestoneOut,
    MonthlyReportCreate, MonthlyReportUpdate, MonthlyReportOut,
    SubTeamCreate, SubTeamUpdate, SubTeamOut,
    SubTeamMemberCreate, SubTeamMemberUpdate, SubTeamMemberOut,
    SubTeamRatingCreate, SubTeamRatingOut,
    MemberMonthlyScoreCreate, MemberMonthlyScoreOut, MemberMonthlyScoreUpdate,
    MemberPerformanceResponse, BatchImportResult,
    GoalTargetUpdate, GoalDefinitionUpdate, GoalManagementResponse,
    KeyProjectCreate, KeyProjectUpdate, KeyProjectOut, KeyProjectWithGoals,
)
from app.websocket import manager

UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

PDF_CACHE_DIR = os.path.join(DATA_DIR, "pdf_cache")
os.makedirs(PDF_CACHE_DIR, exist_ok=True)

app = FastAPI(title="Big Screen Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(monthly_reports)"))
    columns = [row[1] for row in result]
    if "pdf_path" not in columns:
        conn.execute(text("ALTER TABLE monthly_reports ADD COLUMN pdf_path VARCHAR(500)"))
        conn.commit()

# === 数据库迁移：Goal/GoalScore新字段 + member_monthly_scores表 ===
with engine.connect() as conn:
    # goals 表新增字段
    goal_result = conn.execute(text("PRAGMA table_info(goals)"))
    goal_cols = [row[1] for row in goal_result.fetchall()]
    for col in ("monthly_target", "yearly_target", "unit"):
        if col not in goal_cols:
            col_type = "VARCHAR(100)" if col == "unit" else "FLOAT"
            conn.execute(text(f"ALTER TABLE goals ADD COLUMN {col} {col_type}"))

    # goal_scores 表新增字段
    score_result = conn.execute(text("PRAGMA table_info(goal_scores)"))
    score_cols = [row[1] for row in score_result.fetchall()]
    for col in ("monthly_value", "actual_value", "monthly_rate", "yearly_value", "yearly_rate"):
        if col not in score_cols:
            col_type = "FLOAT" if "rate" in col else "VARCHAR(100)"
            conn.execute(text(f"ALTER TABLE goal_scores ADD COLUMN {col} {col_type}"))

    # 创建 member_monthly_scores 表（如果不存在）
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS member_monthly_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_team_member_id INTEGER NOT NULL REFERENCES sub_team_members(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            score INTEGER NOT NULL,
            comment VARCHAR(500) DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sub_team_member_id, year, month)
        )
    """))

    # 创建唯一索引
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_member_score
        ON member_monthly_scores (sub_team_member_id, year, month)
    """))

    # 添加 special 字段
    project_result = conn.execute(text("PRAGMA table_info(projects)"))
    project_cols = [row[1] for row in project_result.fetchall()]
    if "special" not in project_cols:
        conn.execute(text("ALTER TABLE projects ADD COLUMN special INTEGER DEFAULT 0"))

    # 创建 key_projects 表
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS key_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            owner VARCHAR(50),
            start_date DATE,
            end_date DATE,
            progress VARCHAR(20) DEFAULT '在行',
            status VARCHAR(20) DEFAULT 'healthy',
            created_at DATE DEFAULT CURRENT_DATE
        )
    """))

    # goals 表新增 key_project_id 和 gap_analysis
    goal_result = conn.execute(text("PRAGMA table_info(goals)"))
    goal_cols = [row[1] for row in goal_result.fetchall()]
    if "key_project_id" not in goal_cols:
        conn.execute(text("ALTER TABLE goals ADD COLUMN key_project_id INTEGER REFERENCES key_projects(id)"))
    if "gap_analysis" not in goal_cols:
        conn.execute(text("ALTER TABLE goals ADD COLUMN gap_analysis VARCHAR(500)"))

    # goal_scores 表新增 gap_analysis
    score_result2 = conn.execute(text("PRAGMA table_info(goal_scores)"))
    score_cols2 = [row[1] for row in score_result2.fetchall()]
    if "gap_analysis" not in score_cols2:
        conn.execute(text("ALTER TABLE goal_scores ADD COLUMN gap_analysis VARCHAR(500)"))

    conn.commit()
# === 迁移结束 ===

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def recompute_project_score(db: Session, project_id: int):
    goals = db.query(Goal).filter(Goal.project_id == project_id).all()
    project = db.query(Project).filter(Project.id == project_id).first()
    if not goals or not project:
        if project:
            project.score = 0.0
            db.commit()
        return

    # 只取有打分数据（score > 0）的记录，按年月降序
    all_scores = db.query(GoalScore).filter(
        GoalScore.goal_id.in_([g.id for g in goals]),
        GoalScore.score > 0
    ).order_by(GoalScore.year.desc(), GoalScore.month.desc()).all()

    if not all_scores:
        project.score = 0.0
        db.commit()
        return

    # 取有打分数据的最近年月
    latest_year = all_scores[0].year
    latest_month = all_scores[0].month

    current_month_scores = [s for s in all_scores if s.year == latest_year and s.month == latest_month]

    if current_month_scores:
        project.score = round(sum(s.score for s in current_month_scores) / len(current_month_scores), 1)
    else:
        project.score = 0.0

    if project.score >= 80:
        project.status = "healthy"
    elif project.score >= 60:
        project.status = "warning"
    else:
        project.status = "risk"
    project.achievement_rate = round(project.score, 1)
    db.commit()


def parse_monthly_actual_from_comment(comment: Optional[str]) -> Optional[str]:
    """从comment字段中解析月度实际值
    支持格式:
    - '月度目标:22h\n月度实际:38.6h\n月度达成率:56.99%'
    - '3月目标：5h；实际达成：1.71h；达成率34.2%。'
    返回字符串值，支持文本内容
    """
    if not comment:
        return None
    import re
    # 优先匹配"月度实际:"或"实际达成:"后面的值（支持任意文本）
    patterns = [
        r'月度实际[:：]\s*(.+)',
        r'实际达成[:：]\s*(.+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, comment)
        if match:
            val = match.group(1).strip()
            # 移除可能的单位后缀（如 h, % 等）
            val = re.sub(r'[h%]$', '', val).strip()
            return val if val else None
    return None


def parse_yearly_value_from_comment(comment: Optional[str]) -> Optional[str]:
    """从comment字段中解析年度实际值
    支持格式:
    - '实际值 2.29'
    - '年度实际: 2.29'
    返回字符串值，支持文本内容
    """
    if not comment:
        return None
    import re
    patterns = [
        r'实际值\s+(.+)',
        r'年度实际[:：]\s*(.+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, comment)
        if match:
            val = match.group(1).strip()
            val = re.sub(r'[h%]$', '', val).strip()
            return val if val else None
    return None


def parse_yearly_rate_from_comment(comment: Optional[str]) -> Optional[float]:
    """从comment字段中解析年度完成率
    支持格式:
    - '完成率 0.6%'
    - '年度完成率: 0.6%'
    返回百分比数值（如 0.6 表示 0.6%）
    """
    if not comment:
        return None
    import re
    patterns = [
        r'完成率\s+([0-9]+\.?[0-9]*)%?',
        r'年度完成率[:：]\s*([0-9]+\.?[0-9]*)%?',
    ]
    for pattern in patterns:
        match = re.search(pattern, comment)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def build_goal_with_latest(goal: Goal) -> GoalWithLatestScore:
    latest_score = None
    latest_year = None
    latest_month = None
    latest_comment = None
    latest_monthly_value = None
    latest_monthly_actual = None
    latest_monthly_rate = None
    latest_yearly_value = None
    latest_yearly_rate = None
    latest_gap_analysis = None
    if goal.scores:
        valid_scores = [s for s in goal.scores if s.score is not None and s.score > 0]
        valid_scores.sort(key=lambda s: (s.year, s.month), reverse=True)

        business_record = None
        if valid_scores:
            business_record = valid_scores[0]

        if not business_record and goal.scores:
            business_record = goal.scores[0]

        if business_record:
            s = business_record
            latest_score = s.score
            latest_year = s.year
            latest_month = s.month
            latest_comment = s.comment
            latest_monthly_value = s.monthly_value
            latest_monthly_actual = s.actual_value
            latest_monthly_rate = s.monthly_rate
            latest_gap_analysis = s.gap_analysis

        yearly_record = None
        if valid_scores:
            for s in valid_scores:
                if s.yearly_value is not None or s.yearly_rate is not None:
                    yearly_record = s
                    break
        if not yearly_record:
            for s in goal.scores:
                if s.yearly_value is not None or s.yearly_rate is not None:
                    yearly_record = s
                    break

        if yearly_record:
            latest_yearly_value = yearly_record.yearly_value
            latest_yearly_rate = yearly_record.yearly_rate

    return GoalWithLatestScore(
        id=goal.id,
        name=goal.name,
        project_id=goal.project_id,
        project_name=goal.project.name if goal.project else None,
        key_project_id=goal.key_project_id,
        description=goal.description,
        latest_score=latest_score,
        latest_year=latest_year,
        latest_month=latest_month,
        latest_comment=latest_comment,
        monthly_target=goal.monthly_target,
        yearly_target=goal.yearly_target,
        unit=goal.unit or "",
        latest_monthly_value=latest_monthly_value,
        latest_monthly_actual=latest_monthly_actual,
        latest_monthly_rate=latest_monthly_rate,
        latest_yearly_value=latest_yearly_value,
        latest_yearly_rate=latest_yearly_rate,
        latest_gap_analysis=latest_gap_analysis,
    )


def build_project_with_goals(project: Project) -> ProjectWithGoals:
    goals_data = [build_goal_with_latest(g) for g in project.goals]
    milestones_data = [
        MilestoneOut(
            id=m.id, project_id=m.project_id,
            group_name=m.group_name, due_date=m.due_date,
            event=m.event, achieved=m.achieved, note=m.note,
        ) for m in project.milestones
    ]
    reports_data = [
        MonthlyReportOut(
            id=r.id, project_id=r.project_id,
            year=r.year, month=r.month, content=r.content,
            pdf_path=r.pdf_path,
        ) for r in project.reports
    ]
    sub_teams_data = [
        SubTeamOut(
            id=st.id, project_id=st.project_id,
            name=st.name, leader=st.leader,
            members=[
                SubTeamMemberOut(id=m.id, sub_team_id=m.sub_team_id, name=m.name, role=m.role)
                for m in st.members
            ],
            ratings=[
                SubTeamRatingOut(id=r.id, sub_team_id=r.sub_team_id, year=r.year, month=r.month, rating=r.rating, comment=r.comment)
                for r in st.ratings
            ],
        ) for st in project.sub_teams
    ]
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
        milestones=milestones_data,
        reports=reports_data,
        sub_teams=sub_teams_data,
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
    return db.query(Project).filter(Project.special == 0).all()


@app.get("/api/special-projects", response_model=list[ProjectSchema])
async def list_special_projects(db: Session = Depends(get_db)):
    return db.query(Project).filter(Project.special == 1).all()


@app.get("/api/projects/{project_id}", response_model=ProjectWithGoals)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).options(
        joinedload(Project.goals).joinedload(Goal.scores)
    ).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_project_with_goals(project)


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.special == 0).all()
    if not projects:
        return {"total_projects": 0, "avg_progress": 0, "avg_achievement": 0, "avg_score": 0, "risk_count": 0, "achieved_teams": 0, "total_teams": 0}

    risk_count = sum(1 for p in projects if p.status == "risk")

    all_ratings = db.query(SubTeamRating).all()
    total_teams = db.query(SubTeam).count()
    if all_ratings:
        latest = max(all_ratings, key=lambda r: (r.year, r.month))
        latest_year, latest_month = latest.year, latest.month
        achieved_team_ids = set(r.sub_team_id for r in all_ratings if r.year == latest_year and r.month == latest_month and r.rating == "达成")
    else:
        achieved_team_ids = set()

    return {
        "total_projects": len(projects),
        "avg_progress": round(sum(p.progress for p in projects) / len(projects), 1),
        "avg_achievement": round(sum(p.achievement_rate for p in projects) / len(projects), 1),
        "avg_score": round(sum(p.score for p in projects) / len(projects), 1),
        "risk_count": risk_count,
        "achieved_teams": len(achieved_team_ids),
        "total_teams": total_teams,
    }


@app.get("/api/projects/{project_id}/goals", response_model=list[GoalOut])
async def list_goals(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Goal).filter(Goal.project_id == project_id).all()


@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return build_project_with_goals(project)


@app.post("/api/projects", response_model=ProjectWithGoals, status_code=201)
async def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return build_project_with_goals(project)


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"status": "deleted"}


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


@app.get("/api/projects/{project_id}/milestones", response_model=list[MilestoneOut])
async def list_milestones(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Milestone).filter(Milestone.project_id == project_id).order_by(Milestone.due_date).all()


@app.post("/api/projects/{project_id}/milestones", response_model=MilestoneOut, status_code=201)
async def create_milestone(project_id: int, data: MilestoneCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    m = Milestone(project_id=project_id, **data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@app.put("/api/milestones/{milestone_id}", response_model=MilestoneOut)
async def update_milestone(milestone_id: int, data: MilestoneUpdate, db: Session = Depends(get_db)):
    m = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(m, key, value)
    db.commit()
    db.refresh(m)
    return m


@app.delete("/api/milestones/{milestone_id}")
async def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    m = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(m)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/goals/{goal_id}/scores", response_model=list[GoalScoreOut])
async def list_goal_scores(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return db.query(GoalScore).filter(
        GoalScore.goal_id == goal_id
    ).order_by(GoalScore.year.desc(), GoalScore.month.desc()).all()


@app.get("/api/projects/{project_id}/reports", response_model=list[MonthlyReportOut])
async def list_reports(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(MonthlyReport).filter(
        MonthlyReport.project_id == project_id
    ).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()


@app.post("/api/projects/{project_id}/reports", response_model=MonthlyReportOut, status_code=201)
async def create_report(project_id: int, data: MonthlyReportCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    existing = db.query(MonthlyReport).filter(
        MonthlyReport.project_id == project_id,
        MonthlyReport.year == data.year,
        MonthlyReport.month == data.month,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Report for this month already exists")
    report = MonthlyReport(project_id=project_id, **data.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@app.put("/api/reports/{report_id}", response_model=MonthlyReportOut)
async def update_report(report_id: int, data: MonthlyReportUpdate, db: Session = Depends(get_db)):
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(report, key, value)
    from datetime import date as date_type
    report.updated_at = date_type.today()
    db.commit()
    db.refresh(report)
    return report


@app.post("/api/reports/{report_id}/pdf", response_model=MonthlyReportOut)
async def upload_report_pdf(report_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    ext = os.path.splitext(file.filename)[1]
    filename = f"report_{report_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 20MB")
    if report.pdf_path:
        old_file = os.path.join(UPLOAD_DIR, os.path.basename(report.pdf_path))
        if os.path.exists(old_file):
            os.remove(old_file)
    with open(filepath, "wb") as f:
        f.write(content)
    report.pdf_path = f"/uploads/{filename}"
    from datetime import date as date_type
    report.updated_at = date_type.today()
    db.commit()
    db.refresh(report)
    return report


@app.delete("/api/reports/{report_id}/pdf")
async def delete_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.pdf_path:
        old_file = os.path.join(UPLOAD_DIR, os.path.basename(report.pdf_path))
        if os.path.exists(old_file):
            os.remove(old_file)
        report.pdf_path = None
        db.commit()
    return {"status": "deleted"}


@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/reports/{report_id}/pdf-info")
async def get_pdf_info(report_id: int, db: Session = Depends(get_db)):
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")
    pdf_file = os.path.join(UPLOAD_DIR, os.path.basename(report.pdf_path))
    if not os.path.exists(pdf_file):
        raise HTTPException(status_code=404, detail="PDF file not found")
    try:
        import fitz
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    doc = fitz.open(pdf_file)
    count = len(doc)
    doc.close()
    return {"page_count": count}


@app.get("/api/reports/{report_id}/pdf-page/{page_num}")
async def get_pdf_page(report_id: int, page_num: int, db: Session = Depends(get_db)):
    from fastapi.responses import Response
    report = db.query(MonthlyReport).filter(MonthlyReport.id == report_id).first()
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")
    pdf_file = os.path.join(UPLOAD_DIR, os.path.basename(report.pdf_path))
    if not os.path.exists(pdf_file):
        raise HTTPException(status_code=404, detail="PDF file not found")
    cache_path = os.path.join(PDF_CACHE_DIR, f"{os.path.basename(report.pdf_path)}_{page_num}.jpg")
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return Response(content=f.read(), media_type="image/jpeg")
    try:
        import fitz
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    doc = fitz.open(pdf_file)
    if page_num < 0 or page_num >= len(doc):
        doc.close()
        raise HTTPException(status_code=404, detail="Page not found")
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_bytes = pix.tobytes("jpeg", jpg_quality=85)
    doc.close()
    with open(cache_path, "wb") as f:
        f.write(img_bytes)
    return Response(content=img_bytes, media_type="image/jpeg")


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
        # 只更新前端实际传了的字段，保留未传字段的原值
        update_data = score_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing, key, value)
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
    # 如果有 key_project_id，更新关键项目状态
    if goal.key_project_id:
        recompute_key_project_score(db, goal.key_project_id)
    return result


def recompute_key_project_score(db: Session, key_project_id: int):
    goals = db.query(Goal).filter(Goal.key_project_id == key_project_id).all()
    kp = db.query(KeyProject).filter(KeyProject.id == key_project_id).first()
    if not kp:
        return
    all_scores = db.query(GoalScore).filter(
        GoalScore.goal_id.in_([g.id for g in goals]),
        GoalScore.score > 0
    ).order_by(GoalScore.year.desc(), GoalScore.month.desc()).all()
    if not all_scores:
        kp.status = "healthy"
        db.commit()
        return
    latest_year = all_scores[0].year
    latest_month = all_scores[0].month
    current_month_scores = [s for s in all_scores if s.year == latest_year and s.month == latest_month]
    if current_month_scores:
        avg = round(sum(s.score for s in current_month_scores) / len(current_month_scores), 1)
    else:
        avg = 0.0
    if avg >= 80:
        kp.status = "healthy"
    elif avg >= 60:
        kp.status = "warning"
    else:
        kp.status = "risk"
    db.commit()


def compute_key_project_score(db: Session, key_project_id: int) -> Optional[float]:
    """计算关键项目最新月份的平均得分（不写库），无数据返回 None"""
    goals = db.query(Goal).filter(Goal.key_project_id == key_project_id).all()
    if not goals:
        return None
    all_scores = db.query(GoalScore).filter(
        GoalScore.goal_id.in_([g.id for g in goals]),
        GoalScore.score > 0
    ).order_by(GoalScore.year.desc(), GoalScore.month.desc()).all()
    if not all_scores:
        return None
    latest_year = all_scores[0].year
    latest_month = all_scores[0].month
    current_month_scores = [s for s in all_scores if s.year == latest_year and s.month == latest_month]
    if current_month_scores:
        return round(sum(s.score for s in current_month_scores) / len(current_month_scores), 1)
    return None


@app.get("/api/key-projects", response_model=list[KeyProjectOut])
async def list_key_projects(db: Session = Depends(get_db)):
    kps = db.query(KeyProject).order_by(KeyProject.created_at.desc()).all()
    result = []
    for kp in kps:
        score = compute_key_project_score(db, kp.id)
        result.append(KeyProjectOut(
            id=kp.id, name=kp.name, owner=kp.owner,
            start_date=kp.start_date, end_date=kp.end_date,
            progress=kp.progress, status=kp.status, score=score,
        ))
    return result


@app.get("/api/key-projects/{key_project_id}", response_model=KeyProjectWithGoals)
async def get_key_project(key_project_id: int, db: Session = Depends(get_db)):
    kp = db.query(KeyProject).filter(KeyProject.id == key_project_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="Key project not found")
    goals = db.query(Goal).filter(Goal.key_project_id == key_project_id).options(joinedload(Goal.project)).all()
    goals_data = [build_goal_with_latest(g) for g in goals]
    score = compute_key_project_score(db, kp.id)
    return KeyProjectWithGoals(
        id=kp.id,
        name=kp.name,
        owner=kp.owner,
        start_date=kp.start_date,
        end_date=kp.end_date,
        progress=kp.progress,
        status=kp.status,
        score=score,
        goals=goals_data,
    )


@app.post("/api/key-projects", response_model=KeyProjectOut, status_code=201)
async def create_key_project(data: KeyProjectCreate, db: Session = Depends(get_db)):
    kp = KeyProject(**data.model_dump())
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return kp


@app.put("/api/key-projects/{key_project_id}", response_model=KeyProjectOut)
async def update_key_project(key_project_id: int, data: KeyProjectUpdate, db: Session = Depends(get_db)):
    kp = db.query(KeyProject).filter(KeyProject.id == key_project_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="Key project not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(kp, key, value)
    db.commit()
    db.refresh(kp)
    return kp


@app.delete("/api/key-projects/{key_project_id}")
async def delete_key_project(key_project_id: int, db: Session = Depends(get_db)):
    kp = db.query(KeyProject).filter(KeyProject.id == key_project_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="Key project not found")
    # 解除关联的目标
    db.query(Goal).filter(Goal.key_project_id == key_project_id).update({"key_project_id": None})
    db.delete(kp)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/projects/{project_id}/subteams", response_model=list[SubTeamOut])
async def list_sub_teams(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    teams = db.query(SubTeam).filter(SubTeam.project_id == project_id).all()
    result = []
    for st in teams:
        members = db.query(SubTeamMember).filter(SubTeamMember.sub_team_id == st.id).all()
        ratings = db.query(SubTeamRating).filter(SubTeamRating.sub_team_id == st.id).order_by(SubTeamRating.year.desc(), SubTeamRating.month.desc()).all()
        result.append(SubTeamOut(
            id=st.id, project_id=st.project_id, name=st.name, leader=st.leader,
            members=[SubTeamMemberOut(id=m.id, sub_team_id=m.sub_team_id, name=m.name, role=m.role) for m in members],
            ratings=[SubTeamRatingOut(id=r.id, sub_team_id=r.sub_team_id, year=r.year, month=r.month, rating=r.rating, comment=r.comment) for r in ratings],
        ))
    return result


@app.post("/api/projects/{project_id}/subteams", response_model=SubTeamOut, status_code=201)
async def create_sub_team(project_id: int, data: SubTeamCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    st = SubTeam(project_id=project_id, name=data.name, leader=data.leader)
    db.add(st)
    db.flush()
    members_out = []
    for m in data.members:
        member = SubTeamMember(sub_team_id=st.id, name=m.name, role=m.role)
        db.add(member)
        db.flush()
        members_out.append(SubTeamMemberOut(id=member.id, sub_team_id=st.id, name=m.name, role=m.role))
    db.commit()
    return SubTeamOut(id=st.id, project_id=project_id, name=st.name, leader=st.leader, members=members_out, ratings=[])


@app.put("/api/subteams/{subteam_id}", response_model=SubTeamOut)
async def update_sub_team(subteam_id: int, data: SubTeamUpdate, db: Session = Depends(get_db)):
    st = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="SubTeam not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(st, key, value)
    db.commit()
    members = db.query(SubTeamMember).filter(SubTeamMember.sub_team_id == st.id).all()
    ratings = db.query(SubTeamRating).filter(SubTeamRating.sub_team_id == st.id).order_by(SubTeamRating.year.desc(), SubTeamRating.month.desc()).all()
    return SubTeamOut(
        id=st.id, project_id=st.project_id, name=st.name, leader=st.leader,
        members=[SubTeamMemberOut(id=m.id, sub_team_id=m.sub_team_id, name=m.name, role=m.role) for m in members],
        ratings=[SubTeamRatingOut(id=r.id, sub_team_id=r.sub_team_id, year=r.year, month=r.month, rating=r.rating, comment=r.comment) for r in ratings],
    )


@app.delete("/api/subteams/{subteam_id}")
async def delete_sub_team(subteam_id: int, db: Session = Depends(get_db)):
    st = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="SubTeam not found")
    db.delete(st)
    db.commit()
    return {"status": "deleted"}


@app.post("/api/subteams/{subteam_id}/members", response_model=SubTeamMemberOut, status_code=201)
async def add_sub_team_member(subteam_id: int, data: SubTeamMemberCreate, db: Session = Depends(get_db)):
    st = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="SubTeam not found")
    member = SubTeamMember(sub_team_id=subteam_id, name=data.name, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@app.put("/api/subteam-members/{member_id}", response_model=SubTeamMemberOut)
async def update_sub_team_member(member_id: int, data: SubTeamMemberUpdate, db: Session = Depends(get_db)):
    member = db.query(SubTeamMember).filter(SubTeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if data.name is not None:
        member.name = data.name
    if data.role is not None:
        member.role = data.role
    db.commit()
    db.refresh(member)
    return member


@app.delete("/api/subteam-members/{member_id}")
async def delete_sub_team_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(SubTeamMember).filter(SubTeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"status": "deleted"}


@app.post("/api/subteams/{subteam_id}/ratings", response_model=SubTeamRatingOut)
async def upsert_sub_team_rating(subteam_id: int, data: SubTeamRatingCreate, db: Session = Depends(get_db)):
    st = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="SubTeam not found")
    existing = db.query(SubTeamRating).filter(
        SubTeamRating.sub_team_id == subteam_id,
        SubTeamRating.year == data.year,
        SubTeamRating.month == data.month,
    ).first()
    if existing:
        existing.rating = data.rating
        existing.comment = data.comment
        db.commit()
        db.refresh(existing)
        return existing
    rating = SubTeamRating(sub_team_id=subteam_id, **data.model_dump())
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@app.get("/api/subteams/{subteam_id}/ratings", response_model=list[SubTeamRatingOut])
async def list_sub_team_ratings(subteam_id: int, db: Session = Depends(get_db)):
    st = db.query(SubTeam).filter(SubTeam.id == subteam_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="SubTeam not found")
    return db.query(SubTeamRating).filter(
        SubTeamRating.sub_team_id == subteam_id
    ).order_by(SubTeamRating.year.desc(), SubTeamRating.month.desc()).all()


@app.delete("/api/subteam-ratings/{rating_id}")
async def delete_sub_team_rating(rating_id: int, db: Session = Depends(get_db)):
    r = db.query(SubTeamRating).filter(SubTeamRating.id == rating_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(r)
    db.commit()
    return {"status": "deleted"}


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


from datetime import date as date_type

MILESTONES_SEED = {
    "MTPF提升专项": [
        {"group": "研发分阶段提供提升专项版本", "date": "2026-04-30", "event": "发布一个专项版本（V1）"},
        {"group": "研发分阶段提供提升专项版本", "date": "2026-06-30", "event": "研发框架重构完成 + 工单问题解决50%"},
        {"group": "研发分阶段提供提升专项版本", "date": "2026-07-31", "event": "发布一个专项版本（V2）"},
        {"group": "研发分阶段提供提升专项版本", "date": "2026-10-31", "event": "发布一个专项版本（V3）"},
        {"group": "研发分阶段提供提升专项版本", "date": "2026-12-31", "event": "工单问题解决超过85%，MTBF和1460指标分别达成400h和2000h"},
        {"group": "质量跟踪工单TOP问题解决", "date": "2026-03-31", "event": "各月跟踪jira回归和关闭的执行情况"},
        {"group": "质量跟踪工单TOP问题解决", "date": "2026-06-30", "event": "各月跟踪jira回归和关闭的执行情况"},
        {"group": "质量跟踪工单TOP问题解决", "date": "2026-09-30", "event": "各月跟踪jira回归和关闭的执行情况"},
        {"group": "质量跟踪工单TOP问题解决", "date": "2026-12-31", "event": "各月跟踪jira回归和关闭的执行情况"},
        {"group": "工程服务完成涉及现场的版本部署", "date": "2026-05-30", "event": "专项版本（V1）60%部署"},
        {"group": "工程服务完成涉及现场的版本部署", "date": "2026-06-30", "event": "专项版本（V1）100%部署"},
        {"group": "工程服务完成涉及现场的版本部署", "date": "2026-09-30", "event": "专项版本（V2）100%部署"},
        {"group": "工程服务完成涉及现场的版本部署", "date": "2026-12-31", "event": "专项版本（V3）100%部署"},
    ],
    "8H部署专项": [
        {"group": "SW GT按照MRD完成易部署功能开发", "date": "2026-04-30", "event": "4月15日完成第一阶段开发，4月30日上线"},
        {"group": "SW GT按照MRD完成易部署功能开发", "date": "2026-07-31", "event": "6月30日完成第二阶段功能开发，7月30日上线"},
        {"group": "SW GT按照MRD完成易部署功能开发", "date": "2026-09-30", "event": "预研功能（远程部署支持），9月30日上线"},
        {"group": "Titan 810产品易部署功能开发", "date": "2026-04-15", "event": "完成Titan 810产品易部署MRD评审"},
        {"group": "Titan 810产品易部署功能开发", "date": "2026-04-30", "event": "完成易部署功能开发计划评审，FAE完成培训和部署流程优化"},
        {"group": "FAE能力建设", "date": "2026-04-07", "event": "输出Q1部署总结"},
        {"group": "FAE能力建设", "date": "2026-06-30", "event": "完成FAE集中培训"},
        {"group": "FAE能力建设", "date": "2026-08-30", "event": "基于SW GT易部署第二阶段功能上线，FAE完成培训"},
    ],
    "数字中台专项": [
        {"group": "硬件部署与系统导入", "date": "2026-04-30", "event": "完成服务器硬件架设，CRM上线、启动用友ERP财务系统部署"},
        {"group": "系统联调与测试", "date": "2026-04-30", "event": "MES系统上线，中台升级对接新系统，完成数据清洗"},
        {"group": "上线冲刺与试运行", "date": "2026-06-30", "event": "完成用友正式环境构建、集成代码部署，打通经营全流程"},
        {"group": "关键流程打通与看板上线", "date": "2026-06-30", "event": "全新数字中台正式投入使用，支撑月底结账、报表出具"},
        {"group": "完成AI基础能力搭建", "date": "2026-08-31", "event": "构建统一的算力管理知识库和agent能力"},
        {"group": "\"0号员工\"上线", "date": "2026-08-31", "event": "AI数字交互实现，完成数据汇总与分析，支撑运营管理"},
    ],
    "质量提升专项": [
        {"group": "筹备成长期（Q2末）", "date": "2026-06-30", "event": "完成商务流程梳理、合同变更管控标准制定、异常率降至6%以内"},
        {"group": "冲刺提升期（Q3末）", "date": "2026-09-30", "event": "合同异常率控制在5%以下、非正常优惠合同比例控制在10%以内"},
        {"group": "闭环收尾期（Q4末）", "date": "2026-12-31", "event": "全年商务质量目标持续达标，复盘全年工作"},
        {"group": "测试泄漏率降低", "date": "2026-06-30", "event": "版本测试自动化试点；完成Q2现场问题专项排雷"},
        {"group": "测试泄漏率降低", "date": "2026-09-30", "event": "完成Q3现场问题专项排雷；开发代码静动态审查纳入门禁"},
        {"group": "测试泄漏率降低", "date": "2026-12-31", "event": "完成Q4现场问题专项排雷"},
        {"group": "JIRA关闭提升", "date": "2026-04-30", "event": "团队及个人jira问题处理进展上大屏，实时通报"},
        {"group": "JIRA关闭提升", "date": "2026-05-31", "event": "长期未解决jira单每周专项解决；jira处理进展纳入员工绩效"},
        {"group": "JIRA关闭提升", "date": "2026-08-31", "event": "JIRA处理流程优化，应用自动化工具提升效率"},
        {"group": "采购质量体系搭建", "date": "2026-06-30", "event": "体系搭建与标准夯实，规范检验流程"},
        {"group": "采购质量体系搭建", "date": "2026-09-30", "event": "深度审核与精准优化"},
        {"group": "采购质量体系搭建", "date": "2026-12-31", "event": "优胜劣汰与全面闭环"},
        {"group": "消除独家", "date": "2026-06-30", "event": "GT非独家供应商占比达85%，T810达65%"},
        {"group": "生产过程质量", "date": "2026-06-30", "event": "现状排查及生产过程管控，建立包装标准化作业指导书"},
        {"group": "生产过程质量", "date": "2026-08-31", "event": "检测过程优化，推行工位扫码质检机制"},
        {"group": "生产过程质量", "date": "2026-10-31", "event": "人员能力提升，实施关键工序100%防错"},
        {"group": "生产过程质量", "date": "2026-12-31", "event": "流程闭环优化，建立下线全性能测试标准"},
        {"group": "售后质量", "date": "2026-06-30", "event": "国内中心仓库准备完毕；海外欧洲、北美建立中心仓库"},
        {"group": "售后质量", "date": "2026-09-30", "event": "国内前置仓准备完毕；服务商24小时接单率95%"},
        {"group": "售后质量", "date": "2026-11-30", "event": "海外前置仓准备完毕；第三方服务占比40%"},
        {"group": "售后质量", "date": "2026-12-31", "event": "完成公司外包管理标准；完成10次+代理商培训"},
    ],
    "渠道管理能力提升": [
        {"group": "经销商拓展（Q2末）", "date": "2026-06-30", "event": "累计新增15个经销商、收入达到4600万、存销比2:1、复购率25%"},
        {"group": "经销商拓展（Q3末）", "date": "2026-09-30", "event": "累计新增20个经销商、收入11000万、存销比1.5:1、复购率70%"},
        {"group": "经销商拓展（Q4末）", "date": "2026-12-31", "event": "收入1.6亿、存销比与复购率持续达标，30个新增经销商稳定运营"},
        {"group": "服务收费（Q2末）", "date": "2026-06-30", "event": "经销商POC、开局、现场服务等收费标准确定"},
        {"group": "服务收费（Q3末）", "date": "2026-09-30", "event": "完成国内国际所有新签经销商服务收费合同确立"},
        {"group": "服务收费（Q4末）", "date": "2026-12-31", "event": "国外经销商60%，国内30%比例的经销商合同服务比例"},
    ],
    "Marketing能力提升": [
        {"group": "筹备成长期（Q2末）", "date": "2026-06-30", "event": "搭建毛利率与应收周转监控体系，毛利率≥40%、应收周转≤55天"},
        {"group": "冲刺提升期（Q3末）", "date": "2026-09-30", "event": "毛利率≥50%、应收周转≤46天，达成全年目标"},
        {"group": "闭环收尾期（Q4末）", "date": "2026-12-31", "event": "毛利率稳定≥60%、应收周转稳定≤40天"},
    ],
    "政府资金专项": [
        {"group": "南京资金", "date": "2026-12-31", "event": "南京政府资金500万元获批"},
        {"group": "嘉兴1500万", "date": "2026-05-31", "event": "完成嘉兴项目公司注册及人才项目申请"},
        {"group": "嘉兴1500万", "date": "2026-07-31", "event": "申报创业人才项目；申请设备投资补助300万元"},
        {"group": "嘉兴1500万", "date": "2026-11-30", "event": "获批1345万元"},
        {"group": "深圳1000万", "date": "2026-04-30", "event": "收集深圳各地政策"},
        {"group": "深圳1000万", "date": "2026-06-30", "event": "注册深圳落地公司"},
        {"group": "深圳1000万", "date": "2026-11-30", "event": "获批1000万元"},
        {"group": "房租减免", "date": "2026-04-30", "event": "C17栋减免房租155万+红枫科技园减免432万"},
        {"group": "到账资金", "date": "2026-03-31", "event": "到账300万元"},
        {"group": "到账资金", "date": "2026-05-31", "event": "到账150万元"},
        {"group": "到账资金", "date": "2026-08-31", "event": "红枫科技园装修款500万元"},
        {"group": "到账资金", "date": "2026-12-31", "event": "嘉兴南湖750万到账、80万到账、500万获批"},
    ],
    "降本专项": [
        {"group": "GT非独家物料", "date": "2026-06-30", "event": "一类物料完成度达90%、二类达75%、三类达90%、四类达50%"},
        {"group": "T810非独家物料", "date": "2026-06-30", "event": "一类物料完成度达70%、二类达60%、三类达80%、四类达40%"},
        {"group": "GT BOM成本降低", "date": "2026-07-31", "event": "7月起GT各版本发货成本降低1万元/台"},
        {"group": "GT包装成本降低", "date": "2026-07-31", "event": "7月起单套包装成本降低30%（330元/套）"},
        {"group": "810 BOM成本降低", "date": "2026-07-31", "event": "7月起810机器加工作站发货成本降低3万元/台"},
        {"group": "810包装成本降低", "date": "2026-07-31", "event": "7月起单套包装成本降低30%（707元/套）"},
    ],
    "生产提效降费专项": [
        {"group": "Q1目标", "date": "2026-03-31", "event": "生产成本占比10%"},
        {"group": "Q2目标", "date": "2026-06-30", "event": "生产成本占比8%"},
        {"group": "Q3目标", "date": "2026-09-30", "event": "生产成本占比7%"},
        {"group": "Q4目标", "date": "2026-11-30", "event": "生产成本占比6%"},
    ],
    "库存周转专项": [
        {"group": "库存周转天数", "date": "2026-06-30", "event": "库存周转天数达120天"},
        {"group": "库存周转天数", "date": "2026-09-30", "event": "库存周转天数达90天"},
        {"group": "库存周转天数", "date": "2026-12-31", "event": "库存周转天数达55天"},
        {"group": "发货预测准确率", "date": "2026-06-30", "event": "1周100%、4周85%、5周70%"},
        {"group": "发货预测准确率", "date": "2026-12-31", "event": "1周100%、4周85%、5周70%（全年维持）"},
    ],
    "预算管理能力提升专项": [
        {"group": "规则制定", "date": "2026-03-31", "event": "初步制定全面预算管理规则"},
        {"group": "规则执行", "date": "2026-04-30", "event": "执行全面预算管理规则，输出3月现金流执行报告"},
        {"group": "半年复盘", "date": "2026-06-30", "event": "半年预算复盘会，6月经营性净现金流应为正"},
        {"group": "规则执行", "date": "2026-09-30", "event": "组织Q3预算复盘会"},
        {"group": "全年目标", "date": "2026-12-31", "event": "全年经营性净现金流为正"},
    ],
    "核算能力提升专项": [
        {"group": "中台上线前", "date": "2026-03-31", "event": "协调台账建立，出报表预测"},
        {"group": "中台上线前", "date": "2026-04-30", "event": "按周出收入成本预测数据"},
        {"group": "中台上线", "date": "2026-06-30", "event": "中台上线"},
        {"group": "中台上线后", "date": "2026-08-30", "event": "达成7天出报表要求"},
    ],
    "人力提效专项": [
        {"group": "方案确定", "date": "2026-03-31", "event": "薪酬制度优化方案、绩效考核方案确定"},
        {"group": "人才到岗", "date": "2026-04-30", "event": "5个高密度岗位交付"},
        {"group": "人才到岗", "date": "2026-05-31", "event": "3个高密度岗位交付"},
        {"group": "动态预算", "date": "2026-06-30", "event": "动态预算及周期内人力配置计划确定"},
        {"group": "动态预算", "date": "2026-09-30", "event": "动态预算及周期内人力配置计划确定"},
    ],
    "人力降费专项": [
        {"group": "主体成立", "date": "2026-04-30", "event": "深圳主体成立，设立社保公积金公司账号"},
        {"group": "用工切换", "date": "2026-05-15", "event": "用工方式切换（代理20人、外包14人）"},
        {"group": "采购降本", "date": "2026-06-30", "event": "人力资源服务商采购降本"},
    ],
}

# 子团队种子数据（暂无真实数据，留空，后续通过页面或API录入）
SUBTEAMS_SEED = {}


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

        milestones = MILESTONES_SEED.get(p_data["name"], [])
        for ms in milestones:
            due = None
            if ms.get("date"):
                due = date_type.fromisoformat(ms["date"])
            db.add(Milestone(
                project_id=project.id,
                group_name=ms.get("group"),
                due_date=due,
                event=ms.get("event"),
            ))

        # 子团队数据通过页面或API单独录入，不在seed中预填
        # subteams = SUBTEAMS_SEED.get(p_data["name"], [])
        # for st_data in subteams:
        #     ...

    db.commit()

    for p in db.query(Project).all():
        recompute_project_score(db, p.id)

    for p in db.query(Project).all():
        if p.score >= 80:
            p.status = "healthy"
        elif p.score >= 60:
            p.status = "warning"
        else:
            p.status = "risk"
        p.achievement_rate = round(p.score, 1)
    db.commit()

    count = db.query(Project).count()
    goal_count = db.query(Goal).count()
    score_count = db.query(GoalScore).count()
    ms_count = db.query(Milestone).count()
    return {
        "message": f"Seeded {count} projects, {goal_count} goals, {score_count} scores, {ms_count} milestones",
    }


# ============================================================
#  成员每月评级管理 API
# ============================================================

@app.get("/api/score-rules")
async def get_score_rules():
    """返回评分规则"""
    return {
        "score_levels": [
            {"score": 1, "label": "1分（差）", "range": "<40", "color": "#e74c3c", "desc": "远未达成目标，存在明显短板"},
            {"score": 2, "label": "2分（合格）", "range": "40-55", "color": "#e67e22", "desc": "基本完成工作，但距离目标有较大差距"},
            {"score": 3, "label": "3分（良）", "range": "55-70", "color": "#f39c12", "desc": "较好完成工作，大部分目标达成"},
            {"score": 4, "label": "4分（优秀）", "range": "70-85", "color": "#27ae60", "desc": "出色完成工作，超额达成部分目标"},
            {"score": 5, "label": "5分（卓越）", "range": "≥85", "color": "#2980b9", "desc": "卓越表现，全面超额完成目标，可作为标杆"},
        ],
        "team_distribution": {
            "excellent": {
                "condition": "团队得分 >80分",
                "ratio": [0, 10, 30, 40, 20],
            },
            "good": {
                "condition": "团队得分 60-80分",
                "ratio": [10, 20, 30, 30, 10],
            },
            "fair": {
                "condition": "团队得分 <60分",
                "ratio": [20, 30, 30, 20, 0],
            },
        },
        "leader_rule": {
            "title": "专项负责人赋分规则",
            "rules": [
                "1. 专项负责人/子团队负责人不参与上述比例强制分配",
                "2. 负责人得分由上级根据专项整体达成情况+个人贡献度综合评定（1-5分）",
                "3. 负责人得分可高于团队成员最高分，以体现管理责任与贡献",
                "4. 当专项整体未达成目标（<60分）时，负责人得分原则上不超过3分",
                "5. 当专项超额达成目标（≥85分）时，负责人可直接评为5分（卓越）",
                "6. 负责人得分需在成员评分完成后，由部门负责人或PMO确认后生效",
            ],
        },
    }


def _build_member_performance(db: Session, members_query) -> dict:
    """构建成员绩效数据（内部辅助函数）"""
    # 固定显示 2026年4月～12月
    months_list = [
        {"year": 2026, "month": m, "label": f"2026-{m:02d}"}
        for m in range(4, 13)
    ]

    rows = []
    # 预先查询所有相关子团队的最新评级月份，避免 N+1 查询
    sub_team_ids = set()
    for member in members_query:
        sub_team_ids.add(member.sub_team_id)
    latest_rating_map: dict = {}  # sub_team_id -> {"year":.., "month":..}
    if sub_team_ids:
        rating_rows = db.query(SubTeamRating).filter(
            SubTeamRating.sub_team_id.in_(sub_team_ids)
        ).order_by(SubTeamRating.year.desc(), SubTeamRating.month.desc()).all()
        for r in rating_rows:
            if r.sub_team_id not in latest_rating_map:
                latest_rating_map[r.sub_team_id] = {"year": r.year, "month": r.month}

    for member in members_query:
        # 获取成员所属的子团队和项目信息
        sub_team = db.query(SubTeam).filter(SubTeam.id == member.sub_team_id).first()
        project_name = ""
        sub_team_name = ""
        specialty_name = ""
        if sub_team:
            sub_team_name = sub_team.name
            project = db.query(Project).filter(Project.id == sub_team.project_id).first()
            if project:
                project_name = project.name
            specialty_name = getattr(sub_team, 'specialty_name', '') or ''

        # 该成员所在子团队的最新评级月份
        latest_rating_month = latest_rating_map.get(member.sub_team_id) if sub_team else None

        # 获取该成员的月度得分
        scores_dict = {}
        score_records = db.query(MemberMonthlyScore).filter(
            MemberMonthlyScore.sub_team_member_id == member.id
        ).order_by(MemberMonthlyScore.year.desc(), MemberMonthlyScore.month.desc()).all()

        for sr in score_records:
            key = f"{sr.year}-{sr.month:02d}"
            scores_dict[key] = {
                "score": sr.score,
                "id": sr.id,
                "comment": sr.comment,
            }

        row_scores = []
        for ml in months_list:
            key = f"{ml['year']}-{ml['month']:02d}"
            if key in scores_dict:
                row_scores.append({
                    "year": ml["year"],
                    "month": ml["month"],
                    "label": ml["label"],
                    "score": scores_dict[key]["score"],
                    "id": scores_dict[key]["id"],
                    "comment": scores_dict[key]["comment"],
                })
            else:
                row_scores.append({
                    "year": ml["year"],
                    "month": ml["month"],
                    "label": ml["label"],
                    "score": None,
                    "id": None,
                    "comment": "",
                })

        rows.append({
            "member_id": member.id,
            "member_name": member.name,
            "role": member.role or "",
            "project_id": sub_team.project_id if sub_team else 0,
            "project_name": project_name,
            "sub_team_name": sub_team_name,
            "specialty_name": specialty_name,
            "sub_team_id": member.sub_team_id,
            "latest_rating_month": latest_rating_month,
            "scores": row_scores,
        })

    # 按项目 ID 排序（与首页 /api/projects 顺序一致），同项目内按子团队 ID 排序
    def _sort_key(r):
        return (r["project_id"], r["sub_team_name"])
    rows.sort(key=_sort_key)

    return {
        "months": months_list,
        "rows": rows,
        "total": len(rows),
    }


@app.get("/api/member-performance")
async def get_all_member_performance(
    project_id: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    """获取所有成员的月度绩效概览"""
    query = db.query(SubTeamMember).join(
        SubTeam, SubTeamMember.sub_team_id == SubTeam.id
    ).join(
        Project, SubTeam.project_id == Project.id
    ).filter(Project.special == 0)

    if project_id is not None:
        query = query.filter(SubTeam.project_id == project_id)

    members = query.order_by(SubTeamMember.id).all()
    return _build_member_performance(db, members)


@app.get("/api/member-performance/{member_id}")
async def get_member_performance(
    member_id: int,
    db: Session = Depends(get_db)
):
    """获取单个成员的绩效详情"""
    member = db.query(SubTeamMember).filter(SubTeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    return _build_member_performance(db, [member])


@app.put("/api/member-scores/{score_id}")
async def update_member_score(
    score_id: int,
    data: MemberMonthlyScoreUpdate,
    db: Session = Depends(get_db)
):
    """修改单个成员的单月得分"""
    record = db.query(MemberMonthlyScore).filter(MemberMonthlyScore.id == score_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="评分记录不存在")

    if data.score is not None:
        if data.score < 1 or data.score > 5:
            raise HTTPException(status_code=400, detail="得分必须在1-5之间")
        record.score = data.score
    if data.comment is not None:
        record.comment = data.comment

    db.commit()
    db.refresh(record)
    return MemberMonthlyScoreOut(
        id=record.id,
        sub_team_member_id=record.sub_team_member_id,
        year=record.year,
        month=record.month,
        score=record.score,
        comment=record.comment,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@app.post("/api/member-scores/batch-import")
async def batch_import_member_scores(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """批量导入成员月度得分（支持 Excel .xlsx/.xls 和 CSV 格式）"""
    import io
    import csv as csv_module

    content = await file.read()
    filename = file.filename or ""
    is_csv = filename.endswith('.csv')
    is_xlsx = content.startswith(b"PK")

    # ---- CSV 解析 ----
    if is_csv:
        try:
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                text = content.decode('gbk')
            except Exception:
                raise HTTPException(status_code=400, detail="CSV文件编码无法识别，请使用UTF-8或GBK")
        reader = csv_module.reader(io.StringIO(text))
        rows_raw = list(reader)
        header_row = [str(c).strip() for c in (rows_raw[0] if rows_raw else [])]
        data_rows = [row for row in rows_raw[1:] if any(cell.strip() for cell in row)]
        # 统一为字符串列表格式给 _process_import_row
        processed_rows = [[str(c).strip() for c in row] for row in data_rows]
    # ---- xlsx 解析 ----
    elif is_xlsx:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
            ws = wb.active
        except ImportError:
            raise HTTPException(status_code=500, detail="服务器未安装openpyxl，请执行: pip install openpyxl")
        header_row = None
        processed_rows = []
        for idx, row in enumerate(ws.iter_rows(values_only=True)):
            if idx == 0:
                header_row = [str(c or "").strip() for c in row]
                continue
            if not any(c for c in row):
                continue
            processed_rows.append([str(c or "").strip() for c in row])
    # ---- xls (xlrd) 解析 ----
    else:
        try:
            import xlrd
            wb = xlrd.open_workbook(file_contents=content)
            ws = wb.sheet_by_index(0)
        except ImportError:
            raise HTTPException(status_code=500, detail="服务器未安装xlrd，请执行: pip install xlrd")
        header_row = [str(ws.cell_value(0, c)).strip() for c in range(ws.ncols)]
        processed_rows = []
        for r_idx in range(1, ws.nrows):
            row_values = [str(ws.cell_value(r_idx, c)).strip() for c in range(ws.ncols)]
            if not any(v for v in row_values):
                continue
            processed_rows.append(row_values)

    success_count = 0
    fail_count = 0
    errors = []

    expected_headers = ["专项名称", "子团队名称", "项目成员", "月份", "得分"]

    if not header_row:
        raise HTTPException(status_code=400, detail="文件中没有表头行")

    for r_idx, row_values in enumerate(processed_rows, start=2):
        result = _process_import_row(db, row_values, header_row, r_idx)
        if result["ok"]:
            success_count += 1
        else:
            fail_count += 1
            errors.append(result["error"])

    try:
        db.commit()
    except Exception as commit_err:
        db.rollback()
        # 如果是唯一约束冲突等数据库错误，作为一条统一错误返回
        raise HTTPException(status_code=500, detail=f"数据库提交失败: {str(commit_err)}")

    return BatchImportResult(
        success_count=success_count,
        fail_count=fail_count,
        total=success_count + fail_count,
        errors=errors[:20],  # 最多返回前20条错误
    )


def _process_import_row(db: Session, row_values: list, header_row: list, line_num: int) -> dict:
    """处理导入的一行数据"""
    try:
        # 构建映射：列名 -> 值
        row_dict = {}
        for i, h in enumerate(header_row):
            if i < len(row_values):
                row_dict[h] = row_values[i]

        specialty_name = row_dict.get("专项名称", "").strip()
        sub_team_name = row_dict.get("子团队名称", "").strip()
        member_name = row_dict.get("项目成员", "").strip()
        month_str = str(row_dict.get("月份", "")).strip()
        score_str = str(row_dict.get("得分", "")).strip()

        if not all([specialty_name, sub_team_name, member_name, month_str, score_str]):
            return {"ok": False, "error": f"第{line_num}行：必填字段缺失"}

        # 解析月份 (支持 "2026-03" 或 "3月" 或 "2026年3月")
        import re
        month_match = re.match(r"^(\d{4})[-/年](\d{1,2})$", month_str)
        if month_match:
            year = int(month_match.group(1))
            month = int(month_match.group(2))
        elif month_match := re.match(r"^(\d{1,2})月?$", month_str):
            from datetime import date
            year = date.today().year
            month = int(month_match.group(1))
        else:
            return {"ok": False, "error": f"第{line_num}行：月份格式不正确 '{month_str}'，请使用如 2026-03 或 3月"}

        score_val = int(float(score_str))
        if score_val < 1 or score_val > 5:
            return {"ok": False, "error": f"第{line_num}行：得分必须在1-5之间，当前值 {score_val}"}

        # 查找匹配的项目
        project = db.query(Project).filter(Project.name == specialty_name).first()
        if not project:
            return {"ok": False, "error": f"第{line_num}行：未找到专项 '{specialty_name}'"}

        # 处理"专项负责人"特殊情况：不属于任何子团队，跳过子团队匹配
        is_specialty_leader = (sub_team_name == "专项负责人" or sub_team_name == "负责人")

        if is_specialty_leader:
            # 专项负责人：直接在 SubTeamMember 中按名字查找（不限子团队）
            # 先找所有该项目的子团队，再在这些子团队的成员中查找
            sub_teams_in_project = db.query(SubTeam).filter(SubTeam.project_id == project.id).all()
            sub_team_ids = [st.id for st in sub_teams_in_project]
            member = db.query(SubTeamMember).filter(
                SubTeamMember.name == member_name,
                SubTeamMember.sub_team_id.in_(sub_team_ids) if sub_team_ids else False,
            ).first()
            if not member:
                # 专项负责人可能还没有加入任何子团队，尝试通过项目查找
                # 暂时返回错误提示用户需要先将该负责人加入某个子团队
                return {"ok": False, "error": f"第{line_num}行：成员 '{member_name}' 是专项负责人，但未找到其所属的子团队记录，请先在子团队管理中添加该负责人"}
        else:
            # 普通成员：按子团队名称 + 项目ID 查找
            sub_team = db.query(SubTeam).filter(
                SubTeam.name == sub_team_name,
                SubTeam.project_id == project.id,
            ).first()
            if not sub_team:
                return {"ok": False, "error": f"第{line_num}行：在专项 '{specialty_name}' 下未找到子团队 '{sub_team_name}'"}

            member = db.query(SubTeamMember).filter(
                SubTeamMember.name == member_name,
                SubTeamMember.sub_team_id == sub_team.id,
            ).first()
            if not member:
                return {"ok": False, "error": f"第{line_num}行：在子团队 '{sub_team_name}' 中未找到成员 '{member_name}'"}

        # 检查是否已存在（数据库 + 当前session中待提交的新增对象）
        existing = db.query(MemberMonthlyScore).filter(
            MemberMonthlyScore.sub_team_member_id == member.id,
            MemberMonthlyScore.year == year,
            MemberMonthlyScore.month == month,
        ).first()

        # 同时检查 session identity map 中是否有本批次刚 add 的记录
        if not existing:
            for obj in db.new:
                if isinstance(obj, MemberMonthlyScore):
                    if (obj.sub_team_member_id == member.id and
                        obj.year == year and obj.month == month):
                        existing = obj
                        break

        if existing:
            existing.score = score_val
        else:
            new_record = MemberMonthlyScore(
                sub_team_member_id=member.id,
                year=year,
                month=month,
                score=score_val,
            )
            db.add(new_record)

        return {"ok": True, "error": ""}

    except ValueError as e:
        return {"ok": False, "error": f"第{line_num}行：数据解析错误 - {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"第{line_num}行：未知错误 - {str(e)}"}


# ============================================================
#  专项目标管理 API
# ============================================================

@app.get("/api/goal-dashboard")
async def get_goal_dashboard(
    project_id: int = None,
    year: int = 2026,
    db: Session = Depends(get_db)
):
    """目标看板数据 — 表格形式展示所有目标的目标值/实际值/完成率"""
    import re

    query = db.query(Goal)
    if project_id is not None:
        query = query.filter(Goal.project_id == project_id)
    goals = query.order_by(Goal.project_id, Goal.id).all()

    # 获取所有项目名称
    projects_map = {p.id: p.name for p in db.query(Project).all()}
    # 获取所有关键项目
    kp_map = {kp.id: kp.name for kp in db.query(KeyProject).all()}

    # 确定月份列（4-12月）
    display_months = list(range(4, 13))


    # 构建每个 goal 的 score 映射 { (year, month): GoalScore }
    rows = []
    for g in goals:
        scores_list = (
            db.query(GoalScore)
            .filter(GoalScore.goal_id == g.id, GoalScore.year == year)
            .order_by(GoalScore.month)
            .all()
        )
        score_map = {(s.year, s.month): s for s in scores_list}

        months_data = []
        for m in display_months:
            sc = score_map.get((year, m))
            # monthly_value 存的是目标值
            # actual_value 存的是实际值（独立字段）
            # monthly_rate 存的是完成率
            target_val = sc.monthly_value if sc else None
            actual_val = sc.actual_value if sc else None
            comp_rate = sc.monthly_rate if sc else None

            months_data.append({
                "month": m,
                "monthly_target": target_val,
                "actual_value": actual_val,
                "completion_rate": comp_rate,
                "comment": sc.comment if sc else None,
            })

        # 取最新月份的 GoalScore 中的年度累计值
        latest_sc = None
        for m in reversed(display_months):
            latest_sc = score_map.get((year, m))
            if latest_sc:
                break

        rows.append({
            "id": g.id,
            "project_id": g.project_id,
            "project_name": projects_map.get(g.project_id, ""),
            "goal_name": g.name,
            "key_project_id": g.key_project_id,
            "key_project_name": kp_map.get(g.key_project_id, "") if g.key_project_id else "",
            "description": g.description,
            "unit": g.unit or "",
            "yearly_target": g.yearly_target,
            "yearly_value": latest_sc.yearly_value if latest_sc else None,
            "yearly_rate": latest_sc.yearly_rate if latest_sc else None,
            "months": months_data,
        })

    return {
        "months": display_months,
        "rows": rows,
    }


class GoalCellUpdate(BaseModel):
    """单个单元格更新请求"""
    goal_id: int
    year: int
    month: int
    field: str  # yearly_target | yearly_value | yearly_rate | monthly_target | actual_value | completion_rate
    value: Optional[Union[float, str]] = None


@app.put("/api/goal-dashboard/cell")
async def update_goal_cell(data: GoalCellUpdate, db: Session = Depends(get_db)):
    """更新目标看板中的单个单元格

    字段存储映射:
      - yearly_target  -> Goal.yearly_target
      - yearly_value   -> GoalScore.yearly_value（取最新月份的记录）
      - yearly_rate    -> GoalScore.yearly_rate（取最新月份的记录）
      - monthly_target -> GoalScore.monthly_value
      - actual_value   -> GoalScore.actual_value（独立字段）
      - completion_rate-> GoalScore.monthly_rate（独立字段）
    """
    # 年度目标直接更新 goals 表（兼容文本）
    if data.field == "yearly_target":
        goal = db.query(Goal).filter(Goal.id == data.goal_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail="目标不存在")
        # 直接保存为字符串，支持文本和数字
        if data.value is not None:
            goal.yearly_target = str(data.value).strip()
        else:
            goal.yearly_target = None
        db.commit()
        db.refresh(goal)
        return {"success": True, "id": goal.id}

    # 年度实际值/完成率：写入该年最新月份的 GoalScore 记录
    if data.field in ("yearly_value", "yearly_rate"):
        # 找到该目标当年最新月份的 score 记录
        latest_sc = (
            db.query(GoalScore)
            .filter(GoalScore.goal_id == data.goal_id, GoalScore.year == data.year)
            .order_by(GoalScore.month.desc())
            .first()
        )
        if not latest_sc:
            # 如果没有任何月度记录，创建一个当前月份的
            from datetime import date
            current_month = date.today().month
            latest_sc = GoalScore(
                goal_id=data.goal_id,
                year=data.year,
                month=current_month,
                score=0.0,
            )
            db.add(latest_sc)

        if data.field == "yearly_value":
            # 直接存储字符串值，支持文本内容
            if data.value is not None:
                latest_sc.yearly_value = str(data.value).strip()
            else:
                latest_sc.yearly_value = None
        else:  # yearly_rate — 完成率保持数字
            if isinstance(data.value, (int, float)):
                latest_sc.yearly_rate = float(data.value)
            else:
                try:
                    latest_sc.yearly_rate = float(str(data.value).strip())
                except (ValueError, TypeError):
                    latest_sc.yearly_rate = None

        db.commit()
        db.refresh(latest_sc)
        return {"success": True, "id": latest_sc.id}

    sc = (
        db.query(GoalScore)
        .filter(
            GoalScore.goal_id == data.goal_id,
            GoalScore.year == data.year,
            GoalScore.month == data.month,
        )
        .first()
    )

    if not sc:
        sc = GoalScore(
            goal_id=data.goal_id,
            year=data.year,
            month=data.month,
            score=0.0,
        )
        db.add(sc)

    if data.field == "monthly_target":
        # 目标值存入 monthly_value（兼容文本）
        if data.value is not None:
            sc.monthly_value = str(data.value).strip()
        else:
            sc.monthly_value = None
    elif data.field == "actual_value":
        # 实际值直接存入 actual_value 字段（支持文本）
        if data.value is not None:
            sc.actual_value = str(data.value).strip()
        else:
            sc.actual_value = None
    elif data.field == "completion_rate":
        sc.monthly_rate = data.value

    db.commit()
    db.refresh(sc)
    return {"success": True, "id": sc.id}


@app.get("/api/goal-management")


@app.get("/api/goal-management")
async def get_goal_management(
    project_id: int = None,
    db: Session = Depends(get_db)
):
    """获取专项目标管理列表数据（按项目分组）"""
    query = db.query(Goal)
    if project_id is not None:
        query = query.filter(Goal.project_id == project_id)
    goals = query.order_by(Goal.project_id, Goal.id).all()

    # 按项目分组
    from collections import defaultdict
    project_goals: dict[int, list] = defaultdict(list)

    for g in goals:
        goal_data = build_goal_with_latest(g)
        project_goals[g.project_id].append(goal_data)

    # 构造项目列表
    projects_list = []
    for pid, goal_list in project_goals.items():
        project = db.query(Project).filter(Project.id == pid).first()
        projects_list.append({
            "project_id": pid,
            "project_name": project.name if project else "",
            "goals": [g.model_dump() if hasattr(g, 'model_dump') else g for g in goal_list],
        })

    return GoalManagementResponse(projects=projects_list)


@app.put("/api/goals/{goal_id}/targets")
async def update_goal_targets(
    goal_id: int,
    data: GoalTargetUpdate,
    db: Session = Depends(get_db)
):
    """更新目标的目标值（月度目标、年度目标、单位）"""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")

    if data.monthly_target is not None:
        goal.monthly_target = data.monthly_target
    if data.yearly_target is not None:
        goal.yearly_target = data.yearly_target
    if data.unit is not None:
        goal.unit = data.unit

    db.commit()
    db.refresh(goal)
    return {
        "id": goal.id,
        "monthly_target": goal.monthly_target,
        "yearly_target": goal.yearly_target,
        "unit": goal.unit,
    }


@app.get("/api/goal-management/template")
async def download_goal_template():
    """下载目标值批量导入模板（Excel文件，按月填写目标值）"""
    from fastapi.responses import Response
    import io
    try:
        from openpyxl import Workbook
    except ImportError:
        raise HTTPException(status_code=500, detail="后端缺少openpyxl依赖，请执行: pip install openpyxl")

    wb = Workbook()
    ws = wb.active
    ws.title = "目标值导入模板"

    # 表头 — 带月份列，支持每月不同目标值
    headers = ["项目名称", "目标名称", "年份", "月份", "月度目标值", "年度目标值", "单位"]
    ws.append(headers)

    # 示例数据行（展示同一目标不同月份可设不同值）
    sample_rows = [
        ["SWGT", "MTPF平均故障间隔时间（小时）", 2026, 1, 720.0, 8640.0, "小时"],
        ["SWGT", "MTPF平均故障间隔时间（小时）", 2026, 2, 750.0, 8640.0, "小时"],
        ["SWGT", "MTPF平均故障间隔时间（小时）", 2026, 3, 780.0, 8640.0, "小时"],
        ["SWGT", "缺陷密度（个/KLOC）", 2026, 1, 0.5, 0.3, "个/KLOC"],
        ["SWGT", "缺陷密度（个/KLOC）", 2026, 2, 0.45, 0.3, "个/KLOC"],
        ["中台建设", "需求按期交付率", 2026, 1, 95.0, 95.0, "%"],
    ]
    for row in sample_rows:
        ws.append(row)

    # 样式
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    # 说明行
    note_row = len(sample_rows) + 3
    ws.cell(row=note_row, column=1, value="说明：")
    ws.cell(row=note_row, column=1).font = Font(bold=True, color="C00000")
    notes = [
        "1. 同一目标在不同月份可以设置不同的「月度目标值」（如示例中1/2/3月分别为720/750/780）",
        "2. 「年份」填4位数字如 2026，「月份」填1-12",
        "3. 「年度目标值」和「单位」是目标级固定字段，每月重复填写时以最后一次为准",
        "4. 每行代表一个目标在某一月的配置；如果某月不需要单独设值可以不写该行",
    ]
    for i, note in enumerate(notes):
        cell = ws.cell(row=note_row + 1 + i, column=1, value=note)
        cell.font = Font(color="666666", size=9)
        # 合并说明列
        ws.merge_cells(start_row=note_row + 1 + i, start_column=1, end_row=note_row + 1 + i, end_column=len(headers))

    # 设置列宽
    col_widths = [15, 35, 8, 6, 14, 14, 12]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=goal_target_template.xlsx"},
    )


@app.post("/api/goal-management/batch-import")
async def batch_import_goals(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    """批量导入目标值（支持 Excel .xlsx/.xls 和 CSV 格式）"""
    import io
    import csv as csv_module

    filename = file.filename or ""
    is_csv = filename.endswith('.csv')
    is_excel = filename.endswith('.xlsx') or filename.endswith('.xls')

    if not (is_csv or is_excel):
        raise HTTPException(status_code=400, detail="请上传 .xlsx、.xls 或 .csv 格式的文件")

    content = await file.read()

    # ---- CSV 解析 ----
    if is_csv:
        try:
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                text = content.decode('gbk')
            except Exception:
                raise HTTPException(status_code=400, detail="CSV文件编码无法识别，请使用UTF-8或GBK")
        reader = csv_module.reader(io.StringIO(text))
        rows_raw = list(reader)
        # 跳过空行，从第2行开始是数据（第1行是表头）
        data_rows = [row for row in rows_raw[1:] if any(cell.strip() for cell in row)]
    # ---- Excel 解析 ----
    else:
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise HTTPException(status_code=500, detail="后端缺少openpyxl依赖，请执行: pip install openpyxl")
        wb = load_workbook(io.BytesIO(content))
        ws = wb.active
        excel_rows = list(ws.iter_rows(min_row=2, values_only=True))
        data_rows = [[str(c) if c is not None else "" for c in row] for row in excel_rows if any(c for c in row)]

    if not data_rows:
        raise HTTPException(status_code=400, detail="文件中没有数据行（请从第2行开始填写）")

    success_count = 0
    fail_count = 0
    errors = []

    for idx, row in enumerate(data_rows, start=2):
        try:
            project_name = str(row[0] or "").strip()
            goal_name = str(row[1] or "").strip()

            if not project_name or not goal_name:
                errors.append(f"第{idx}行: 项目名称和目标名称不能为空")
                fail_count += 1
                continue

            # 查找项目
            project = db.query(Project).filter(Project.name == project_name).first()
            if not project:
                errors.append(f"第{idx}行: 项目'{project_name}'不存在")
                fail_count += 1
                continue

            # 查找目标
            goal = db.query(Goal).filter(
                Goal.project_id == project.id,
                Goal.name == goal_name
            ).first()
            if not goal:
                errors.append(f"第{idx}行: 目标'{goal_name}'在项目'{project_name}'下不存在")
                fail_count += 1
                continue

            # ---- 新格式：7列（项目、目标、年份、月份、月度目标值、年度目标值、单位）----
            import re

            year_val = None
            month_val = None
            monthly_target_val = None
            yearly_target_val = None
            unit_val = None

            # 列2=年份, 列3=月份, 列4=月度目标值, 列5=年度目标值, 列6=单位
            if len(row) > 2 and row[2] is not None and str(row[2]).strip():
                try:
                    year_val = int(str(row[2]).strip())
                    if year_val < 2000 or year_val > 2100:
                        raise ValueError()
                except ValueError:
                    errors.append(f"第{idx}行: 年份格式错误，应为4位数字如2026，当前值'{row[2]}'")
                    fail_count += 1
                    continue

            if len(row) > 3 and row[3] is not None and str(row[3]).strip():
                try:
                    month_val = int(str(row[3]).strip())
                    if month_val < 1 or month_val > 12:
                        raise ValueError()
                except ValueError:
                    errors.append(f"第{idx}行: 月份格式错误，应为1-12的数字，当前值'{row[3]}'")
                    fail_count += 1
                    continue

            if len(row) > 4 and row[4] is not None and str(row[4]).strip():
                try:
                    monthly_target_val = float(str(row[4]).strip())
                except ValueError:
                    errors.append(f"第{idx}行: 月度目标值格式错误，应为数字，当前值'{row[4]}'")
                    fail_count += 1
                    continue

            if len(row) > 5 and row[5] is not None and str(row[5]).strip():
                try:
                    yearly_target_val = float(str(row[5]).strip())
                except ValueError:
                    errors.append(f"第{idx}行: 年度目标值格式错误，应为数字，当前值'{row[5]}'")
                    fail_count += 1
                    continue

            if len(row) > 6 and row[6] is not None and str(row[6]).strip():
                unit_val = str(row[6]).strip()

            # 更新Goal表的固定字段（年度目标值、单位）
            if yearly_target_val is not None:
                goal.yearly_target = yearly_target_val
            if unit_val is not None:
                goal.unit = unit_val

            # 如果有年月+月度目标值，写入/更新 GoalScore 的 monthly_value 字段
            if year_val is not None and month_val is not None and monthly_target_val is not None:
                existing_score = db.query(GoalScore).filter(
                    GoalScore.goal_id == goal.id,
                    GoalScore.year == year_val,
                    GoalScore.month == month_val,
                ).first()

                if existing_score:
                    # 更新已有记录的monthly_value
                    existing_score.monthly_value = monthly_target_val
                else:
                    # 创建新的评分记录（只有目标值，暂无得分）
                    new_score = GoalScore(
                        goal_id=goal.id,
                        year=year_val,
                        month=month_val,
                        score=0.0,  # 占位，后续可编辑
                        monthly_value=monthly_target_val,
                    )
                    db.add(new_score)

            success_count += 1
        except ValueError as ve:
            errors.append(f"第{idx}行: 数值格式错误 - {ve}")
            fail_count += 1
        except Exception as e:
            errors.append(f"第{idx}行: {str(e)}")
            fail_count += 1

    db.commit()

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "errors": errors,
    }
async def update_goal_definition(
    goal_id: int,
    data: GoalDefinitionUpdate,
    db: Session = Depends(get_db)
):
    """更新目标的定义（名称和描述）"""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")

    if data.name is not None and data.name.strip():
        goal.name = data.name.strip()
    if data.description is not None:
        goal.description = data.description

    db.commit()
    db.refresh(goal)
    return {
        "id": goal.id,
        "name": goal.name,
        "description": goal.description,
    }
