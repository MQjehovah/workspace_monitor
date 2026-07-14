<template>
  <div class="goal-dashboard-page">
    <!-- 顶部导航栏 -->
    <header class="top-bar">
      <div class="top-left">
        <router-link to="/" class="back-btn">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          返回看板
        </router-link>
        <h1 class="page-title">专项目标</h1>
      </div>
      <div class="top-right">
        <select v-model="filterProject" class="select-box" @change="loadData">
          <option value="">全部项目</option>
          <option v-for="p in projectList" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-row" v-if="dashboardData.rows.length > 0">
      <div class="stat-card">
        <span class="stat-num">{{ dashboardData.rows.length }}</span>
        <span class="stat-label">目标总数</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ projectCount }}</span>
        <span class="stat-label">涉及专项</span>
      </div>
      <div class="stat-card saving-hint" v-if="saving">
        <span class="saving-dot"></span>
        <span>保存中...</span>
      </div>
      <div class="stat-card saved-hint" v-else-if="saveSuccess">
        <span>&#10003;</span>
        <span>已保存</span>
      </div>
    </div>

    <!-- 目标数据表格 -->
    <section class="table-section" v-if="dashboardData.rows.length > 0 && !loading">
      <div class="table-card">
        <table class="goal-table">
          <thead>
            <tr>
              <th class="col-sticky col-project">专项名称</th>
              <th class="col-sticky col-goal">目标名称</th>
              <th class="col-label">维度</th>
              <th class="col-sticky col-target">年度目标</th>
              <th v-for="m in dashboardData.months" :key="m" class="col-month">{{ m }}月</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(row, idx) in dashboardData.rows" :key="row.id">
              <!-- 第1行：目标值 -->
              <tr class="data-row" :class="getProjectClass(row.project_name)">
                <td class="col-sticky col-project" v-if="idx === 0 || dashboardData.rows[idx-1].project_id !== row.project_id">
                  {{ row.project_name }}
                </td>
                <td class="col-sticky col-project" v-else></td>
                <td class="col-sticky col-goal" v-if="idx === 0 || dashboardData.rows[idx-1].id !== row.id">
                  {{ row.goal_name }}
                  <span v-if="row.key_project_name" class="key-project-tag">{{ row.key_project_name }}</span>
                  <span v-if="row.description" class="goal-desc-icon" @click.stop="showGoalDesc(row)" title="查看描述">?</span>
                </td>
                <td class="col-sticky col-goal" v-else></td>
                <td class="col-label target-label">目标值</td>
                <td class="col-sticky col-target editable-cell" v-if="idx === 0 || dashboardData.rows[idx-1].id !== row.id"
                    @mousedown.prevent="activateEdit(row.id, 0, 'yearly_target', row.yearly_target)">
                  <input v-if="isEditing(row.id, 0, 'yearly_target')"
                         :ref="el => setEditRef(row.id, 0, 'yearly_target', el)"
                         type="text"
                         class="cell-input target-input"
                         v-model="editValue"
                         @blur="saveEdit(row.id, 0, 'yearly_target')"
                         @keyup.enter="$event.target.blur()"
                         @keyup.escape="cancelEdit()" />
                  <span v-else class="cell-display" :class="{ 'has-value': row.yearly_target != null }" :title="row.yearly_target != null ? String(row.yearly_target) : ''">
                    {{ row.yearly_target != null ? row.yearly_target : '—' }}
                  </span>
                </td>
                <td class="col-sticky col-target" v-else></td>
                <td v-for="(mc, mi) in row.months" :key="'t-'+row.id+'-'+mi" class="val-cell target-val editable-cell"
                    @mousedown.prevent="activateEdit(row.id, mc.month, 'monthly_target', mc.monthly_target)">
                  <input v-if="isEditing(row.id, mc.month, 'monthly_target')"
                         :ref="el => setEditRef(row.id, mc.month, 'monthly_target', el)"
                         type="text"
                         class="cell-input target-input"
                         v-model="editValue"
                         @blur="saveEdit(row.id, mc.month, 'monthly_target')"
                         @keyup.enter="$event.target.blur()"
                         @keyup.escape="cancelEdit()" />
                  <span v-else class="cell-display" :class="{ 'has-value': mc.monthly_target != null }" :title="mc.monthly_target != null ? String(mc.monthly_target) : ''">
                    {{ mc.monthly_target != null ? mc.monthly_target : '—' }}
                  </span>
                </td>
              </tr>
              <!-- 第2行：实际值 -->
              <tr class="data-row actual-row" :class="getProjectClass(row.project_name)">
                <td class="col-sticky col-project"></td>
                <td class="col-sticky col-goal"></td>
                <td class="col-label actual-label">实际值</td>
                <td class="col-sticky col-target editable-cell"
                    v-if="idx === 0 || dashboardData.rows[idx-1].id !== row.id"
                    @mousedown.prevent="activateEdit(row.id, 0, 'yearly_value', row.yearly_value)">
                  <input v-if="isEditing(row.id, 0, 'yearly_value')"
                         :ref="el => setEditRef(row.id, 0, 'yearly_value', el)"
                         type="text"
                         class="cell-input actual-input"
                         v-model="editValue"
                         @blur="saveEdit(row.id, 0, 'yearly_value')"
                         @keyup.enter="$event.target.blur()"
                         @keyup.escape="cancelEdit()" />
                  <span v-else class="cell-display text-truncate" :class="{ 'has-value': row.yearly_value != null }" :title="row.yearly_value != null ? String(row.yearly_value) : ''">
                    {{ row.yearly_value != null ? row.yearly_value : '—' }}
                  </span>
                </td>
                <td class="col-sticky col-target" v-else></td>
                <td v-for="(mc, mi) in row.months" :key="'a-'+row.id+'-'+mi" class="val-cell actual-val editable-cell"
                    @mousedown.prevent="activateEdit(row.id, mc.month, 'actual_value', mc.actual_value)">
                  <input v-if="isEditing(row.id, mc.month, 'actual_value')"
                         :ref="el => setEditRef(row.id, mc.month, 'actual_value', el)"
                         type="text"
                         class="cell-input actual-input"
                         v-model="editValue"
                         @blur="saveEdit(row.id, mc.month, 'actual_value')"
                         @keyup.enter="$event.target.blur()"
                         @keyup.escape="cancelEdit()" />
                  <span v-else class="cell-display text-truncate" :class="{ 'has-value': mc.actual_value != null }" :title="mc.actual_value != null ? String(mc.actual_value) : ''">
                    {{ mc.actual_value != null ? mc.actual_value : '—' }}
                  </span>
                </td>
              </tr>
              <!-- 第3行：完成率 -->
              <tr class="data-row rate-row" :class="getProjectClass(row.project_name)">
                <td class="col-sticky col-project"></td>
                <td class="col-sticky col-goal"></td>
                <td class="col-label rate-label">完成率</td>
                <td class="col-sticky col-target editable-cell rate-editable"
                    v-if="idx === 0 || dashboardData.rows[idx-1].id !== row.id"
                    @mousedown.prevent="activateEdit(row.id, 0, 'yearly_rate', row.yearly_rate)">
                  <input v-if="isEditing(row.id, 0, 'yearly_rate')"
                         :ref="el => setEditRef(row.id, 0, 'yearly_rate', el)"
                         type="number"
                         step="0.1"
                         class="cell-input rate-input"
                         v-model.number="editValue"
                         @blur="saveEdit(row.id, 0, 'yearly_rate')"
                         @keyup.enter="$event.target.blur()"
                         @keyup.escape="cancelEdit()" />
                  <template v-else>
                    <span v-if="row.yearly_rate != null" class="rate-badge cell-display has-value clickable" :style="getRateStyle(row.yearly_rate)">
                      {{ formatRate(row.yearly_rate) }}
                    </span>
                    <span v-else class="cell-display text-muted">—</span>
                  </template>
                </td>
                <td class="col-sticky col-target" v-else></td>
                <td v-for="(mc, mi) in row.months" :key="'r-'+row.id+'-'+mi" class="val-cell rate-val editable-cell"
                    @mousedown.prevent="activateEdit(row.id, mc.month, 'completion_rate', mc.completion_rate)">
                  <input v-if="isEditing(row.id, mc.month, 'completion_rate')"
                         :ref="el => setEditRef(row.id, mc.month, 'completion_rate', el)"
                         type="number"
                         step="0.1"
                         class="cell-input rate-input"
                         v-model.number="editValue"
                         @blur="saveEdit(row.id, mc.month, 'completion_rate')"
                         @keyup.enter="$event.target.blur()"
                         @keyup.escape="cancelEdit()" />
                  <template v-else>
                    <span v-if="mc.completion_rate != null" class="rate-badge cell-display has-value clickable" :style="getRateStyle(mc.completion_rate)">
                      {{ formatRate(mc.completion_rate) }}
                    </span>
                    <span v-else class="cell-display text-muted">—</span>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 加载中 -->
    <section v-else-if="loading" class="empty-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </section>

    <!-- 无数据 -->
    <section v-else class="empty-state">
      <div class="empty-icon">&#128202;</div>
      <p v-if="loadError">⚠️ {{ loadError }}</p>
      <p v-else>暂无目标数据，请先在后台管理中添加项目目标。</p>
    </section>

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
import { ref, computed, onMounted, nextTick } from 'vue'
import { api } from '@/api'

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

const filterProject = ref('')
const dashboardData = ref<DashboardData>({ months: [], rows: [] })
const projectList = ref<any[]>([])
const loading = ref(false)
const loadError = ref('')

// 编辑状态
const editKey = ref<string>('')   // 格式: "goalId-month-field"
const editValue = ref<number | string | null>(null)
const saving = ref(false)
const saveSuccess = ref(false)
const activeInputEl = ref<HTMLInputElement | null>(null)

const descGoalName = ref('')
const descGoalContent = ref('')
const showDescModal = ref(false)

const showGoalDesc = (row: GoalRow) => {
  descGoalName.value = row.goal_name
  descGoalContent.value = row.description || '暂无描述'
  showDescModal.value = true
}

const projectCount = computed(() => {
  return new Set(dashboardData.value.rows.map(r => r.project_id)).size
})

const getProjectClass = (name: string): string => {
  const names = [...new Set(dashboardData.value.rows.map(r => r.project_name))]
  const colors = ['proj-a', 'proj-b', 'proj-c', 'proj-d', 'proj-e']
  const map: Record<string, string> = {}
  names.forEach((n, i) => { map[n] = colors[i % colors.length] })
  return map[name] || ''
}

const formatRate = (val: number): string => val.toFixed(1) + '%'

const getRateStyle = (rate: number) => {
  if (rate >= 100) return { background: 'rgba(39,174,96,0.15)', color: '#27ae60', borderColor: 'rgba(39,174,96,0.3)' }
  if (rate >= 80) return { background: 'rgba(59,130,246,0.15)', color: '#3b82f6', borderColor: 'rgba(59,130,246,0.3)' }
  if (rate >= 60) return { background: 'rgba(243,156,18,0.15)', color: '#f39c12', borderColor: 'rgba(243,156,18,0.3)' }
  return { background: 'rgba(231,76,60,0.15)', color: '#e74c3c', borderColor: 'rgba(231,76,60,0.3)' }
}

// === 单元格编辑 ===
const isEditing = (goalId: number, month: number, field: string): boolean => {
  return editKey.value === `${goalId}-${month}-${field}`
}

// 用 ref callback 收集当前激活的 input DOM 元素
const setEditRef = (goalId: number, month: number, field: string, el: any) => {
  if (isEditing(goalId, month, field) && el) {
    activeInputEl.value = el as HTMLInputElement
  }
}

// 激活编辑模式（用 mousedown.prevent 阻止失焦）
const activateEdit = async (goalId: number, month: number, field: string, currentValue: number | string | null) => {
  // 如果点击的是已经在编辑的单元格，不做任何事
  if (isEditing(goalId, month, field)) return

  editKey.value = `${goalId}-${month}-${field}`
  editValue.value = currentValue ?? ''
  saveSuccess.value = false
  activeInputEl.value = null

  await nextTick()
  // 通过 ref callback 已经设置了 activeInputEl，直接聚焦
  if (activeInputEl.value) {
    activeInputEl.value.focus()
    activeInputEl.value.select()
  }
}

const cancelEdit = () => {
  editKey.value = ''
  editValue.value = null
  activeInputEl.value = null
}

// 统一的保存函数：处理所有字段类型
const saveEdit = async (goalId: number, month: number, field: string) => {
  if (!editKey.value) return

  const val = editValue.value
  editKey.value = ''
  editValue.value = null
  activeInputEl.value = null

  saving.value = true
  try {
    await api.put('/api/goal-dashboard/cell', {
      goal_id: goalId,
      year: 2026,
      month: month,
      field: field,
      value: val
    })

    // 更新本地数据 — 区分年度字段和月度字段
    const row = dashboardData.value.rows.find(r => r.id === goalId)
    if (row) {
      if (month === 0 && ['yearly_target', 'yearly_value', 'yearly_rate'].includes(field)) {
        // 年度字段直接在 row 上
        ;(row as any)[field] = val
      } else {
        // 月度字段在 months 数组中
        const mc = row.months.find(m => m.month === month)
        if (mc) {
          ;(mc as any)[field] = val
        }
      }
    }

    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 2000)
  } catch (e: any) {
    console.error('保存失败', e)
    loadError.value = '保存失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    saving.value = false
  }
}

// === 数据加载 ===
const loadData = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const params: any = { year: 2026 }
    if (filterProject.value) params.project_id = Number(filterProject.value)
    const [dashRes, projRes] = await Promise.all([
      api.get('/api/goal-dashboard', { params }),
      api.get('/api/projects'),
    ])
    dashboardData.value = dashRes.data
    projectList.value = projRes.data
  } catch (e: any) {
    console.error('加载目标看板数据失败', e)
    loadError.value = e.response?.data?.detail || e.message || '请求失败，请确认后端服务已启动'
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
/* ===== 关键项目标签 ===== */
.key-project-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 4px;
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
  font-size: 11px;
  font-weight: 500;
  margin-left: 4px;
}

/* ===== 页面容器 ===== */
.goal-dashboard-page {
  padding: 16px 20px 32px;
  min-height: 100vh;
  background: var(--bg-base, #0f1117);
  color: var(--text-primary, #e1e4eb);
}

/* ===== 顶部栏 ===== */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle, #1e2035);
}
.top-left { display: flex; align-items: center; gap: 16px; }
.back-btn {
  display: inline-flex; align-items: center; gap: 4px;
  color: var(--accent-blue, #3b82f6); text-decoration: none;
  font-size: 13px; padding: 4px 8px; border-radius: 6px;
  transition: background .15s;
}
.back-btn:hover { background: rgba(59,130,246,0.1); }
.page-title { margin: 0; font-size: 20px; font-weight: 700; }
.top-right { display: flex; align-items: center; gap: 10px; }

.select-box {
  padding: 7px 12px; border-radius: 8px;
  border: 1px solid var(--border-subtle, #1e2035);
  background: var(--bg-card, #161822); color: var(--text-primary, #e1e4eb);
  font-size: 13px; cursor: pointer;
}
.select-box:focus { border-color: var(--accent-blue, #3b82f6); }

/* ===== 统计卡片 ===== */
.stats-row { display: flex; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.stat-card {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 12px 22px; border-radius: 10px;
  background: var(--bg-card, #161822); border: 1px solid var(--border-subtle, #1e2035);
}
.stat-num { font-size: 22px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 11px; color: var(--text-muted, #5c5f73); }
.saving-hint .saving-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-blue, #3b82f6);
  animation: pulse 1s infinite;
}
.saved-hint .stat-num { color: var(--accent-green, #27ae60); }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* ===== 表格（撑满屏幕，无横向滚动）===== */
.table-section { margin-bottom: 24px; }
.table-card {
  border-radius: 12px; border: 1px solid var(--border-subtle, #1e2035);
  background: var(--bg-card, #161822); overflow-x: hidden;
}

.goal-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 13px;
}

/* 表头 */
.goal-table thead th {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg-elevated, #1c1e2e);
  color: var(--text-secondary, #8b8fa3);
  font-weight: 600;
  font-size: 12px;
  padding: 10px 8px;
  border-bottom: 1px solid var(--border-subtle, #1e2035);
  white-space: nowrap;
  text-align: center;
}

/* 数据单元格 */
.goal-table tbody td {
  padding: 9px 6px;
  border-bottom: 1px solid rgba(30,32,53,0.5);
  text-align: center;
  vertical-align: middle;
  font-size: 13px;
  /* 固定行高，防止长文本撑开 */
  height: 42px;
  max-height: 42px;
  overflow: hidden;
}
.goal-table tbody tr:last-child td { border-bottom: none; }

.data-row { transition: background .12s; }
.data-row:hover { background: rgba(255,255,255,0.03); }

/* 固定列 */
.col-sticky {
  position: sticky;
  z-index: 5;
  background: var(--bg-card, #161822);
  text-align: left;
  vertical-align: middle;
}
.goal-table thead .col-sticky { z-index: 11; }

.col-project {
  width: 7%;
  min-width: 70px;
  font-weight: 600;
  font-size: 13px;
  padding-left: 14px !important;
  left: 0;
}
.col-goal {
  width: 18%;
  min-width: 130px;
  font-weight: 500;
  left: 0;
}
.col-target {
  width: 6%;
  min-width: 55px;
  font-weight: 600;
  color: var(--accent-green, #27ae60);
  left: 0;
}

/* 维度列（目标值/实际值/完成率）*/
.col-label {
  width: 5%;
  min-width: 48px;
  text-align: center !important;
  font-weight: 600;
  font-size: 12px;
}
.target-label { color: var(--accent-green, #27ae60); }
.actual-label { color: var(--accent-blue, #3b82f6); }
.rate-label { color: #f39c12; }

/* 月份列 — 均分剩余宽度 */
.col-month { text-align: center; }

/* 数值单元格 & 可编辑 */
.val-cell { font-variant-numeric: tabular-nums; }
.target-val { color: var(--accent-green, #27ae60); }
.actual-val { color: var(--accent-blue, #3b82f6); font-weight: 500; }

.editable-cell {
  cursor: pointer;
  position: relative;
  padding: 2px 4px !important;
}
.editable-cell:hover {
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
}

.cell-display {
  display: inline-block;
  min-width: 28px;
  max-width: 100%;
  padding: 2px 4px;
  border-radius: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}
.cell-display.has-value { opacity: 1; }
.cell-display.text-truncate {
  display: block;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: help;
}
.text-muted { color: var(--text-muted, #5c5f73); opacity: 0.5; }

.cell-input {
  width: 72px;
  padding: 3px 6px;
  border: 1.5px solid var(--accent-blue, #3b82f6);
  border-radius: 5px;
  background: var(--bg-elevated, #1c1e2e);
  color: var(--text-primary, #e1e4eb);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  outline: none;
  box-shadow: 0 0 8px rgba(59,130,246,0.25);
}
.cell-input::-webkit-inner-spin-button,
.cell-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.target-input { color: var(--accent-green, #27ae60); border-color: var(--accent-green, #27ae60); box-shadow: 0 0 8px rgba(39,174,96,0.25); }
.actual-input { color: var(--accent-blue, #3b82f6); box-shadow: 0 0 8px rgba(59,130,246,0.25); }
.rate-input { color: #f39c12; border-color: #f39c12; box-shadow: 0 0 8px rgba(243,156,18,0.25); }

/* 完成率徽章 */
.rate-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
  white-space: nowrap;
  cursor: pointer;
}

/* 项目行区分色 */
.proj-a .col-project { border-left: 3px solid var(--accent-blue, #3b82f6); }
.proj-b .col-project { border-left: 3px solid var(--accent-purple, #a855f7); }
.proj-c .col-project { border-left: 3px solid var(--accent-green, #27ae60); }
.proj-d .col-project { border-left: 3px solid var(--accent-orange, #f97316); }
.proj-e .col-project { border-left: 3px solid var(--accent-cyan, #06b6d4); }

/* 空状态 / 加载 */
.empty-state { text-align: center; padding: 60px 0; color: var(--text-muted, #5c5f73); font-size: 14px; }
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.loading-spinner {
  width: 28px; height: 28px;
  border: 3px solid var(--border-subtle, #1e2035);
  border-top-color: var(--accent-blue, #3b82f6);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

.goal-desc-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  margin-left: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #3b82f6;
  background: rgba(59,130,246,0.12);
  border-radius: 50%;
  cursor: pointer;
  vertical-align: middle;
  flex-shrink: 0;
  transition: background 0.15s;
}
.goal-desc-icon:hover { background: rgba(59,130,246,0.25); }

.desc-modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center; z-index: 999;
}
.desc-modal-box {
  background: #fff; border-radius: 12px; padding: 24px 28px;
  max-width: 460px; width: 90%; box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.desc-modal-box h3 { margin: 0 0 14px; font-size: 16px; color: #1a1a2e; }
.desc-content { line-height: 1.7; color: #555; white-space: pre-wrap; margin: 0 0 18px; }
.desc-close-btn {
  padding: 6px 20px; background: #3b82f6; color: #fff;
  border: none; border-radius: 6px; cursor: pointer; font-size: 13px;
}
.desc-close-btn:hover { background: #2563eb; }
</style>
