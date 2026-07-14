<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <router-link to="/mobile" class="back-btn">&larr;</router-link>
      <h1>成员专项绩效</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>专项</label>
        <select v-model="selectedProject" class="filter-select">
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label>子团队</label>
        <select v-model="selectedSubTeam" class="filter-select">
          <option v-for="st in availableSubTeams" :key="st.name" :value="st.name">{{ st.name }}</option>
        </select>
      </div>
      <div class="filter-item" style="flex: 0.7;">
        <label>月份</label>
        <select v-model="selectedMonth" class="filter-select">
          <option v-for="m in months" :key="m.label" :value="m.label">{{ m.month }}月</option>
        </select>
      </div>
    </div>

    <!-- 数据列表 -->
    <div class="content-area">
      <div v-if="filteredRows.length > 0" class="member-list">
        <div v-for="row in filteredRows" :key="row.member_id" class="member-card">
          <div class="member-row">
            <span class="member-name">{{ row.member_name }}</span>
            <span v-if="getScore(row) !== null" class="score-badge" :style="getScoreBadgeStyle(getScore(row)!)">
              {{ getScore(row) }}分
            </span>
            <span v-else class="score-empty">—</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">暂无数据</div>
    </div>

    <nav class="bottom-nav">
      <router-link to="/mobile" class="nav-item">
        <span class="nav-icon">📊</span>
        <span>总览</span>
      </router-link>
      <router-link to="/mobile/performance" class="nav-item">
        <span class="nav-icon">👥</span>
        <span>绩效</span>
      </router-link>
      <router-link to="/mobile/goals" class="nav-item">
        <span class="nav-icon">🎯</span>
        <span>目标</span>
      </router-link>
      <router-link to="/mobile/key-projects" class="nav-item">
        <span class="nav-icon">🔑</span>
        <span>关键项目</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '@/api'
import { useProjectStore } from '@/stores/project'
const store = useProjectStore()

interface ScoreItem {
  year: number
  month: number
  label: string
  score: number | null
  id: number | null
  comment: string
}

interface PerfRow {
  member_id: number
  member_name: string
  role: string
  project_id: number
  project_name: string
  sub_team_name: string
  specialty_name: string
  scores: ScoreItem[]
}

interface PerfData {
  months: { year: number; month: number; label: string }[]
  rows: PerfRow[]
  total: number
}

const perfData = ref<PerfData>({ months: [], rows: [], total: 0 })
const selectedProject = ref<number>(0)
const selectedSubTeam = ref<string>('')
const selectedMonth = ref<string>('')

const projects = computed(() => store.projects)

// 根据选中专项筛选子团队
const availableSubTeams = computed(() => {
  const map = new Map<string, { name: string }>()
  for (const row of perfData.value.rows) {
    if (row.project_id === selectedProject.value && row.sub_team_name && !map.has(row.sub_team_name)) {
      map.set(row.sub_team_name, { name: row.sub_team_name })
    }
  }
  return Array.from(map.values())
})

const months = computed(() => perfData.value.months)

// 筛选后的行
const filteredRows = computed(() => {
  let rows = perfData.value.rows
  rows = rows.filter(r => r.project_id === selectedProject.value)
  if (selectedSubTeam.value) {
    rows = rows.filter(r => r.sub_team_name === selectedSubTeam.value)
  }
  return rows
})

const getScore = (row: PerfRow): number | null => {
  const sc = row.scores.find(s => s.label === selectedMonth.value)
  return sc?.score ?? null
}

const scoreColors: Record<number, string> = {
  1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#22c55e', 5: '#3b82f6',
}

const getScoreBadgeStyle = (score: number) => ({
  background: scoreColors[score] + '18',
  color: scoreColors[score],
  borderColor: scoreColors[score],
})

const loadData = async () => {
  try {
    const res = await api.get('/api/member-performance')
    perfData.value = res.data

    // 默认选中第一个专项、第一个子团队、最新有数据的月份
    if (store.projects.length > 0 && !selectedProject.value) {
      selectedProject.value = store.projects[0].id
    }
    const teams = availableSubTeams.value
    if (teams.length > 0 && !selectedSubTeam.value) {
      selectedSubTeam.value = teams[0].name
    }
    if (res.data.months.length > 0 && !selectedMonth.value) {
      let latestMonth = res.data.months[res.data.months.length - 1]
      for (let i = res.data.months.length - 1; i >= 0; i--) {
        const m = res.data.months[i]
        const hasData = res.data.rows.some(row =>
          row.scores.find((s: ScoreItem) => s.label === m.label && s.score != null)
        )
        if (hasData) {
          latestMonth = m
          break
        }
      }
      selectedMonth.value = latestMonth.label
    }
  } catch (e) {
    console.error('加载成员绩效数据失败', e)
  }
}

// 切换专项时，如果当前子团队不在新专项下，选中第一个子团队
watch(selectedProject, () => {
  const teams = availableSubTeams.value
  if (teams.length > 0) {
    const exists = teams.some(st => st.name === selectedSubTeam.value)
    if (!exists) {
      selectedSubTeam.value = teams[0].name
    }
  }
})

onMounted(() => {
  store.fetchProjects()
  loadData()
})
</script>

<style scoped>
.mobile-page {
  max-width: 390px;
  margin: 0 auto;
  background: var(--bg-primary);
  min-height: 100vh;
  padding-bottom: 80px;
}

.mobile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--bg-secondary);
}

.mobile-header h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.back-btn {
  color: var(--text-primary);
  text-decoration: none;
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  background: var(--accent-blue);
  color: white;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  padding: 10px 12px;
  gap: 8px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

.filter-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.filter-item label {
  font-size: 10px;
  color: var(--text-secondary);
}

.filter-select {
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
  width: 100%;
}

.content-area {
  padding: 12px 16px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.member-card {
  background: var(--bg-card);
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
}

.member-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.member-name {
  font-size: 14px;
  font-weight: 600;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 12px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 14px;
  border: 1px solid;
}

.score-empty {
  color: var(--text-muted);
  font-size: 14px;
}

.empty-hint {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  max-width: 390px;
  margin: 0 auto;
  display: flex;
  justify-content: space-around;
  padding: 10px 8px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-subtle);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 10px;
}

.nav-item.router-link-exact-active {
  color: var(--accent-blue);
}

.nav-icon {
  font-size: 20px;
}
</style>
