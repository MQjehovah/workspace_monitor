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