<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <h1>数据分析</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <div class="analysis-content">
      <div class="chart-card">
        <h3>进度分布</h3>
        <div class="chart-placeholder">
          <div class="chart-bar green" style="width: 60%">60%</div>
          <div class="chart-bar orange" style="width: 25%">25%</div>
          <div class="chart-bar red" style="width: 15%">15%</div>
        </div>
        <div class="chart-legend">
          <span class="legend-item green">健康 9</span>
          <span class="legend-item orange">需关注 2</span>
          <span class="legend-item red">高风险 3</span>
        </div>
      </div>

      <div class="chart-card">
        <h3>部门分布</h3>
        <div class="dept-list">
          <div v-for="dept in deptStats" :key="dept.name" class="dept-item">
            <span class="dept-name">{{ dept.name }}</span>
            <span class="dept-count">{{ dept.count }}</span>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <h3>趋势分析</h3>
        <div class="trend-placeholder">
          <span class="trend-icon">📈</span>
          <p>整体进度稳中有升</p>
          <p class="trend-detail">较上周提升 3.2%</p>
        </div>
      </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const deptStats = ref([
  { name: '研发部', count: 5 },
  { name: '产品部', count: 3 },
  { name: '运营部', count: 4 },
  { name: '市场部', count: 2 },
])
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

.header-right {
  display: flex;
  align-items: center;
}

.avatar {
  background: var(--accent-blue);
  color: white;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
}

.analysis-content {
  padding: 16px;
}

.chart-card {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
}

.chart-card h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

.chart-placeholder {
  display: flex;
  gap: 8px;
  height: 40px;
  border-radius: 8px;
  overflow: hidden;
}

.chart-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.chart-bar.green { background: var(--accent-green); }
.chart-bar.orange { background: var(--accent-orange); }
.chart-bar.red { background: var(--accent-red); }

.chart-legend {
  display: flex;
  justify-content: space-around;
  margin-top: 12px;
  font-size: 12px;
}

.legend-item::before {
  content: '●';
  margin-right: 4px;
}

.legend-item.green { color: var(--accent-green); }
.legend-item.orange { color: var(--accent-orange); }
.legend-item.red { color: var(--accent-red); }

.dept-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dept-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.dept-name {
  font-size: 13px;
}

.dept-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-blue);
}

.trend-placeholder {
  text-align: center;
  padding: 20px;
}

.trend-icon {
  font-size: 32px;
}

.trend-placeholder p {
  margin: 8px 0;
  font-size: 14px;
}

.trend-detail {
  color: var(--accent-green);
  font-size: 12px;
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