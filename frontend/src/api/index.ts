import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL
})

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
}

export interface Stats {
  total_projects: number
  avg_progress: number
  avg_achievement: number
  avg_score: number
  risk_count: number
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
}

export interface GoalWithLatestScore {
  id: number
  name: string
  description?: string
  latest_score: number | null
  latest_year: number | null
  latest_month: number | null
}

export interface ProjectWithGoals extends Project {
  goals: GoalWithLatestScore[]
}

export const getProjects = () => api.get<Project[]>('/api/projects')
export const getStats = () => api.get<Stats>('/api/stats')
export const getProject = (id: number) => api.get<ProjectWithGoals>(`/api/projects/${id}`)

export const getProjectGoals = (projectId: number) => api.get<Goal[]>(`/api/projects/${projectId}/goals`)
export const createGoal = (projectId: number, data: { name: string; description?: string }) =>
  api.post<Goal>(`/api/projects/${projectId}/goals`, data)
export const updateGoal = (goalId: number, data: { name?: string; description?: string }) =>
  api.put<Goal>(`/api/goals/${goalId}`, data)
export const deleteGoal = (goalId: number) => api.delete(`/api/goals/${goalId}`)

export const getGoalScores = (goalId: number) => api.get<GoalScore[]>(`/api/goals/${goalId}/scores`)
export const upsertGoalScore = (goalId: number, data: { year: number; month: number; score: number; comment?: string }) =>
  api.post<GoalScore>(`/api/goals/${goalId}/scores`, data)
export const deleteScore = (scoreId: number) => api.delete(`/api/scores/${scoreId}`)

export const seedData = () => api.post('/api/seed')
