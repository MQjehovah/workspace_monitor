<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <router-link to="/mobile" class="back-btn">&larr;</router-link>
      <h1>关键项目</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <!-- 概览 -->
    <div class="kpi-row" v-if="list.length > 0">
      <div class="kpi-mini">
        <span class="kpi-num">{{ list.length }}</span>
        <span class="kpi-label">项目总数</span>
      </div>
      <div class="kpi-mini">
        <span class="kpi-num green">{{ healthyCount }}</span>
        <span class="kpi-label">健康</span>
      </div>
      <div class="kpi-mini risk">
        <span class="kpi-num red">{{ riskCount }}</span>
        <span class="kpi-label">高风险</span>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="content-area">
      <div v-if="list.length > 0" class="project-list">
        <router-link
          v-for="item in list"
          :key="item.id"
          :to="`/mobile/key-project/${item.id}`"
          class="project-card"
          :class="item.status"
        >
          <div class="card-top">
            <span class="project-name">{{ item.name }}</span>
            <span class="status-badge" :class="item.status">{{ getStatusText(item.status) }}</span>
          </div>
          <div class="card-mid">
            <div class="meta-item">
              <span class="meta-label">负责人</span>
              <span class="meta-value">{{ item.owner || '-' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">进度</span>
              <span class="meta-value">{{ item.progress }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">得分</span>
              <span class="meta-value score" :class="getScoreClass(item.score)">{{ item.score != null ? item.score.toFixed(1) : '-' }}</span>
            </div>
          </div>
        </router-link>
      </div>
      <div v-else class="empty-hint">暂无关键项目</div>
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
import { ref, computed, onMounted } from 'vue'
import { getKeyProjects } from '@/api'
import type { KeyProject } from '@/api'

const list = ref<KeyProject[]>([])

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getScoreClass = (score: number | null | undefined) => {
  if (score == null) return ''
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const healthyCount = computed(() => list.value.filter(i => i.status === 'healthy').length)
const riskCount = computed(() => list.value.filter(i => i.status === 'risk').length)

const loadData = async () => {
  try {
    const res = await getKeyProjects()
    list.value = res.data
  } catch (e) {
    console.error('加载关键项目失败', e)
  }
}

onMounted(loadData)
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

/* 概览 */
.kpi-row {
  display: flex;
  padding: 12px 16px;
  gap: 10px;
}

.kpi-mini {
  flex: 1;
  background: var(--bg-card);
  border-radius: 10px;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--border-subtle);
}

.kpi-num {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.kpi-num.green { color: var(--accent-green); }
.kpi-num.red { color: var(--accent-red); }
.kpi-label { font-size: 11px; color: var(--text-muted); }

/* 列表 */
.content-area {
  padding: 0 16px;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-card {
  background: var(--bg-card);
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--border-subtle);
  text-decoration: none;
  display: block;
}

.project-card.healthy { border-left-color: var(--accent-green); }
.project-card.warning { border-left-color: var(--accent-orange); }
.project-card.risk { border-left-color: var(--accent-red); }

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.project-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.healthy { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.status-badge.warning { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.status-badge.risk { background: rgba(239,68,68,0.15); color: var(--accent-red); }

.card-mid {
  display: flex;
  gap: 8px;
}

.meta-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label { font-size: 10px; color: var(--text-muted); }
.meta-value { font-size: 12px; color: var(--text-secondary); }
.meta-value.score { font-weight: 700; }
.meta-value.score.green { color: var(--accent-green); }
.meta-value.score.orange { color: var(--accent-orange); }
.meta-value.score.red { color: var(--accent-red); }

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
