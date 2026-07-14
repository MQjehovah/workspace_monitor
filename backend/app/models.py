from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, UniqueConstraint, DateTime, func
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
    special = Column(Integer, default=0)
    created_at = Column(Date, default=lambda: datetime.now().date())

    goals = relationship("Goal", back_populates="project", cascade="all, delete-orphan", order_by="Goal.id")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan", order_by="Milestone.due_date")
    reports = relationship("MonthlyReport", back_populates="project", cascade="all, delete-orphan", order_by="desc(MonthlyReport.year), desc(MonthlyReport.month)")
    sub_teams = relationship("SubTeam", back_populates="project", cascade="all, delete-orphan", order_by="SubTeam.id")


class KeyProject(Base):
    __tablename__ = "key_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner = Column(String(50))
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    progress = Column(String(20), default="在行")
    status = Column(String(20), default="healthy")
    created_at = Column(Date, default=lambda: datetime.now().date())

    goals = relationship("Goal", back_populates="key_project", order_by="Goal.id")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key_project_id = Column(Integer, ForeignKey("key_projects.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    monthly_target = Column(String(100), nullable=True, comment="月度目标值")
    yearly_target = Column(String(100), nullable=True, comment="年度目标值")
    unit = Column(String(50), default="", comment="单位")
    created_at = Column(Date, default=lambda: datetime.now().date())

    project = relationship("Project", back_populates="goals")
    key_project = relationship("KeyProject", back_populates="goals")
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
    monthly_value = Column(String(100), nullable=True, comment="当月目标值")
    actual_value = Column(String(100), nullable=True, comment="当月实际值")
    monthly_rate = Column(Float, nullable=True, comment="当月完成率(%)")
    yearly_value = Column(String(100), nullable=True, comment="年度累计实际值")
    yearly_rate = Column(Float, nullable=True, comment="年度完成率(%)")
    gap_analysis = Column(String(500), nullable=True, comment="差距分析")
    created_at = Column(Date, default=lambda: datetime.now().date())

    goal = relationship("Goal", back_populates="scores")


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"
    __table_args__ = (UniqueConstraint("project_id", "year", "month", name="uq_report_project_year_month"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    content = Column(String(50000), default="")
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(Date, default=lambda: datetime.now().date())
    updated_at = Column(Date, default=lambda: datetime.now().date(), onupdate=lambda: datetime.now().date())

    project = relationship("Project", back_populates="reports")


class SubTeam(Base):
    __tablename__ = "sub_teams"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    leader = Column(String(50))
    specialty_name = Column(String(100), comment="专项名称/专业方向")
    created_at = Column(Date, default=lambda: datetime.now().date())

    project = relationship("Project", back_populates="sub_teams")
    members = relationship("SubTeamMember", back_populates="sub_team", cascade="all, delete-orphan", order_by="SubTeamMember.id")
    ratings = relationship("SubTeamRating", back_populates="sub_team", cascade="all, delete-orphan",
                           order_by="desc(SubTeamRating.year), desc(SubTeamRating.month)")


class SubTeamMember(Base):
    __tablename__ = "sub_team_members"

    id = Column(Integer, primary_key=True, index=True)
    sub_team_id = Column(Integer, ForeignKey("sub_teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(String(50))

    sub_team = relationship("SubTeam", back_populates="members")


class SubTeamRating(Base):
    __tablename__ = "sub_team_ratings"
    __table_args__ = (UniqueConstraint("sub_team_id", "year", "month", name="uq_subteam_rating_year_month"),)

    id = Column(Integer, primary_key=True, index=True)
    sub_team_id = Column(Integer, ForeignKey("sub_teams.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    rating = Column(String(10), nullable=False)
    comment = Column(String(500))
    created_at = Column(Date, default=lambda: datetime.now().date())

    sub_team = relationship("SubTeam", back_populates="ratings")


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


class MemberMonthlyScore(Base):
    __tablename__ = "member_monthly_scores"
    __table_args__ = (UniqueConstraint("sub_team_member_id", "year", "month", name="uq_member_score"),)

    id = Column(Integer, primary_key=True, index=True)
    sub_team_member_id = Column(Integer, ForeignKey("sub_team_members.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False, comment="1-5分制")
    comment = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    member = relationship("SubTeamMember")
