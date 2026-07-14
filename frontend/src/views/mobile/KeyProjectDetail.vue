<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <router-link to="/mobile/key-projects" class="back-btn">&larr;</router-link>
      <h1>关键项目详情</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <div v-if="keyProject" class="detail-content">
      <!-- 项目信息卡片 -->
      <div class="hero-card">
        <div class="hero-top">
          <h2>{{ keyProject.name }}</h2>
          <div class="hero-badges">
            <span v-if="keyProject.score != null" class="score-badge" :class="getScoreClass(keyProject.score)">{{ keyProject.score.toFixed(1) }}</span>
            <span class="status-badge" :class="keyProject.status">{{ getStatusText(keyProject.status) }}</span>
          </div>
        </div>
        <div class="hero-meta">
          <div class="meta-item"><span class="meta-label">负责人</span><span class="meta-value">{{ keyProject.owner || '-' }}</span></div>
          <div class="meta-item"><span class="meta-label">进度</span><span class="meta-value">{{ keyProject.progress }}</span></div>
          <div class="meta-item" v-if="keyProject.start_date"><span class="meta-label">开始</span><span class="meta-value">{{ keyProject.start_date }}</span></div>
          <div class="meta-item" v-if="keyProject.end_date"><span class="meta-label">结束</span><span class="meta-value">{{ keyProject.end_date }}</span></div>
        </div>
      </div>

      <!-- 月份选择 -->
      <div v-if="availableMonths.length > 0" class="month-tabs">
        <button
          v-for="m in availableMonths"
          :key="m.key"
          class="month-tab"
          :class="{ active: selectedMonth === m.key }"
          @click="selectedMonth = m.key"
        >
          {{ m.label }}
        </button>
      </div>
      <div v-else class="empty-hint">暂无打分数据</div>

      <!-- 指标列表 -->
      <div v-if="selectedMonth && displayedGoals.length > 0" class="goal-list">
        <div v-for="item in displayedGoals" :key="item.goal.id" class="goal-card">
          <div class="goal-header">
            <span class="goal-name">{{ item.goal.name }}</span>
            <span v-if="item.score && item.score.score > 0" class="score-value" :class="getScoreClass(item.score.score)">{{ item.score.score.toFixed(1) }}</span>
            <span v-else class="score-value unscored">未评分</span>
          </div>
          <div class="goal-tag-row">
            <span class="project-tag">{{ item.goal.project_name || '-' }}</span>
          </div>
          <div class="goal-metrics">
            <div class="metric-item">
              <span class="metric-label">月度目标</span>
              <span class="metric-value">{{ item.score?.monthly_value || item.goal.monthly_target || '-' }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">月度实际</span>
              <span class="metric-value">{{ item.score?.actual_value || '-' }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">完成率</span>
              <span class="metric-value" :class="getRateClass(item.score?.monthly_rate)">
                {{ item.score?.monthly_rate != null ? item.score.monthly_rate.toFixed(1) + '%' : '-' }}
              </span>
            </div>
          </div>
          <div class="gap-section">
            <div class="gap-label">差距分析</div>
            <div v-if="item.score" class="gap-content" @click="startEditGap(item.goal.id, item.score)">
              <textarea
                v-if="editingGapKey === gapKey(item.goal.id, item.score.year, item.score.month)"
                v-model="editingGapValue"
                class="gap-textarea"
                rows="3"
                :ref="(el: any) => { if (el && editingGapKey === gapKey(item.goal.id, item.score.year, item.score.month)) gapTextareaEl = el }"
                @blur="saveGap(item.goal.id, item.score)"
              ></textarea>
              <div v-else class="gap-display">
                <span v-if="item.score.gap_analysis">{{ item.score.gap_analysis }}</span>
                <span v-else class="gap-placeholder">点击编辑</span>
              </div>
            </div>
            <div v-else class="gap-content"><span class="gap-placeholder">-</span></div>
          </div>
        </div>
      </div>
      <div v-else-if="selectedMonth && goals.length > 0" class="empty-hint">该月份暂无指标数据</div>
      <div v-else-if="goals.length === 0 && selectedMonth" class="empty-hint">该关键项目暂无关联指标</div>
    </div>

    <div v-else class="empty-hint">加载中...</div>

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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { getKeyProject, getGoalScores, upsertGoalScore } from '@/api'
import type { GoalWithLatestScore, GoalScore } from '@/api'

const route = useRoute()
const keyProject = ref<any>(null)
const goals = ref<GoalWithLatestScore[]>([])
const goalScoresMap = ref<Record<number, GoalScore[]>>({})
const selectedMonth = ref<string>('')

// 差距分析编辑
const editingGapKey = ref<string>('')
const editingGapValue = ref<string>('')
const gapTextareaEl = ref<any>(null)
const savingGap = ref(false)

// 专项排序优先级
const PROJECT_ORDER = ['Marketing能力提升', 'MTPF提升专项', '生产提效专项', '8H部署专项', '质量提升专项']

const gapKey = (goalId: number, year: number, month: number) => `${goalId}-${year}-${month}`

const startEditGap = (goalId: number, score: GoalScore) => {
  editingGapKey.value = gapKey(goalId, score.year, score.month)
  editingGapValue.value = score.gap_analysis || ''
  nextTick(() => {
    if (gapTextareaEl.value) {
      gapTextareaEl.value.focus()
      gapTextareaEl.value.select?.()
    }
  })
}

const saveGap = async (goalId: number, score: GoalScore) => {
  const newVal = editingGapValue.value
  if (newVal === (score.gap_analysis || '')) {
    editingGapKey.value = ''
    return
  }
  if (savingGap.value) return
  savingGap.value = true
  try {
    await upsertGoalScore(goalId, {
      year: score.year,
      month: score.month,
      score: score.score,
      gap_analysis: newVal,
    })
    score.gap_analysis = newVal
    const arr = goalScoresMap.value[goalId]
    if (arr) {
      const target = arr.find(s => s.year === score.year && s.month === score.month)
      if (target) target.gap_analysis = newVal
    }
  } catch (e) {
    console.error('保存差距分析失败', e)
  } finally {
    savingGap.value = false
    editingGapKey.value = ''
  }
}

const availableMonths = computed(() => {
  const months = new Set<string>()
  for (const scores of Object.values(goalScoresMap.value)) {
    for (const s of scores) {
      if (s.score > 0) {
        months.add(`${s.year}-${String(s.month).padStart(2, '0')}`)
      }
    }
  }
  const sorted = Array.from(months).sort().reverse()
  return sorted.map(m => {
    const [y, mo] = m.split('-')
    return { key: m, label: `${y}年${parseInt(mo)}月` }
  })
})

const displayedGoals = computed(() => {
  if (!selectedMonth.value) return []
  const [year, month] = selectedMonth.value.split('-').map(Number)
  const items = goals.value.map(goal => {
    const scores = goalScoresMap.value[goal.id] || []
    const score = scores.find(s => s.year === year && s.month === month)
    return { goal, score }
  })
  return items.sort((a, b) => {
    const ia = PROJECT_ORDER.indexOf(a.goal.project_name || '')
    const ib = PROJECT_ORDER.indexOf(b.goal.project_name || '')
    return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib)
  })
})

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

const getRateClass = (rate: number | null | undefined) => {
  if (rate == null) return ''
  if (rate >= 100) return 'green'
  if (rate >= 80) return 'green'
  if (rate >= 60) return 'orange'
  return 'red'
}

const loadData = async () => {
  const id = Number(route.params.id)
  const res = await getKeyProject(id)
  keyProject.value = res.data
  goals.value = res.data.goals || []

  const promises = goals.value.map(async g => {
    try {
      const scoreRes = await getGoalScores(g.id)
      goalScoresMap.value[g.id] = scoreRes.data
    } catch {
      goalScoresMap.value[g.id] = []
    }
  })
  await Promise.all(promises)

  if (availableMonths.value.length > 0 && !selectedMonth.value) {
    selectedMonth.value = availableMonths.value[0].key
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

.detail-content {
  padding: 12px 16px;
}

/* 项目信息卡片 */
.hero-card {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
  margin-bottom: 14px;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
}

.hero-top h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  flex: 1;
  line-height: 1.3;
}

.hero-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.score-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
}

.score-badge.green { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.score-badge.orange { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.score-badge.red { background: rgba(239,68,68,0.15); color: var(--accent-red); }

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.healthy { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.status-badge.warning { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.status-badge.risk { background: rgba(239,68,68,0.15); color: var(--accent-red); }

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-meta .meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--bg-secondary);
  padding: 4px 10px;
  border-radius: 6px;
}

.hero-meta .meta-label { font-size: 10px; color: var(--text-muted); }
.hero-meta .meta-value { font-size: 12px; color: var(--text-secondary); }

/* 月份选择 */
.month-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.month-tab {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.month-tab.active {
  background: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

/* 指标列表 */
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.goal-name {
  font-size: 14px;
  font-weight: 600;
  flex: 1;
  line-height: 1.3;
}

.score-value {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.score-value.green { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.score-value.orange { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.score-value.red { background: rgba(239,68,68,0.15); color: var(--accent-red); }
.score-value.unscored { background: rgba(148,163,184,0.15); color: var(--text-muted); font-weight: 500; font-size: 10px; }

.goal-tag-row {
  margin-bottom: 10px;
}

.project-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(139,92,246,0.15);
  color: #a78bfa;
  font-size: 11px;
}

.goal-metrics {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.metric-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.metric-label { font-size: 10px; color: var(--text-muted); }
.metric-value { font-size: 13px; font-weight: 700; }
.metric-value.green { color: var(--accent-green); }
.metric-value.orange { color: var(--accent-orange); }
.metric-value.red { color: var(--accent-red); }

/* 差距分析 */
.gap-section {
  border-top: 1px solid var(--border-subtle);
  padding-top: 10px;
}

.gap-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.gap-content {
  cursor: pointer;
}

.gap-display {
  min-height: 20px;
}

.gap-display span {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.gap-placeholder {
  color: var(--text-muted);
  font-style: italic;
}

.gap-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid var(--accent-blue);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.5;
  resize: vertical;
  outline: none;
  font-family: inherit;
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
