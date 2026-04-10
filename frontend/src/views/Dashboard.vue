<template>
  <div class="dashboard">
    <header class="nav-header">
      <div class="nav-title">
        <h1>重大项目全景监控看板</h1>
        <span class="version">V1.0</span>
      </div>
      <div class="nav-actions">
        <span class="update-time">数据更新：2026-04-10 08:00</span>
        <button @click="refresh" class="btn-refresh">手动刷新</button>
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
            <span>平均达成率</span>
            <div class="kpi-icon purple">🎯</div>
          </div>
          <div class="kpi-value">{{ (stats?.avg_achievement || 0).toFixed(1) }}%</div>
          <div class="progress-bar">
            <div class="progress-fill purple" :style="{ width: (stats?.avg_achievement || 0) + '%' }"></div>
          </div>
          <div class="kpi-trend down">环比 -2%</div>
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
            <th>达成率</th>
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
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="progress-fill" :class="getProgressClass(project.achievement_rate)" :style="{ width: project.achievement_rate + '%' }"></div>
                </div>
                <span>{{ project.achievement_rate }}%</span>
              </div>
            </td>
            <td :class="{ red: project.score < 70 }">{{ project.score }}</td>
            <td>{{ getGrade(project.score) }}</td>
            <td>
              <span class="status-badge" :class="project.status">{{ getStatusText(project.status) }}</span>
            </td>
            <td>{{ project.owner }}</td>
            <td><button class="btn-detail">详情</button></td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'

const store = useProjectStore()

const refresh = async () => {
  await store.fetchProjects()
  await store.fetchStats()
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

.btn-refresh, .btn-export {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
}

.btn-refresh {
  background: var(--bg-card);
  color: var(--accent-blue);
}

.btn-export {
  background: var(--accent-blue);
  color: white;
}

.kpi-section, .table-section {
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
  grid-template-columns: repeat(5, 1fr);
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
</style>