<template>
  <div class="dashboard">
    <header class="nav-header">
      <div class="nav-title">
        <h1>重大项目全景监控看板</h1>
        <span class="version">V2.0</span>
      </div>
      <div class="nav-actions">
        <span class="update-time">数据更新：{{ currentTime }}</span>
        <button @click="refresh" class="btn-refresh">手动刷新</button>
        <router-link to="/admin" class="btn-admin">后台管理</router-link>
        <button class="btn-export">导出报告</button>
      </div>
    </header>

    <!-- KPI Cards -->
    <section class="kpi-section">
      <h2 class="section-title">关键指标总览</h2>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-header">
            <span>重大项目总数</span>
            <div class="kpi-icon">📁</div>
          </div>
          <div class="kpi-value">{{ stats?.total_projects || 0 }}</div>
          <div class="kpi-trend up">+2 较上月</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-header">
            <span>平均进度</span>
            <div class="kpi-icon green">📊</div>
          </div>
          <div class="kpi-value">{{ (stats?.avg_progress || 0).toFixed(1) }}%</div>
          <div class="progress-bar">
            <div class="progress-fill green" :style="{ width: (stats?.avg_progress || 0) + '%' }"></div>
          </div>
          <div class="kpi-trend up">环比 +5%</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-header">
            <span>平均考核得分</span>
            <div class="kpi-icon orange">🏆</div>
          </div>
          <div class="kpi-value">{{ (stats?.avg_score || 0).toFixed(1) }}</div>
          <div class="kpi-trend">较上月持平</div>
        </div>
        <div class="kpi-card risk">
          <div class="kpi-header">
            <span>风险项目数</span>
            <div class="kpi-icon red">⚠️</div>
          </div>
          <div class="kpi-value red">{{ stats?.risk_count || 0 }}</div>
          <div class="kpi-trend red">超过预警阈值</div>
        </div>
      </div>
    </section>

    <!-- Project Table -->
    <section class="table-section">
      <h2 class="section-title">重大项目明细</h2>
      <table class="project-table">
        <thead>
          <tr>
            <th>项目名称</th>
            <th>进度</th>
            <th>考核得分</th>
            <th>等级</th>
            <th>健康状态</th>
            <th>负责人</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projects" :key="project.id">
            <td>{{ project.name }}</td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="progress-fill" :class="getProgressClass(project.progress)" :style="{ width: project.progress + '%' }"></div>
                </div>
                <span>{{ project.progress }}%</span>
              </div>
            </td>
            <td :class="{ red: project.score < 70 }">{{ project.score }}</td>
            <td>{{ getGrade(project.score) }}</td>
            <td>
              <span class="status-badge" :class="project.status">{{ getStatusText(project.status) }}</span>
            </td>
            <td>{{ project.owner }}</td>
            <td><button class="btn-detail" @click="openDetail(project.id)">详情</button></td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Goal Score Detail Panel -->
    <section v-if="selectedProject" class="goal-section">
      <div class="goal-header">
        <h2 class="section-title">{{ selectedProject.name }} — 详情</h2>
        <button class="btn-close" @click="selectedProject = null">关闭</button>
      </div>
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: detailTab === 'goals' }" @click="detailTab = 'goals'">目标评分</button>
        <button class="tab-btn" :class="{ active: detailTab === 'milestones' }" @click="detailTab = 'milestones'">项目里程碑</button>
      </div>

      <!-- Goals Tab -->
      <div v-if="detailTab === 'goals'" class="tab-content">
        <div class="goal-cards">
          <div v-for="goal in selectedProject.goals" :key="goal.id" class="goal-card">
            <div class="goal-name">{{ goal.name }}</div>
            <div class="goal-score-row">
              <span class="goal-score-label">最新评分</span>
              <span class="goal-score-value" :class="getScoreClass(goal.latest_score)">
                {{ goal.latest_score !== null ? goal.latest_score.toFixed(1) : '未评分' }}
              </span>
              <span v-if="goal.latest_year && goal.latest_month" class="goal-score-date">
                ({{ goal.latest_year }}年{{ goal.latest_month }}月)
              </span>
            </div>
            <div class="goal-score-bar">
              <div class="progress-bar">
                <div class="progress-fill" :class="getScoreBarClass(goal.latest_score)" :style="{ width: (goal.latest_score || 0) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
        <div class="goal-summary">
          <span class="summary-label">项目综合得分</span>
          <span class="summary-value">{{ selectedProject.score.toFixed(1) }}</span>
          <span class="summary-grade">{{ getGrade(selectedProject.score) }}</span>
          <span class="summary-hint">（当月已评分目标的平均值）</span>
        </div>
      </div>

      <!-- Milestones Tab -->
      <div v-if="detailTab === 'milestones'" class="tab-content">
        <div v-if="selectedProject.milestones && selectedProject.milestones.length > 0" class="milestone-list">
          <div v-for="ms in selectedProject.milestones" :key="ms.id" class="milestone-item">
            <div class="ms-left">
              <span class="ms-status" :class="{ done: ms.achieved }">{{ ms.achieved ? '✓' : '○' }}</span>
            </div>
            <div class="ms-body">
              <div class="ms-event">{{ ms.event || ms.group_name }}</div>
              <div class="ms-meta">
                <span v-if="ms.group_name && ms.event" class="ms-group">{{ ms.group_name }}</span>
                <span v-if="ms.due_date" class="ms-date">{{ ms.due_date }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无里程碑数据</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useProjectStore } from '@/stores/project'
import type { ProjectWithGoals } from '@/api'
import dayjs from 'dayjs'

const store = useProjectStore()
const selectedProject = ref<ProjectWithGoals | null>(null)
const detailTab = ref<'goals' | 'milestones'>('goals')

const currentTime = computed(() => dayjs().format('YYYY-MM-DD HH:mm'))

const refresh = async () => {
  await store.fetchProjects()
  await store.fetchStats()
  if (selectedProject.value) {
    await store.fetchProjectDetail(selectedProject.value.id)
    selectedProject.value = store.currentProject
  }
}

const openDetail = async (projectId: number) => {
  const detail = await store.fetchProjectDetail(projectId)
  selectedProject.value = detail
}

const getProgressClass = (progress: number) => {
  if (progress < 50) return 'red'
  if (progress < 75) return 'orange'
  return 'blue'
}

const getGrade = (score: number) => {
  if (score >= 90) return 'A'
  if (score >= 80) return 'B'
  if (score >= 70) return 'C'
  return 'D'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getScoreClass = (score: number | null) => {
  if (score === null) return 'muted'
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const getScoreBarClass = (score: number | null) => {
  if (score === null) return 'gray'
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const projects = computed(() => store.projects)
const stats = computed(() => store.stats)

onMounted(() => {
  store.fetchProjects()
  store.fetchStats()
})
</script>

<style scoped>
.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.nav-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.nav-title h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.version {
  background: var(--accent-blue);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-time {
  color: var(--text-secondary);
  font-size: 12px;
}

.btn-refresh, .btn-export, .btn-close, .btn-admin {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  text-decoration: none;
}

.btn-refresh {
  background: var(--bg-card);
  color: var(--accent-blue);
}

.btn-admin {
  background: var(--accent-purple);
  color: white;
}

.btn-export {
  background: var(--accent-blue);
  color: white;
}

.btn-close {
  background: var(--border-subtle);
  color: var(--text-primary);
}

.kpi-section, .table-section, .goal-section {
  margin-top: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.kpi-header span {
  color: var(--text-secondary);
  font-size: 13px;
}

.kpi-icon {
  background: #1E3A5F;
  padding: 8px;
  border-radius: 8px;
  font-size: 14px;
}

.kpi-icon.green { background: #1A3A2F; }
.kpi-icon.purple { background: #2D1B3E; }
.kpi-icon.red { background: #450A0A; }
.kpi-icon.orange { background: #3D1F0A; }

.kpi-value {
  font-size: 40px;
  font-weight: 700;
}

.kpi-value.red { color: var(--accent-red); }

.kpi-trend {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.kpi-trend.up { color: var(--accent-green); }
.kpi-trend.down { color: var(--accent-orange); }
.kpi-trend.red { color: var(--accent-red); }

.progress-fill.blue { background: var(--accent-blue); }
.progress-fill.green { background: var(--accent-green); }
.progress-fill.orange { background: var(--accent-orange); }
.progress-fill.red { background: var(--accent-red); }
.progress-fill.purple { background: var(--accent-purple); }
.progress-fill.gray { background: var(--text-muted); }

.project-table {
  width: 100%;
  border-collapse: collapse;
}

.project-table th,
.project-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.project-table th {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.project-table td {
  font-size: 13px;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-cell .progress-bar {
  width: 80px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.status-badge.healthy {
  background: var(--accent-green);
  color: white;
}

.status-badge.warning {
  background: var(--accent-orange);
  color: white;
}

.status-badge.risk {
  background: var(--accent-red);
  color: white;
}

.btn-detail {
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  background: var(--bg-card);
  color: var(--accent-blue);
  cursor: pointer;
  font-size: 12px;
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.goal-header .section-title {
  margin: 0;
}

.goal-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.goal-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px;
}

.goal-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.goal-score-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.goal-score-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.goal-score-value {
  font-size: 24px;
  font-weight: 700;
}

.goal-score-value.green { color: var(--accent-green); }
.goal-score-value.orange { color: var(--accent-orange); }
.goal-score-value.red { color: var(--accent-red); }
.goal-score-value.muted { color: var(--text-muted); }

.goal-score-date {
  font-size: 12px;
  color: var(--text-muted);
}

.goal-score-bar .progress-bar {
  width: 100%;
}

.goal-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--accent-blue);
  border-radius: 12px;
}

.summary-label {
  font-size: 14px;
  font-weight: 600;
}

.summary-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent-blue);
}

.summary-grade {
  font-size: 18px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
  background: var(--accent-blue);
  color: white;
}

.summary-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
}

.tab-bar {
  display: flex;
  gap: 0;
  margin-top: 16px;
  border-bottom: 2px solid var(--border-subtle);
}

.tab-btn {
  padding: 8px 20px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.tab-content {
  margin-top: 16px;
}

.milestone-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.milestone-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
}

.milestone-item:hover {
  border-color: var(--accent-blue);
}

.ms-left {
  padding-top: 2px;
}

.ms-status {
  font-size: 16px;
  color: var(--text-muted);
}

.ms-status.done {
  color: var(--accent-green);
  font-weight: 700;
}

.ms-body {
  flex: 1;
}

.ms-event {
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-line;
}

.ms-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.ms-group {
  font-size: 11px;
  color: var(--accent-purple);
  background: rgba(139, 92, 246, 0.1);
  padding: 1px 8px;
  border-radius: 4px;
}

.ms-date {
  font-size: 11px;
  color: var(--text-muted);
}

.empty-hint {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}
</style>
