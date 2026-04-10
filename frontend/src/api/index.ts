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

export const getProjects = () => api.get<Project[]>('/api/projects')
export const getStats = () => api.get<Stats>('/api/stats')
export const getProject = (id: number) => api.get<Project>(`/api/projects/${id}`)