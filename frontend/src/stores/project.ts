import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getProjects, getStats, getProject,
  createGoal, updateGoal, deleteGoal,
  upsertGoalScore, getGoalScores, deleteScore,
  type Project, type Stats, type ProjectWithGoals,
} from '@/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const stats = ref<Stats | null>(null)
  const loading = ref(false)
  const currentProject = ref<ProjectWithGoals | null>(null)

  const fetchProjects = async () => {
    loading.value = true
    try {
      const res = await getProjects()
      projects.value = res.data
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    const res = await getStats()
    stats.value = res.data
  }

  const fetchProjectDetail = async (id: number) => {
    const res = await getProject(id)
    currentProject.value = res.data
    return res.data
  }

  const addGoal = async (projectId: number, name: string, description?: string) => {
    await createGoal(projectId, { name, description })
    await fetchProjectDetail(projectId)
    await fetchProjects()
    await fetchStats()
  }

  const editGoal = async (goalId: number, projectId: number, data: { name?: string; description?: string }) => {
    await updateGoal(goalId, data)
    await fetchProjectDetail(projectId)
  }

  const removeGoal = async (goalId: number, projectId: number) => {
    await deleteGoal(goalId)
    await fetchProjectDetail(projectId)
    await fetchProjects()
    await fetchStats()
  }

  const scoreGoal = async (goalId: number, year: number, month: number, score: number, comment?: string) => {
    await upsertGoalScore(goalId, { year, month, score, comment })
  }

  const fetchGoalScores = async (goalId: number) => {
    const res = await getGoalScores(goalId)
    return res.data
  }

  const removeScore = async (scoreId: number) => {
    await deleteScore(scoreId)
  }

  return {
    projects, stats, loading, currentProject,
    fetchProjects, fetchStats, fetchProjectDetail,
    addGoal, editGoal, removeGoal, scoreGoal, fetchGoalScores, removeScore,
  }
})
