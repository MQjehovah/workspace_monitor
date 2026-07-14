<template>
  <div class="detail-page">
    <header class="detail-header">
      <router-link to="/" class="back-btn">&larr; 返回看板</router-link>
      <span class="update-time">数据更新：{{ currentTime }}</span>
    </header>

    <div v-if="keyProject" class="detail-content">
      <div class="project-hero">
        <div class="hero-left">
          <h1>{{ keyProject.name }}</h1>
          <div class="hero-meta">
            <span class="meta-item">负责人：{{ keyProject.owner || '-' }}</span>
            <span v-if="keyProject.start_date" class="meta-item">开始时间：{{ keyProject.start_date }}</span>
            <span v-if="keyProject.end_date" class="meta-item">结束时间：{{ keyProject.end_date }}</span>
            <span class="meta-item">进度：{{ keyProject.progress }}</span>
          </div>
        </div>
        <div class="hero-right">
          <span v-if="keyProject.score != null" class="score-badge" :class="getScoreClass(keyProject.score)">{{ keyProject.score.toFixed(1) }}</span>
          <span class="status-badge" :class="keyProject.status">{{ getStatusText(keyProject.status) }}</span>
        </div>
      </div>

      <div v-if="availableMonths.length > 0" class="month-tabs">
        <span class="month-label">考核月份：</span>
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
      <div v-else class="no-months">暂无打分数据</div>

      <!-- 指标按所属专项分组展示 -->
      <div v-if="selectedMonth && groupedGoals.length > 0" class="groups-container">
        <div v-for="group in groupedGoals" :key="group.projectName" class="project-group" :style="{ borderLeftColor: group.color }">
          <div class="group-header" :style="{ background: group.color + '1a' }">
            <div class="group-title-wrap">
              <span class="group-color-dot" :style="{ background: group.color }"></span>
              <span class="group-title">{{ group.projectName }}</span>
            </div>
            <div class="group-meta">
              <span class="group-count">{{ group.items.length }} 个指标</span>
              <span v-if="group.avgScore != null" class="group-avg" :style="{ background: group.color + '22', color: group.color }">平均 {{ group.avgScore.toFixed(1) }}</span>
            </div>
          </div>
          <table class="goal-table">
            <thead>
              <tr>
                <th style="min-width:240px">指标名称</th>
                <th style="width:90px">月度目标</th>
                <th style="width:90px">月度实际</th>
                <th style="width:80px">月完成率</th>
                <th style="width:40%">差距分析</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in group.items" :key="item.goal.id">
                <td>
                  <div class="goal-name-cell">
                    <span class="goal-name">{{ item.goal.name }}</span>
                    <span v-if="item.score && item.score.score > 0" class="goal-score-value" :class="getScoreClass(item.score.score)">{{ item.score.score.toFixed(1) }}</span>
                    <span v-else class="goal-score-value unscored">未评分</span>
                  </div>
                </td>
                <td class="center">{{ item.score?.monthly_value || item.goal.monthly_target || '-' }}</td>
                <td class="center">{{ item.score?.actual_value || '-' }}</td>
                <td class="center">
                  <span v-if="item.score?.monthly_rate != null">{{ item.score.monthly_rate.toFixed(1) }}%</span>
                  <span v-else>-</span>
                </td>
                <td class="gap-cell">
                  <div v-if="item.score" class="gap-edit-wrapper">
                    <textarea
                      v-if="editingGapKey === gapKey(item.goal.id, item.score.year, item.score.month)"
                      v-model="editingGapValue"
                      class="gap-textarea"
                      rows="2"
                      :ref="(el: any) => { if (el && editingGapKey === gapKey(item.goal.id, item.score.year, item.score.month)) gapTextareaEl = el }"
                      @blur="saveGap(item.goal.id, item.score)"
                      @keyup.enter.exact.prevent="($event.target as HTMLTextAreaElement).blur()"
                    ></textarea>
                    <div v-else class="gap-display" @click="startEditGap(item.goal.id, item.score)">
                      <span v-if="item.score.gap_analysis" class="gap-text">{{ item.score.gap_analysis }}</span>
                      <span v-else class="gap-placeholder">点击编辑</span>
                    </div>
                  </div>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else-if="selectedMonth && goals.length > 0" class="empty-state">该月份暂无打分数据</div>
      <div v-else-if="goals.length === 0" class="empty-state">该关键项目暂无关联指标</div>
    </div>

    <div v-else class="loading">加载中...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { getKeyProject, getGoalScores, upsertGoalScore } from '@/api'
import type { GoalWithLatestScore, GoalScore } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const keyProject = ref<any>(null)
const goals = ref<GoalWithLatestScore[]>([])
const goalScoresMap = ref<Record<number, GoalScore[]>>({})
const selectedMonth = ref<string>('')

// 差距分析编辑状态
const editingGapKey = ref<string>('')
const editingGapValue = ref<string>('')
const gapTextareaEl = ref<any>(null)
const savingGap = ref(false)

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
  // 没有变化直接关闭
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
    // 更新本地数据
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

const currentTime = computed(() => dayjs().format('YYYY-MM-DD HH:mm'))

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

// 专项排序优先级
const PROJECT_ORDER = ['Marketing能力提升', 'MTPF提升专项', '生产提效专项', '8H部署专项', '质量提升专项']

// 专项主题色（左侧色条 + 标题色）
const PROJECT_COLORS: Record<string, string> = {
  'Marketing能力提升': '#3b82f6',
  'MTPF提升专项': '#8b5cf6',
  '生产提效专项': '#10b981',
  '8H部署专项': '#f59e0b',
  '质量提升专项': '#ef4444',
}
const DEFAULT_PROJECT_COLOR = '#64748b'

const getProjectColor = (name: string) => PROJECT_COLORS[name] || DEFAULT_PROJECT_COLOR

const displayedGoals = computed(() => {
  if (!selectedMonth.value) return []
  const [year, month] = selectedMonth.value.split('-').map(Number)
  const items = goals.value.map(goal => {
    const scores = goalScoresMap.value[goal.id] || []
    const score = scores.find(s => s.year === year && s.month === month)
    return { goal, score }
  })
  // 按指定专项顺序排序，同一专项内保持原顺序
  return items.sort((a, b) => {
    const ia = PROJECT_ORDER.indexOf(a.goal.project_name || '')
    const ib = PROJECT_ORDER.indexOf(b.goal.project_name || '')
    return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib)
  })
})

// 按所属专项分组
const groupedGoals = computed(() => {
  const groups: { projectName: string; color: string; items: typeof displayedGoals.value; avgScore: number | null }[] = []
  const map = new Map<string, typeof displayedGoals.value>()
  for (const item of displayedGoals.value) {
    const pn = item.goal.project_name || '其他'
    if (!map.has(pn)) map.set(pn, [])
    map.get(pn)!.push(item)
  }
  for (const [projectName, items] of map) {
    const scored = items.filter(i => i.score && i.score.score > 0)
    const avgScore = scored.length > 0
      ? Math.round(scored.reduce((sum, i) => sum + (i.score!.score || 0), 0) / scored.length * 10) / 10
      : null
    groups.push({ projectName, color: getProjectColor(projectName), items, avgScore })
  }
  return groups
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

const loadData = async () => {
  const id = Number(route.params.id)
  const res = await getKeyProject(id)
  keyProject.value = res.data
  goals.value = res.data.goals || []

  // 加载每个目标的所有历史分数
  const promises = goals.value.map(async g => {
    try {
      const scoreRes = await getGoalScores(g.id)
      goalScoresMap.value[g.id] = scoreRes.data
    } catch {
      goalScoresMap.value[g.id] = []
    }
  })
  await Promise.all(promises)

  // 默认选中最新月份
  if (availableMonths.value.length > 0 && !selectedMonth.value) {
    selectedMonth.value = availableMonths.value[0].key
  }
}

onMounted(loadData)
</script>

<style scoped>
.detail-page { max-width: 1200px; margin: 0 auto; padding: 20px; min-height: 100vh; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.back-btn { color: var(--accent-blue); text-decoration: none; font-size: 14px; }
.update-time { font-size: 12px; color: var(--text-muted); }

.project-hero { display: flex; justify-content: space-between; align-items: flex-start; background: var(--bg-card); padding: 24px; border-radius: 12px; margin-bottom: 20px; }
.hero-left h1 { margin: 0 0 12px; font-size: 22px; font-weight: 700; }
.hero-meta { display: flex; flex-wrap: wrap; gap: 12px; }
.meta-item { font-size: 13px; color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 4px; }
.hero-right { display: flex; align-items: center; gap: 10px; }
.score-badge { display: inline-block; padding: 6px 14px; border-radius: 8px; font-size: 15px; font-weight: 700; }
.score-badge.green { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.score-badge.orange { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.score-badge.red { background: rgba(239,68,68,0.15); color: var(--accent-red); }
.status-badge { display: inline-block; padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; }
.status-badge.healthy { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.status-badge.warning { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.status-badge.risk { background: rgba(239,68,68,0.15); color: var(--accent-red); }

.month-tabs { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.month-label { font-size: 13px; color: var(--text-secondary); }
.month-tab { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border-subtle); background: var(--bg-card); color: var(--text-secondary); cursor: pointer; font-size: 13px; }
.month-tab.active { background: var(--accent-blue); color: white; border-color: var(--accent-blue); }
.no-months { padding: 40px; text-align: center; color: var(--text-muted); }

.groups-container { display: flex; flex-direction: column; gap: 20px; }
.project-group { background: var(--bg-card); border-radius: 12px; overflow: hidden; border-left: 4px solid var(--border-subtle); }
.group-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; }
.group-title-wrap { display: flex; align-items: center; gap: 10px; }
.group-color-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.group-title { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.group-meta { display: flex; align-items: center; gap: 10px; }
.group-count { font-size: 12px; color: var(--text-muted); }
.group-avg { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 700; }
.goal-table { width: 100%; border-collapse: collapse; }
.goal-table th { padding: 12px 16px; text-align: left; color: var(--text-muted); font-size: 12px; font-weight: 600; border-bottom: 1px solid var(--border-subtle); }
.goal-table td { padding: 12px 16px; font-size: 13px; border-bottom: 1px solid var(--border-subtle); }
.goal-table tbody tr:hover { background: rgba(59,130,246,0.05); }
.goal-name { font-weight: 500; }
.goal-name-cell { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.project-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; background: rgba(139,92,246,0.15); color: #a78bfa; font-size: 12px; }
.goal-score-value { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.goal-score-value.green { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.goal-score-value.orange { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.goal-score-value.red { background: rgba(239,68,68,0.15); color: var(--accent-red); }
.goal-score-value.unscored { background: rgba(148,163,184,0.15); color: var(--text-muted); font-weight: 500; font-size: 11px; }
.center { text-align: center; }
.gap-cell { color: var(--text-secondary); width: 40%; }
.gap-edit-wrapper { width: 100%; }
.gap-display { cursor: pointer; min-height: 20px; padding: 2px 4px; border-radius: 4px; transition: background 0.15s; }
.gap-display:hover { background: rgba(59,130,246,0.1); }
.gap-text { font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
.gap-placeholder { font-size: 12px; color: var(--text-muted); font-style: italic; }
.gap-textarea { width: 100%; box-sizing: border-box; padding: 6px 8px; border-radius: 4px; border: 1px solid var(--accent-blue); background: var(--bg-primary); color: var(--text-primary); font-size: 12px; line-height: 1.5; resize: vertical; outline: none; font-family: inherit; }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.loading { text-align: center; padding: 60px; color: var(--text-muted); }
</style>
