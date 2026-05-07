from fastapi import FastAPI, Depends, HTTPException, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import os
import uuid
from app.database import get_db, engine, Base, DATA_DIR
from app.models import Project, Goal, GoalScore, Milestone, MonthlyReport, SubTeam, SubTeamMember, SubTeamRating
from app.schemas import (
    ProjectCreate, ProjectUpdate, Project as ProjectSchema, StatsResponse,
    GoalCreate, GoalUpdate, GoalOut,
    GoalScoreCreate, GoalScoreOut, ProjectWithGoals, GoalWithLatestScore,
    MilestoneCreate, MilestoneUpdate, MilestoneOut,
    MonthlyReportCreate, MonthlyReportUpdate, MonthlyReportOut,
    SubTeamCreate, SubTeamUpdate, SubTeamOut,
    SubTeamMemberCreate, SubTeamMemberOut,
    SubTeamRatingCreate, SubTeamRatingOut,
)
from app.websocket import manager

UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


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

    if project.score >= 80:
        project.status = "healthy"
    elif project.score >= 60:
        project.status = "warning"
    else:
        project.status = "risk"
    project.achievement_rate = round(project.score, 1)
    db.commit()


def build_goal_with_latest(goal: Goal) -> GoalWithLatestScore:
    latest_score = None
    latest_year = None
    latest_month = None
    latest_comment = None
    if goal.scores:
        s = goal.scores[0]
        latest_score = s.score
        latest_year = s.year
        latest_month = s.month
        latest_comment = s.comment
    return GoalWithLatestScore(
        id=goal.id,
        name=goal.name,
        description=goal.description,
        latest_score=latest_score,
        latest_year=latest_year,
        latest_month=latest_month,
        latest_comment=latest_comment,
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
