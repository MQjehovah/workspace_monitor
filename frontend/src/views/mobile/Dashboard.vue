<template>
  <div class="mobile-dashboard">
    <header class="mobile-header">
      <h1>项目全景看板</h1>
      <div class="header-right">
        <span class="bell">🔔</span>
        <span class="avatar">PMO</span>
      </div>
    </header>

    <div class="kpi-row">
      <div class="kpi-mini">
        <span class="kpi-num">{{ stats?.total_projects || 0 }}</span>
        <span class="kpi-label">专项总数</span>
      </div>
      <div class="kpi-mini">
        <span class="kpi-num green">{{ (stats?.avg_progress || 0).toFixed(0) }}%</span>
        <span class="kpi-label">平均进度</span>
      </div>
      <div class="kpi-mini risk">
        <span class="kpi-num red">{{ stats?.risk_count || 0 }}</span>
        <span class="kpi-label">风险专项</span>
      </div>
    </div>

    <div class="section-header">
      <h2>专项进度总览</h2>
      <span>{{ projects.length }} 个专项</span>
    </div>

    <div class="project-list">
      <router-link 
        v-for="project in projects" 
        :key="project.id" 
        :to="`/mobile/project/${project.id}`"
        class="project-card"
        :class="project.status"
      >
        <div class="card-top">
          <span class="project-name">{{ project.name }}</span>
          <span class="status-badge" :class="project.status">{{ getStatusText(project.status) }}</span>
        </div>
        <div class="card-mid">
          <span class="progress-label">进度</span>
          <span class="progress-value" :class="getProgressClass(project.progress)">{{ project.progress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :class="getProgressClass(project.progress)" :style="{ width: project.progress + '%' }"></div>
        </div>
        <div class="card-footer">
          <span>负责人：{{ project.owner }}</span>
          <span>考核: {{ project.score }}分</span>
        </div>
      </router-link>
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
import { computed, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getProgressClass = (progress: number) => {
  if (progress < 50) return 'red'
  if (progress < 75) return 'orange'
  return 'green'
}

onMounted(() => {
  store.fetchProjects()
  store.fetchStats()
})

const projects = computed(() => store.projects)
const stats = computed(() => store.stats)
</script>

<style scoped>
.mobile-dashboard {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bell, .avatar {
  font-size: 18px;
}

.avatar {
  background: var(--accent-blue);
  color: white;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
}

.kpi-row {
  display: flex;
  padding: 12px 16px;
  gap: 10px;
}

.kpi-mini {
  flex: 1;
  background: var(--bg-card);
  padding: 12px;
  border-radius: 12px;
  text-align: center;
}

.kpi-mini.risk {
  border: 1px solid var(--accent-red);
}

.kpi-num {
  display: block;
  font-size: 28px;
  font-weight: 700;
}

.kpi-num.green { color: var(--accent-green); }
.kpi-num.red { color: var(--accent-red); }

.kpi-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.section-header {
  display: flex;
  justify-content: space-between;
  padding: 4px 16px;
  align-items: center;
}

.section-header h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.section-header span {
  font-size: 12px;
  color: var(--text-muted);
}

.project-list {
  padding: 12px;
}

.project-card {
  display: block;
  background: var(--bg-card);
  padding: 14px;
  border-radius: 12px;
  margin-bottom: 8px;
  border: 1px solid var(--border-subtle);
  text-decoration: none;
  color: inherit;
}

.project-card.risk {
  border-color: var(--accent-red);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.project-name {
  font-size: 14px;
  font-weight: 600;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.status-badge.healthy { background: var(--accent-green); color: white; }
.status-badge.warning { background: var(--accent-orange); color: white; }
.status-badge.risk { background: var(--accent-red); color: white; }

.card-mid {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.progress-label { font-size: 12px; color: var(--text-secondary); }

.progress-value {
  font-size: 14px;
  font-weight: 700;
}

.progress-value.green { color: var(--accent-green); }
.progress-value.orange { color: var(--accent-orange); }
.progress-value.red { color: var(--accent-red); }

.progress-bar {
  background: var(--progress-track);
  height: 6px;
  border-radius: 3px;
  margin-bottom: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
}

.progress-fill.green { background: var(--accent-green); }
.progress-fill.orange { background: var(--accent-orange); }
.progress-fill.red { background: var(--accent-red); }

.card-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
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