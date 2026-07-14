import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL
})

export { api }

export interface Project {
  id: number
  name: string
  owner: string
  department: string
  progress: number
  achievement_rate: number
  score: number
  status: string
  target_date?: string
  special?: number
}

export interface Stats {
  total_projects: number
  avg_progress: number
  avg_achievement: number
  avg_score: number
  risk_count: number
  achieved_teams: number
  total_teams: number
}

export interface Goal {
  id: number
  project_id: number
  name: string
  description?: string
  scores: GoalScore[]
}

export interface GoalScore {
  id: number
  goal_id: number
  year: number
  month: number
  score: number
  comment?: string
  monthly_value?: string | null
  actual_value?: string | null
  monthly_rate?: number | null
  yearly_value?: string | null
  yearly_rate?: number | null
  gap_analysis?: string | null
}

export interface GoalWithLatestScore {
  id: number
  name: string
  project_id?: number
  project_name?: string | null
  key_project_id?: number | null
  description?: string
  unit?: string | null
  monthly_target?: number | null
  yearly_target?: number | null
  latest_score: number | null
  latest_year: number | null
  latest_month: number | null
  latest_comment: string | null
  latest_monthly_value?: string | null
  latest_monthly_actual?: string | null
  latest_monthly_rate?: number | null
  latest_yearly_value?: string | null
  latest_yearly_rate?: number | null
  latest_gap_analysis?: string | null
}

export interface Milestone {
  id: number
  project_id: number
  group_name: string | null
  due_date: string | null
  event: string | null
  achieved: boolean
  note: string | null
}

export interface MonthlyReport {
  id: number
  project_id: number
  year: number
  month: number
  content: string
  pdf_path: string | null
}

export interface SubTeamMember {
  id: number
  sub_team_id: number
  name: string
  role: string | null
}

export interface SubTeamRating {
  id: number
  sub_team_id: number
  year: number
  month: number
  rating: string
  comment: string | null
}

export interface SubTeam {
  id: number
  project_id: number
  name: string
  leader: string | null
  members: SubTeamMember[]
  ratings: SubTeamRating[]
}

export interface KeyProject {
  id: number
  name: string
  owner: string
  start_date: string | null
  end_date: string | null
  progress: string
  status: string
  score?: number | null
}

export interface ProjectWithGoals extends Project {
  goals: GoalWithLatestScore[]
  milestones: Milestone[]
  reports: MonthlyReport[]
  sub_teams: SubTeam[]
}

export const getProjects = () => api.get<Project[]>('/api/projects')
export const getSpecialProjects = () => api.get<Project[]>('/api/special-projects')
export const getStats = () => api.get<Stats>('/api/stats')
export const getProject = (id: number) => api.get<ProjectWithGoals>(`/api/projects/${id}`)
export const updateProject = (id: number, data: { name?: string; owner?: string; department?: string; target_date?: string; progress?: number }) =>
  api.put<ProjectWithGoals>(`/api/projects/${id}`, data)
export const createProject = (data: { name: string; owner?: string; department?: string; target_date?: string; special?: number }) =>
  api.post<ProjectWithGoals>('/api/projects', data)
export const deleteProject = (id: number) => api.delete(`/api/projects/${id}`)

export const getKeyProjects = () => api.get<KeyProject[]>('/api/key-projects')
export const getKeyProject = (id: number) => api.get<KeyProject & { goals: GoalWithLatestScore[] }>(`/api/key-projects/${id}`)
export const createKeyProject = (data: { name: string; owner?: string; start_date?: string; end_date?: string; progress?: string; status?: string }) =>
  api.post<KeyProject>('/api/key-projects', data)
export const updateKeyProject = (id: number, data: { name?: string; owner?: string; start_date?: string; end_date?: string; progress?: string; status?: string }) =>
  api.put<KeyProject>(`/api/key-projects/${id}`, data)
export const deleteKeyProject = (id: number) => api.delete(`/api/key-projects/${id}`)

export const getProjectGoals = (projectId: number) => api.get<Goal[]>(`/api/projects/${projectId}/goals`)
export const createGoal = (projectId: number, data: { name: string; description?: string; key_project_id?: number | null }) =>
  api.post<Goal>(`/api/projects/${projectId}/goals`, data)
export const updateGoal = (goalId: number, data: { name?: string; description?: string; unit?: string; key_project_id?: number | null }) =>
  api.put<Goal>(`/api/goals/${goalId}`, data)
export const deleteGoal = (goalId: number) => api.delete(`/api/goals/${goalId}`)

export const getGoalScores = (goalId: number) => api.get<GoalScore[]>(`/api/goals/${goalId}/scores`)
export const upsertGoalScore = (goalId: number, data: { year: number; month: number; score: number; comment?: string; monthly_value?: string | null; actual_value?: string | null; monthly_rate?: number | null; yearly_value?: string | null; yearly_rate?: number | null; gap_analysis?: string | null }) =>
  api.post<GoalScore>(`/api/goals/${goalId}/scores`, data)
export const deleteScore = (scoreId: number) => api.delete(`/api/scores/${scoreId}`)

export const getMilestones = (projectId: number) => api.get<Milestone[]>(`/api/projects/${projectId}/milestones`)
export const createMilestone = (projectId: number, data: { group_name?: string; due_date?: string; event?: string }) =>
  api.post<Milestone>(`/api/projects/${projectId}/milestones`, data)
export const updateMilestone = (id: number, data: { group_name?: string; due_date?: string; event?: string; achieved?: boolean; note?: string }) =>
  api.put<Milestone>(`/api/milestones/${id}`, data)
export const deleteMilestone = (id: number) => api.delete(`/api/milestones/${id}`)

export const getReports = (projectId: number) => api.get<MonthlyReport[]>(`/api/projects/${projectId}/reports`)
export const createReport = (projectId: number, data: { year: number; month: number; content: string }) =>
  api.post<MonthlyReport>(`/api/projects/${projectId}/reports`, data)
export const updateReport = (reportId: number, data: { content: string }) =>
  api.put<MonthlyReport>(`/api/reports/${reportId}`, data)
export const uploadReportPdf = (reportId: number, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post<MonthlyReport>(`/api/reports/${reportId}/pdf`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}
export const deleteReportPdf = (reportId: number) => api.delete(`/api/reports/${reportId}/pdf`)
export const deleteReport = (reportId: number) => api.delete(`/api/reports/${reportId}`)

export const getSubTeams = (projectId: number) => api.get<SubTeam[]>(`/api/projects/${projectId}/subteams`)
export const createSubTeam = (projectId: number, data: { name: string; leader?: string; members?: { name: string; role?: string }[] }) =>
  api.post<SubTeam>(`/api/projects/${projectId}/subteams`, data)
export const updateSubTeam = (subteamId: number, data: { name?: string; leader?: string }) =>
  api.put<SubTeam>(`/api/subteams/${subteamId}`, data)
export const deleteSubTeam = (subteamId: number) => api.delete(`/api/subteams/${subteamId}`)
export const addSubTeamMember = (subteamId: number, data: { name: string; role?: string }) =>
  api.post<SubTeamMember>(`/api/subteams/${subteamId}/members`, data)
export const updateSubTeamMember = (memberId: number, data: { name?: string; role?: string }) =>
  api.put<SubTeamMember>(`/api/subteam-members/${memberId}`, data)
export const deleteSubTeamMember = (memberId: number) => api.delete(`/api/subteam-members/${memberId}`)
export const upsertSubTeamRating = (subteamId: number, data: { year: number; month: number; rating: string; comment?: string }) =>
  api.post<SubTeamRating>(`/api/subteams/${subteamId}/ratings`, data)
export const getSubTeamRatings = (subteamId: number) => api.get<SubTeamRating[]>(`/api/subteams/${subteamId}/ratings`)
export const deleteSubTeamRating = (ratingId: number) => api.delete(`/api/subteam-ratings/${ratingId}`)

export const seedData = () => api.post('/api/seed')

// ====== 成员每月评分 ======
export interface MemberPerformanceRow {
  member_id: number
  member_name: string
  sub_team_id: number
  sub_team_name: string
  scores: Record<string, number | null>
}

export const getMemberPerformance = (projectId?: number) =>
  api.get<MemberPerformanceRow[]>('/api/member-performance', {
    params: projectId ? { project_id: projectId } : undefined,
  })
