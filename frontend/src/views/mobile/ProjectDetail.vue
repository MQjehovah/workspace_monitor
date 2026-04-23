<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <router-link to="/mobile" class="back-btn">&larr;</router-link>
      <h1>专项详情</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <div v-if="project" class="detail-content">
      <div class="project-header">
        <h2>{{ project.name }}</h2>
        <span class="status-badge" :class="project.status">{{ getStatusText(project.status) }}</span>
      </div>

      <div class="kpi-grid">
        <div class="kpi-item">
          <span class="kpi-label">进度</span>
          <span class="kpi-value green">{{ project.progress.toFixed(1) }}%</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">考核得分</span>
          <span class="kpi-value">{{ project.score.toFixed(1) }}分</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">达成率</span>
          <span class="kpi-value">{{ project.achievement_rate.toFixed(1) }}%</span>
        </div>
      </div>

      <div class="info-section">
        <h3>基本信息</h3>
        <div class="info-row">
          <span class="info-label">负责人</span>
          <span class="info-value">{{ project.owner }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">部门</span>
          <span class="info-value">{{ project.department }}</span>
        </div>
        <div v-if="project.target_date" class="info-row">
          <span class="info-label">目标日期</span>
          <span class="info-value">{{ project.target_date }}</span>
        </div>
      </div>

      <div class="tab-section">
        <div class="tab-bar">
          <button class="tab-btn" :class="{ active: activeTab === 'goals' }" @click="activeTab = 'goals'">目标评分</button>
          <button class="tab-btn" :class="{ active: activeTab === 'milestones' }" @click="activeTab = 'milestones'">项目里程碑</button>
        </div>

        <template v-if="activeTab === 'goals'">
          <div class="goals-list" v-if="project.goals && project.goals.length > 0">
            <div v-for="goal in project.goals" :key="goal.id" class="goal-item">
              <div class="goal-top">
                <span class="goal-name">{{ goal.name }}</span>
              </div>
              <div class="goal-score-display">
                <span class="score-num" :class="getScoreClass(goal.latest_score)">
                  {{ goal.latest_score !== null ? goal.latest_score.toFixed(1) : '未评分' }}
                </span>
                <span v-if="goal.latest_year && goal.latest_month" class="score-date">
                  {{ goal.latest_year }}/{{ goal.latest_month }}
                </span>
              </div>
              <div class="goal-bar">
                <div class="progress-bar">
                  <div class="progress-fill" :class="getScoreBarClass(goal.latest_score)" :style="{ width: (goal.latest_score || 0) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无目标数据</div>

          <div class="project-score-summary" v-if="project.goals && project.goals.length > 0">
            <span>项目综合得分</span>
            <span class="summary-score">{{ project.score.toFixed(1) }}</span>
            <span class="summary-grade" :class="getGradeClass(project.score)">{{ getGrade(project.score) }}</span>
          </div>
        </template>

        <template v-if="activeTab === 'milestones'">
          <div class="timeline" v-if="project.milestones && project.milestones.length > 0">
            <div v-for="(ms, idx) in sortedMilestones" :key="ms.id" class="tl-item" :class="{ last: idx === sortedMilestones.length - 1 }">
              <div class="tl-left">
                <div class="tl-dot" :class="{ done: ms.achieved }"></div>
                <div class="tl-line" v-if="idx < sortedMilestones.length - 1"></div>
              </div>
              <div class="tl-content">
                <div class="tl-date">{{ ms.due_date || '待定' }}</div>
                <div class="tl-title">{{ ms.event || ms.group_name }}</div>
                <div v-if="ms.group_name && ms.event" class="tl-group">{{ ms.group_name }}</div>
                <span v-if="ms.achieved" class="tl-badge">已完成</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无里程碑数据</div>
        </template>
      </div>
    </div>

    <div v-else class="loading">加载中...</div>

    <nav class="bottom-nav">
      <router-link to="/mobile" class="nav-item">
        <span class="nav-icon">📊</span>
        <span>总览</span>
      </router-link>
      <router-link to="/mobile" class="nav-item">
        <span class="nav-icon">📋</span>
        <span>专项</span>
      </router-link>
      <router-link to="/mobile/analysis" class="nav-item">
        <span class="nav-icon">📈</span>
        <span>分析</span>
      </router-link>
      <router-link to="/mobile/alerts" class="nav-item">
        <span class="nav-icon">⚠️</span>
        <span>预警</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const store = useProjectStore()
const activeTab = ref<'goals' | 'milestones'>('goals')

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getGrade = (score: number) => {
  if (score >= 90) return 'A'
  if (score >= 80) return 'B'
  if (score >= 70) return 'C'
  return 'D'
}

const getGradeClass = (score: number) => {
  if (score >= 90) return 'grade-a'
  if (score >= 80) return 'grade-b'
  if (score >= 70) return 'grade-c'
  return 'grade-d'
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

onMounted(async () => {
  const id = Number(route.params.id)
  await store.fetchProjects()
  await store.fetchProjectDetail(id)
})

const project = computed(() => store.currentProject)

const sortedMilestones = computed(() => {
  if (!project.value?.milestones) return []
  return [...project.value.milestones].sort((a, b) => {
    if (!a.due_date) return 1
    if (!b.due_date) return -1
    return a.due_date.localeCompare(b.due_date)
  })
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

.detail-content {
  padding: 16px;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.project-header h2 {
  margin: 0;
  font-size: 18px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.status-badge.healthy { background: var(--accent-green); color: white; }
.status-badge.warning { background: var(--accent-orange); color: white; }
.status-badge.risk { background: var(--accent-red); color: white; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.kpi-item {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.kpi-label {
  display: block;
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 20px;
  font-weight: 700;
}

.kpi-value.green { color: var(--accent-green); }

.info-section {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.info-section h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.info-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.info-value {
  font-size: 13px;
}

.goals-section {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
}

.tab-section {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
}

.tab-bar {
  display: flex;
  border-bottom: 2px solid var(--border-subtle);
  margin-bottom: 12px;
}

.tab-btn {
  flex: 1;
  padding: 10px 0;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.empty-hint {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.timeline {
  padding: 4px 0;
}

.tl-item {
  display: flex;
  gap: 12px;
  min-height: 60px;
}

.tl-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}

.tl-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--text-muted);
  border: 2px solid var(--bg-card);
  box-shadow: 0 0 0 2px var(--text-muted);
  flex-shrink: 0;
  margin-top: 4px;
}

.tl-dot.done {
  background: var(--accent-green);
  box-shadow: 0 0 0 2px var(--accent-green);
}

.tl-line {
  width: 2px;
  flex: 1;
  background: var(--border-subtle);
  margin: 4px 0;
}

.tl-content {
  flex: 1;
  padding-bottom: 16px;
}

.tl-date {
  font-size: 11px;
  color: var(--accent-blue);
  font-weight: 600;
  margin-bottom: 2px;
}

.tl-title {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

.tl-group {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.tl-badge {
  display: inline-block;
  margin-top: 4px;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
}

.goals-section h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

.goals-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.goal-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
}

.goal-top {
  margin-bottom: 8px;
}

.goal-name {
  font-size: 13px;
  font-weight: 600;
}

.goal-score-display {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.score-num {
  font-size: 22px;
  font-weight: 700;
}

.score-num.green { color: var(--accent-green); }
.score-num.orange { color: var(--accent-orange); }
.score-num.red { color: var(--accent-red); }
.score-num.muted { color: var(--text-muted); font-size: 14px; }

.score-date {
  font-size: 11px;
  color: var(--text-muted);
}

.goal-bar .progress-bar {
  width: 100%;
}

.progress-fill.green { background: var(--accent-green); }
.progress-fill.orange { background: var(--accent-orange); }
.progress-fill.red { background: var(--accent-red); }
.progress-fill.gray { background: var(--text-muted); }

.project-score-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--accent-blue);
  font-size: 13px;
}

.summary-score {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-blue);
}

.summary-grade {
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  color: white;
}

.grade-a { background: var(--accent-green); }
.grade-b { background: var(--accent-blue); }
.grade-c { background: var(--accent-orange); }
.grade-d { background: var(--accent-red); }

.loading {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
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
</style>
