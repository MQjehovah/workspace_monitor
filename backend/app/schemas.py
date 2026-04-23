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


class ProjectWithGoals(Project):
    goals: list[GoalWithLatestScore] = []

    class Config:
        from_attributes = True
