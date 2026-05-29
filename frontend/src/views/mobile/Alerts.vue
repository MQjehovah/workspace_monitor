<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <h1>风险预警</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <div class="alert-summary">
      <div class="alert-item high">
        <span class="alert-num">3</span>
        <span class="alert-label">高风险</span>
      </div>
      <div class="alert-item warning">
        <span class="alert-num">5</span>
        <span class="alert-label">需关注</span>
      </div>
      <div class="alert-item total">
        <span class="alert-num">8</span>
        <span class="alert-label">预警总数</span>
      </div>
    </div>

    <div class="alert-list">
      <div v-for="alert in alerts" :key="alert.id" class="alert-card" :class="alert.level">
        <div class="alert-header">
          <span class="alert-title">{{ alert.project_name }}</span>
          <span class="alert-badge" :class="alert.level">{{ alert.level === 'risk' ? '高风险' : '需关注' }}</span>
        </div>
        <p class="alert-content">{{ alert.message }}</p>
        <div class="alert-footer">
          <span>{{ alert.date }}</span>
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

const alerts = ref([
  { id: 1, project_name: '智慧园区建设', level: 'risk', message: '进度严重滞后，已连续2周无进展', date: '2026-04-10' },
  { id: 2, project_name: '数据中台搭建', level: 'risk', message: '预算超支风险，预计超支30%', date: '2026-04-09' },
  { id: 3, project_name: '智能办公系统', level: 'risk', message: '核心人员离职，进度受阻', date: '2026-04-08' },
  { id: 4, project_name: '供应链优化', level: 'warning', message: '进度略低于预期，需关注', date: '2026-04-10' },
  { id: 5, project_name: '客户管理系统', level: 'warning', message: '部分需求变更，需调整计划', date: '2026-04-09' },
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

.alert-summary {
  display: flex;
  padding: 16px;
  gap: 10px;
}

.alert-item {
  flex: 1;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.alert-item.high { background: rgba(239, 68, 68, 0.15); border: 1px solid var(--accent-red); }
.alert-item.warning { background: rgba(245, 158, 11, 0.15); border: 1px solid var(--accent-orange); }
.alert-item.total { background: var(--bg-card); }

.alert-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
}

.alert-item.high .alert-num { color: var(--accent-red); }
.alert-item.warning .alert-num { color: var(--accent-orange); }

.alert-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.alert-list {
  padding: 0 16px;
}

.alert-card {
  background: var(--bg-card);
  padding: 14px;
  border-radius: 12px;
  margin-bottom: 10px;
  border-left: 4px solid;
}

.alert-card.risk { border-left-color: var(--accent-red); }
.alert-card.warning { border-left-color: var(--accent-orange); }

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alert-title {
  font-size: 14px;
  font-weight: 600;
}

.alert-badge {
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 10px;
}

.alert-badge.risk { background: var(--accent-red); color: white; }
.alert-badge.warning { background: var(--accent-orange); color: white; }

.alert-content {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0 0 8px;
}

.alert-footer {
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