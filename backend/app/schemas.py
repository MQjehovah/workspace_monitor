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
    special: int = 0


class KeyProjectBase(BaseModel):
    name: str
    owner: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress: str = "在行"
    status: str = "healthy"


class KeyProjectCreate(KeyProjectBase):
    pass


class KeyProjectUpdate(BaseModel):
    name: Optional[str] = None
    owner: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress: Optional[str] = None
    status: Optional[str] = None


class KeyProjectOut(KeyProjectBase):
    id: int
    score: Optional[float] = None

    class Config:
        from_attributes = True


class KeyProjectGoal(BaseModel):
    id: int
    name: str
    project_id: int
    project_name: str = ""
    description: Optional[str] = None
    unit: Optional[str] = None
    monthly_target: Optional[str] = None
    yearly_target: Optional[str] = None
    latest_score: Optional[float] = None
    latest_year: Optional[int] = None
    latest_month: Optional[int] = None
    latest_monthly_value: Optional[str] = None
    latest_monthly_actual: Optional[str] = None
    latest_monthly_rate: Optional[float] = None
    latest_yearly_value: Optional[str] = None
    latest_yearly_rate: Optional[float] = None
    latest_gap_analysis: Optional[str] = None

    class Config:
        from_attributes = True


class KeyProjectWithGoals(KeyProjectOut):
    goals: list[KeyProjectGoal] = []

    class Config:
        from_attributes = True


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
    achieved_teams: int
    total_teams: int


class GoalBase(BaseModel):
    name: str
    description: Optional[str] = None
    monthly_target: Optional[str] = None
    yearly_target: Optional[str] = None
    unit: str = ""


class GoalCreate(GoalBase):
    key_project_id: Optional[int] = None


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    monthly_target: Optional[str] = None
    yearly_target: Optional[str] = None
    unit: Optional[str] = None
    key_project_id: Optional[int] = None


class GoalScoreBase(BaseModel):
    year: int
    month: int
    score: float
    comment: Optional[str] = None
    monthly_value: Optional[str] = None
    actual_value: Optional[str] = None
    monthly_rate: Optional[float] = None
    yearly_value: Optional[str] = None
    yearly_rate: Optional[float] = None
    gap_analysis: Optional[str] = None


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
    project_id: int = 0
    project_name: Optional[str] = None
    key_project_id: Optional[int] = None
    description: Optional[str] = None
    monthly_target: Optional[str] = None
    yearly_target: Optional[str] = None
    unit: Optional[str] = ""
    latest_score: Optional[float] = None
    latest_year: Optional[int] = None
    latest_month: Optional[int] = None
    latest_comment: Optional[str] = None
    latest_monthly_value: Optional[str] = None
    latest_monthly_actual: Optional[str] = None
    latest_monthly_rate: Optional[float] = None
    latest_yearly_value: Optional[str] = None
    latest_yearly_rate: Optional[float] = None
    latest_gap_analysis: Optional[str] = None


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


class SubTeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None


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


# ==================== 成员每月评级 Schema ====================

class MemberMonthlyScoreBase(BaseModel):
    year: int
    month: int
    score: int  # 1-5分制
    comment: Optional[str] = ""


class MemberMonthlyScoreCreate(MemberMonthlyScoreBase):
    pass


class MemberMonthlyScoreUpdate(BaseModel):
    score: Optional[int] = None
    comment: Optional[str] = None


class MemberMonthlyScoreOut(MemberMonthlyScoreBase):
    id: int
    sub_team_member_id: int

    class Config:
        from_attributes = True


class MemberPerformanceRow(BaseModel):
    """成员绩效行 - 用于列表展示"""
    member_id: int
    member_name: str
    member_role: Optional[str] = None
    sub_team_id: int
    sub_team_name: str
    project_id: int
    project_name: str
    scores: list[MemberMonthlyScoreOut] = []


class MemberPerformanceResponse(BaseModel):
    """成员绩效查询响应"""
    total: int
    rows: list[MemberPerformanceRow] = []


class BatchImportResult(BaseModel):
    """批量导入结果"""
    success_count: int
    fail_count: int
    errors: list[str] = []


# ==================== 目标管理扩展 Schema ====================

class GoalTargetUpdate(BaseModel):
    """目标值更新"""
    monthly_target: Optional[float] = None
    yearly_target: Optional[float] = None


class GoalDefinitionUpdate(BaseModel):
    """目标定义更新"""
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None


class GoalManagementItem(BaseModel):
    """目标管理页面的单个项目-目标项"""
    project_id: int
    project_name: str
    goals: list[GoalWithLatestScore] = []


class GoalManagementResponse(BaseModel):
    """目标管理页面响应"""
    projects: list[GoalManagementItem] = []


# ========== 目标看板（Dashboard）数据结构 =========

class GoalMonthScore(BaseModel):
    """目标看板中单月数据"""
    month: int
    monthly_target: Optional[float] = None   # 月度目标值
    actual_value: Optional[str] = None       # 实际值
    completion_rate: Optional[float] = None  # 完成率(%)
    comment: Optional[str] = None            # 备注


class GoalDashboardRow(BaseModel):
    """目标看板中的单行（一个goal）"""
    id: int
    project_id: int
    project_name: str
    goal_name: str
    unit: str = ""
    yearly_target: Optional[float] = None    # 年度目标值
    months: list[GoalMonthScore] = []        # 各月数据


class GoalDashboardResponse(BaseModel):
    """目标看板响应"""
    months: list[int] = []                    # 显示的月份列表，如 [4,5,6,7,8,9,10,11,12]
    rows: list[GoalDashboardRow] = []         # 所有目标的行数据


ProjectWithGoals.model_rebuild()
