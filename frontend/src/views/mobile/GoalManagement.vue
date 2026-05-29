<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <router-link to="/mobile" class="back-btn">&larr;</router-link>
      <h1>专项目标</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item project-filter">
        <label>专项</label>
        <select v-model="selectedProject" class="filter-select">
          <option :value="null">全部专项</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="filter-item month-filter">
        <label>月份</label>
        <select v-model="selectedMonth" class="filter-select">
          <option :value="null">全年</option>
          <option v-for="m in months" :key="m" :value="m">{{ m }}月</option>
        </select>
      </div>
    </div>

    <!-- 目标列表 -->
    <div class="content-area">
      <div v-if="filteredRows.length > 0" class="goal-list">
        <div v-for="row in filteredRows" :key="row.id" class="goal-card">
          <div class="goal-header">
            <span class="project-name">{{ row.project_name }}</span>
            <span class="goal-name">{{ row.goal_name }}</span>
            <span v-if="row.description" class="goal-desc-icon" @click.stop="showGoalDesc(row)" title="查看描述">?</span>
          </div>
          <div class="goal-metrics">
            <div class="metric-item">
              <span class="metric-label">{{ isYearly ? '年度目标' : '当月目标' }}</span>
              <span class="metric-value target">{{ displayTarget(row) }}</span>
              <span v-if="row.unit && displayTarget(row) !== '—'" class="unit">{{ row.unit }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">{{ isYearly ? '年度实际' : '当月实际' }}</span>
              <span class="metric-value actual">{{ displayActual(row) }}</span>
              <span v-if="row.unit && displayActual(row) !== '—'" class="unit">{{ row.unit }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">{{ isYearly ? '年完成率' : '月完成率' }}</span>
              <span class="metric-value rate" :style="getRateStyle(displayRate(row))">
                {{ displayRate(row) != null ? displayRate(row)!.toFixed(1) + '%' : '—' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">暂无目标数据</div>
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
    </nav>

    <!-- 目标描述弹窗 -->
    <div v-if="showDescModal" class="desc-modal-mask" @click.self="showDescModal = false">
      <div class="desc-modal-box">
        <h3>{{ descGoalName }}</h3>
        <p class="desc-content">{{ descGoalContent }}</p>
        <button class="desc-close-btn" @click="showDescModal = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()

interface MonthScore {
  month: number
  monthly_target: number | null
  actual_value: number | null
  completion_rate: number | null
  comment: string | null
}

interface GoalRow {
  id: number
  project_id: number
  project_name: string
  goal_name: string
  description: string
  unit: string
  yearly_target: number | null
  yearly_value: number | null
  yearly_rate: number | null
  months: MonthScore[]
}

interface DashboardData {
  months: number[]
  rows: GoalRow[]
}

const dashboardData = ref<DashboardData>({ months: [], rows: [] })
const selectedProject = ref<number | null>(null)
const selectedMonth = ref<number | null>(null)

const descGoalName = ref('')
const descGoalContent = ref('')
const showDescModal = ref(false)

const showGoalDesc = (row: GoalRow) => {
  descGoalName.value = row.goal_name
  descGoalContent.value = row.description || '暂无描述'
  showDescModal.value = true
}

const projects = computed(() => store.projects)
const months = computed(() => dashboardData.value.months)
const isYearly = computed(() => selectedMonth.value === null)

// 筛选后的行
const filteredRows = computed(() => {
  let rows = dashboardData.value.rows
  if (selectedProject.value !== null) {
    rows = rows.filter(r => r.project_id === selectedProject.value)
  }
  return rows
})

// 显示目标值
const displayTarget = (row: GoalRow): string => {
  if (isYearly.value) {
    return row.yearly_target != null ? String(row.yearly_target) : '—'
  }
  const m = row.months.find((mc: MonthScore) => mc.month === selectedMonth.value)
  return m?.monthly_target != null ? String(m.monthly_target) : '—'
}

// 显示实际值
const displayActual = (row: GoalRow): string => {
  if (isYearly.value) {
    return row.yearly_value != null ? String(row.yearly_value) : '—'
  }
  const m = row.months.find((mc: MonthScore) => mc.month === selectedMonth.value)
  return m?.actual_value != null ? String(m.actual_value) : '—'
}

// 显示完成率
const displayRate = (row: GoalRow): number | null => {
  if (isYearly.value) {
    return row.yearly_rate
  }
  const m = row.months.find((mc: MonthScore) => mc.month === selectedMonth.value)
  return m?.completion_rate ?? null
}

const getRateStyle = (rate: number | null) => {
  if (rate === null) return { color: 'var(--text-muted)' }
  if (rate >= 100) return { color: '#27ae60' }
  if (rate >= 80) return { color: '#3b82f6' }
  if (rate >= 60) return { color: '#f39c12' }
  return { color: '#e74c3c' }
}

const loadData = async () => {
  try {
    const res = await api.get('/api/goal-dashboard', { params: { year: 2026 } })
    dashboardData.value = res.data
  } catch (e) {
    console.error('加载目标看板数据失败', e)
  }
}

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
  padding: 12px 16px;
  gap: 12px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-subtle);
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-filter {
  flex: 2;
}

.month-filter {
  flex: 1;
}

.filter-item label {
  font-size: 11px;
  color: var(--text-secondary);
}

.filter-select {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.content-area {
  padding: 12px 16px;
}

.goal-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.goal-card {
  background: var(--bg-card);
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.goal-header {
  margin-bottom: 12px;
}

.project-name {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.goal-name {
  font-size: 14px;
  font-weight: 600;
}

.goal-metrics {
  display: flex;
  gap: 8px;
}

.metric-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.metric-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 15px;
  font-weight: 700;
}

.metric-value.target {
  color: var(--accent-green);
}

.metric-value.actual {
  color: var(--accent-blue);
}

.metric-value.rate {
  font-size: 15px;
  font-weight: 700;
}

.unit {
  font-size: 10px;
  color: var(--text-muted);
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
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-subtle);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 11px;
}

.nav-item.router-link-exact-active {
  color: var(--accent-blue);
}

.nav-icon {
  font-size: 22px;
}

.goal-desc-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 15px; height: 15px; margin-left: 3px; font-size: 10px; font-weight: 700;
  color: var(--accent-blue, #3b82f6); background: rgba(59,130,246,0.12); border-radius: 50%;
  cursor: pointer; vertical-align: middle; flex-shrink: 0;
}
.desc-modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
  padding: 16px;
}
.desc-modal-box {
  background: var(--bg-card, #1e293b); border-radius: 12px; padding: 20px;
  max-width: 400px; width: 100%; max-height: 70vh;
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  display: flex; flex-direction: column;
  box-sizing: border-box;
}
.desc-modal-box h3 { margin: 0 0 12px; font-size: 15px; color: var(--text-primary, #e2e8f0); }
.desc-content {
  line-height: 1.7; color: var(--text-secondary, #94a3b8);
  white-space: pre-wrap; margin: 0 0 16px; font-size: 13px;
  overflow-y: auto; flex: 1;
}
.desc-close-btn {
  padding: 8px 0; background: var(--accent-blue, #3b82f6); color: #fff;
  border: none; border-radius: 8px; cursor: pointer; font-size: 14px; width: 100%;
}
</style>
