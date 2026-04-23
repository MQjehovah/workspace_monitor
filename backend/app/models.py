from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner = Column(String(50))
    department = Column(String(50))
    progress = Column(Float, default=0.0)
    achievement_rate = Column(Float, default=0.0)
    score = Column(Float, default=0.0)
    status = Column(String(20), default="healthy")
    target_date = Column(Date, nullable=True)
    created_at = Column(Date, default=lambda: datetime.now().date())

    goals = relationship("Goal", back_populates="project", cascade="all, delete-orphan", order_by="Goal.id")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan", order_by="Milestone.due_date")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    created_at = Column(Date, default=lambda: datetime.now().date())

    project = relationship("Project", back_populates="goals")
    scores = relationship("GoalScore", back_populates="goal", cascade="all, delete-orphan",
                          order_by="desc(GoalScore.year), desc(GoalScore.month)")


class GoalScore(Base):
    __tablename__ = "goal_scores"
    __table_args__ = (UniqueConstraint("goal_id", "year", "month", name="uq_goal_year_month"),)

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    comment = Column(String(500))
    created_at = Column(Date, default=lambda: datetime.now().date())

    goal = relationship("Goal", back_populates="scores")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    group_name = Column(String(200))
    due_date = Column(Date, nullable=True)
    event = Column(String(500))
    achieved = Column(Boolean, default=False)
    note = Column(String(500))
    created_at = Column(Date, default=lambda: datetime.now().date())

    project = relationship("Project", back_populates="milestones")
