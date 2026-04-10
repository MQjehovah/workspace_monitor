import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProjects, getStats, type Project, type Stats } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const stats = ref<Stats | null>(null)
  const loading = ref(false)
  
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
  
  return { projects, stats, loading, fetchProjects, fetchStats }
})