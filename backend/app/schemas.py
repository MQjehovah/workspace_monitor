from pydantic import BaseModel
from datetime import date
from typing import Optional


class ProjectBase(BaseModel):
    name: str
    owner: Optional[str] = None
    department: Optional[str] = None
    progress: float = 0.0
    achievement_rate: float = 0.0
    score: float = 0.0
    status: str = "healthy"
    target_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    owner: Optional[str] = None
    department: Optional[str] = None
    progress: Optional[float] = None
    achievement_rate: Optional[float] = None
    target_date: Optional[date] = None


class Project(ProjectBase):
    id: int

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_projects: int
    avg_progress: float
    avg_achievement: float
    avg_score: float
    risk_count: int


class GoalBase(BaseModel):
    name: str
    description: Optional[str] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GoalScoreBase(BaseModel):
    year: int
    month: int
    score: float
    comment: Optional[str] = None


class GoalScoreCreate(GoalScoreBase):
    pass


class GoalScoreOut(GoalScoreBase):
    id: int
    goal_id: int

    class Config:
        from_attributes = True


class GoalOut(GoalBase):
    id: int
    project_id: int
    scores: list[GoalScoreOut] = []

    class Config:
        from_attributes = True


class GoalWithLatestScore(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    latest_score: Optional[float] = None
    latest_year: Optional[int] = None
    latest_month: Optional[int] = None
    latest_comment: Optional[str] = None


class MilestoneBase(BaseModel):
    group_name: Optional[str] = None
    due_date: Optional[date] = None
    event: Optional[str] = None


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    group_name: Optional[str] = None
    due_date: Optional[date] = None
    event: Optional[str] = None
    achieved: Optional[bool] = None
    note: Optional[str] = None


class MilestoneOut(MilestoneBase):
    id: int
    project_id: int
    achieved: bool = False
    note: Optional[str] = None

    class Config:
        from_attributes = True


class MonthlyReportBase(BaseModel):
    year: int
    month: int
    content: str = ""


class MonthlyReportCreate(MonthlyReportBase):
    pass


class MonthlyReportUpdate(BaseModel):
    content: str = ""


class MonthlyReportOut(MonthlyReportBase):
    id: int
    project_id: int
    pdf_path: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectWithGoals(Project):
    goals: list[GoalWithLatestScore] = []
    milestones: list[MilestoneOut] = []
    reports: list[MonthlyReportOut] = []
    sub_teams: list["SubTeamOut"] = []

    class Config:
        from_attributes = True


class SubTeamMemberBase(BaseModel):
    name: str
    role: Optional[str] = None


class SubTeamMemberCreate(SubTeamMemberBase):
    pass


class SubTeamMemberOut(SubTeamMemberBase):
    id: int
    sub_team_id: int

    class Config:
        from_attributes = True


class SubTeamRatingBase(BaseModel):
    year: int
    month: int
    rating: str
    comment: Optional[str] = None


class SubTeamRatingCreate(SubTeamRatingBase):
    pass


class SubTeamRatingOut(SubTeamRatingBase):
    id: int
    sub_team_id: int

    class Config:
        from_attributes = True


class SubTeamBase(BaseModel):
    name: str
    leader: Optional[str] = None


class SubTeamCreate(SubTeamBase):
    members: list[SubTeamMemberCreate] = []


class SubTeamUpdate(BaseModel):
    name: Optional[str] = None
    leader: Optional[str] = None


class SubTeamOut(SubTeamBase):
    id: int
    project_id: int
    members: list[SubTeamMemberOut] = []
    ratings: list[SubTeamRatingOut] = []

    class Config:
        from_attributes = True


ProjectWithGoals.model_rebuild()
