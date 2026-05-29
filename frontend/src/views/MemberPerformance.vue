<template>
  <div class="perf-page">
    <!-- 顶部导航栏 -->
    <header class="top-bar">
      <div class="top-left">
        <router-link to="/" class="back-btn">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          返回看板
        </router-link>
        <h1 class="page-title">成员专项绩效</h1>
      </div>
      <div class="top-right">
        <select v-model="filterProject" class="select-box" @change="loadData">
          <option value="">全部项目</option>
          <option v-for="p in projectList" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button class="btn btn-outline" @click="showRules = true">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M8 5V8L10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          评分规则
        </button>
        <label class="btn btn-primary">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          批量导入
          <input type="file" accept=".xlsx,.xls,.csv" @change="handleImport" hidden />
        </label>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-row" v-if="perfData.rows.length > 0">
      <div class="stat-card">
        <span class="stat-num">{{ perfData.total || 0 }}</span>
        <span class="stat-label">成员总数</span>
      </div>
      <div class="stat-card" v-for="s in scoreStats" :key="s.score">
        <span class="stat-num" :style="{ color: s.color }">{{ s.count }}</span>
        <span class="stat-label" :style="{ color: s.color }">{{ s.label }}</span>
      </div>
    </div>

    <!-- 数据表格 -->
    <section class="table-section" v-if="perfData.rows.length > 0">
      <div class="table-card">
        <div class="table-scroll">
          <table class="perf-table">
            <thead>
              <tr>
                <th class="col-sticky col-project">项目名称</th>
                <th class="col-sticky col-team">子团队</th>
                <th class="col-sticky col-name">成员姓名</th>
                <th v-for="m in perfData.months" :key="m.label" class="col-month">{{ m.label.replace('2026-','') }}月</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in perfData.rows" :key="row.member_id"
                  class="data-row"
                  :class="getProjectClass(row.project_name)">
                <td class="col-sticky col-project">{{ row.project_name }}</td>
                <td class="col-sticky col-team">
                  {{ row.sub_team_name }}
                  <span v-if="row.specialty_name" class="tag-specialty">{{ row.specialty_name }}</span>
                </td>
                <td class="col-sticky col-name">{{ row.member_name }}</td>
                <td v-for="sc in row.scores" :key="sc.label"
                    class="score-cell"
                    @click="openScoreEditor(sc, row)">
                  <template v-if="sc.score !== null">
                    <span class="score-badge" :style="getScoreBadgeStyle(sc.score)">{{ sc.score }}</span>
                  </template>
                  <template v-else>
                    <span class="score-empty">—</span>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section v-else class="empty-state">
      <div class="empty-icon">📊</div>
      <p>暂无数据，请先在后台管理中添加子团队成员</p>
    </section>

    <!-- 评分规则弹窗 -->
    <div v-if="showRules" class="modal-mask" @click.self="showRules = false">
      <div class="modal-box modal-lg">
        <div class="modal-top">
          <h3>评分规则</h3>
          <button class="btn-x" @click="showRules = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="rules-block">
            <h4>得分等级（1–5 分）</h4>
            <div class="level-grid">
              <div v-for="level in rules.score_levels" :key="level.score" class="level-card" :style="{ borderColor: level.color }">
                <span class="level-badge" :style="{ background: level.color+'22', color: level.color }">{{ level.label }}</span>
                <span class="level-range">{{ level.range }}</span>
              </div>
            </div>
          </div>
          <div class="rules-block">
            <h4>团队得分分布比例（建议）</h4>
            <table class="tbl-dist">
              <thead>
                <tr>
                  <th>条件</th>
                  <th v-for="n in 5" :key="n">{{ n }}分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(d, key) in rules.team_distribution" :key="key">
                  <td class="cond-cell">{{ d.condition }}</td>
                  <td v-for="(n, i) in d.ratio" :key="i" class="pct-cell">{{ n }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="import-tip">* 导入模板列：专项名称 · 子团队名称 · 项目成员 · 月份 · 得分</p>
          <p class="leader-tip">专项负责人根据专项的得分按以上规则自动赋1-5分。</p>
        </div>
      </div>
    </div>

    <!-- 得分编辑弹窗 -->
    <div v-if="editingScore" class="modal-mask" @click.self="editingScore = null">
      <div class="modal-box modal-sm">
        <div class="modal-top">
          <h3>修改得分</h3>
          <button class="btn-x" @click="editingScore = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="edit-info">
            <span>{{ editingRow?.member_name }}</span>
            <span class="edit-month">{{ editingScore?.label?.replace('2026-','') }}月</span>
          </div>
          <div class="score-picker">
            <button v-for="n in 5" :key="n"
                    class="score-opt"
                    :class="{ active: editForm.score === n }"
                    :style="editForm.score === n ? getScoreBadgeStyle(n) : {}"
                    @click="editForm.score = n">
              {{ n }}分
            </button>
          </div>
          <div class="edit-field">
            <label>备注</label>
            <textarea v-model="editForm.comment" rows="2" placeholder="可选备注…"></textarea>
          </div>
          <div class="modal-btns">
            <button class="btn btn-primary" @click="saveScore" :disabled="saving || !editForm.score">保存</button>
            <button class="btn btn-ghost" @click="editingScore = null">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 导入结果提示 -->
    <transition name="toast">
      <div v-if="importResult" class="toast-msg" :class="importResult.fail_count > 0 ? 'toast-warn' : 'toast-ok'">
        <div class="toast-content">
          <span class="toast-summary">导入完成：成功 {{ importResult.success_count }} 条，失败 {{ importResult.fail_count }} 条</span>
          <ul v-if="importResult.errors?.length" class="toast-errors">
            <li v-for="(err, i) in importResult.errors.slice(0, 10)" :key="i">{{ err }}</li>
            <li v-if="importResult.errors.length > 10" class="toast-more">...还有 {{ importResult.errors.length - 10 }} 条错误</li>
          </ul>
        </div>
        <button class="toast-close" @click="importResult = null">✕</button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import axios from 'axios'

const API = ''

interface ScoreItem {
  year: number
  month: number
  label: string
  score: number | null
  id: number | null
  comment: string
}

interface PerfRow {
  member_id: number
  member_name: string
  role: string
  project_id: number
  project_name: string
  sub_team_name: string
  specialty_name: string
  scores: ScoreItem[]
}

interface PerfData {
  months: { year: number; month: number; label: string }[]
  rows: PerfRow[]
  total: number
}

const filterProject = ref('')
const showRules = ref(false)
const perfData = ref<PerfData>({ months: [], rows: [], total: 0 })
const projectList = ref<any[]>([])
const rules = ref<any>({ score_levels: [], team_distribution: {}, leader_rule: null })
const editingScore = ref<ScoreItem | null>(null)
const editingRow = ref<PerfRow | null>(null)
const saving = ref(false)
const importResult = ref<any>(null)

const editForm = reactive({ score: 0 as number | null, comment: '' })

const scoreColors: Record<number, string> = {
  1: '#ef4444', 2: '#f97316', 3: '#eab308', 4: '#22c55e', 5: '#3b82f6',
}
const scoreLabels: Record<number, string> = {
  1: '1分(差)', 2: '2分(合格)', 3: '3分(良)', 4: '4分(优秀)', 5: '5分(卓越)',
}

const PROJECT_BG_LIST = [
  'rgba(59,130,246,0.06)',   // 蓝
  'rgba(34,197,94,0.06)',    // 绿
  'rgba(234,179,8,0.06)',    // 黄
  'rgba(168,85,247,0.06)',    // 紫
  'rgba(6,182,212,0.06)',     // 青
  'rgba(249,115,22,0.06)',   // 橙
  'rgba(236,72,153,0.06)',   // 粉
  'rgba(139,92,246,0.06)',   // 靛
]
const projectClassMap = new Map<string, string>()
let projectClassIdx = 0
const getProjectClass = (projectName: string) => {
  if (!projectClassMap.has(projectName)) {
    projectClassMap.set(projectName, `proj-bg-${projectClassIdx % PROJECT_BG_LIST.length}`)
    projectClassIdx++
  }
  return projectClassMap.get(projectName)
}

const scoreStats = computed(() => {
  const counts: Record<number, number> = { 1:0, 2:0, 3:0, 4:0, 5:0 }
  if (!perfData.value.months.length || !perfData.value.rows.length) return []
  // 从后往前找，取第一个（即最新）有实际打分数据的月份
  let latestMonth: typeof perfData.value.months[0] | null = null
  for (let i = perfData.value.months.length - 1; i >= 0; i--) {
    const m = perfData.value.months[i]
    const hasData = perfData.value.rows.some(row =>
      row.scores.find(s => s.label === m.label && s.score != null && s.score !== '')
    )
    if (hasData) {
      latestMonth = m
      break
    }
  }
  if (!latestMonth) return []
  for (const row of perfData.value.rows) {
    const sc = row.scores.find(s => s.label === latestMonth!.label)
    if (sc?.score != null && sc.score !== '') counts[sc.score]++
  }
  return Object.entries(counts).map(([score]) => ({
    score: Number(score),
    label: scoreLabels[Number(score)],
    color: scoreColors[Number(score)],
    count: counts[Number(score)],
  }))
})

const loadData = async () => {
  try {
    const params: any = {}
    if (filterProject.value) params.project_id = Number(filterProject.value)
    const [perfRes, projRes, rulesRes] = await Promise.allSettled([
      axios.get(`${API}/api/member-performance`, { params }),
      axios.get(`${API}/api/projects`),
      axios.get(`${API}/api/score-rules`),
    ])
    if (perfRes.status === 'fulfilled') {
      perfData.value = perfRes.value.data
      // 后端已按 project_id 排序（与首页项目列表顺序一致），前端不再重排
      // 如需自定义顺序可在此调整
    }
    else console.error('成员绩效数据加载失败', perfRes.reason)
    if (projRes.status === 'fulfilled') projectList.value = projRes.value.data
    else console.error('项目列表加载失败', projRes.reason)
    if (rulesRes.status === 'fulfilled') rules.value = rulesRes.value.data
    else console.error('评分规则加载失败', rulesRes.reason)
  } catch (e: any) {
    console.error('加载数据失败', e)
  }
}

const getScoreBadgeStyle = (score: number) => ({
  background: scoreColors[score] + '18',
  color: scoreColors[score],
  borderColor: scoreColors[score],
})

const openScoreEditor = (score: ScoreItem, row: PerfRow) => {
  editingScore.value = score
  editingRow.value = row
  editForm.score = score.score
  editForm.comment = score.comment || ''
}

const saveScore = async () => {
  if (!editingScore.value || !editForm.score) return
  saving.value = true
  try {
    if (editingScore.value.id) {
      await axios.put(`${API}/api/member-scores/${editingScore.value.id}`, {
        score: editForm.score,
        comment: editForm.comment,
      })
    } else {
      alert('该月暂无评分记录，请通过批量导入添加')
    }
    await loadData()
    editingScore.value = null
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleImport = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await axios.post(`${API}/api/member-scores/batch-import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = res.data
    await loadData()
  } catch (e: any) {
    const detail = e.response?.data
    if (detail?.detail) {
      const errs = Array.isArray(detail.detail) ? detail.detail : [JSON.stringify(detail.detail)]
      importResult.value = { success_count: 0, fail_count: 1, errors: errs }
    } else {
      importResult.value = { success_count: 0, fail_count: 1, errors: [e.message || '导入失败'] }
    }
  }
  input.value = ''
}

onMounted(() => { loadData() })
</script>

<style scoped>
/* ===== 页面容器 ===== */
.perf-page {
  padding: 20px 28px 40px;
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
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle, #1e2035);
}
.top-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--accent-blue, #3b82f6);
  text-decoration: none;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background .15s;
}
.back-btn:hover { background: rgba(59,130,246,0.1); }
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.top-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* ===== 按钮/选择框 ===== */
.select-box {
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle, #1e2035);
  background: var(--bg-card, #161822);
  color: var(--text-primary, #e1e4eb);
  font-size: 13px;
  cursor: pointer;
  outline: none;
  transition: border-color .15s;
}
.select-box:focus { border-color: var(--accent-blue, #3b82f6); }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all .15s;
}
.btn-primary {
  background: var(--accent-blue, #3b82f6);
  color: #fff;
}
.btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: .45; cursor: not-allowed; }
.btn-outline {
  background: transparent;
  color: var(--text-secondary, #8b8fa3);
  border: 1px solid var(--border-subtle, #1e2035);
}
.btn-outline:hover { border-color: var(--accent-blue, #3b82f6); color: var(--accent-blue, #3b82f6); }
.btn-ghost {
  background: transparent;
  color: var(--text-secondary, #8b8fa3);
}
.btn-ghost:hover { color: var(--text-primary, #e1e4eb); }

/* ===== 统计卡片 ===== */
.stats-row {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 14px 24px;
  border-radius: 12px;
  background: var(--bg-card, #161822);
  border: 1px solid var(--border-subtle, #1e2035);
  min-width: 90px;
}
.stat-num {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}
.stat-label {
  font-size: 11px;
  color: var(--text-muted, #5c5f73);
}

/* ===== 表格区域 ===== */
.table-section { margin-bottom: 24px; }
.table-card {
  border-radius: 12px;
  border: 1px solid var(--border-subtle, #1e2035);
  background: var(--bg-card, #161822);
  overflow: hidden;
}
.table-scroll {
  overflow-x: auto;
}
.perf-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
  min-width: 800px;
}
.perf-table thead th {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg-elevated, #1c1e2e);
  color: var(--text-secondary, #8b8fa3);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-subtle, #1e2035);
  white-space: nowrap;
  text-align: center;
}
.perf-table tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-subtle, #1e2035);
  white-space: nowrap;
  vertical-align: middle;
  text-align: center;
}
.perf-table tbody tr:last-child td { border-bottom: none; }
.data-row { transition: background .12s; }
.data-row:hover { background: rgba(255,255,255,0.03); }

/* 固定列 */
.col-sticky {
  position: sticky;
  left: 0;
  z-index: 5;
  background: var(--bg-card, #161822);
  text-align: center;
}
.col-project { min-width: 140px; font-weight: 500; }
.col-team   { min-width: 120px; left: 140px; }
.col-name   { min-width: 90px; left: 260px; font-weight: 500; }
.perf-table thead .col-sticky { z-index: 11; }

/* 月份列 */
.col-month {
  min-width: 64px;
  text-align: center;
  font-size: 12px;
}

/* 得分单元格 */
.score-cell {
  text-align: center;
  cursor: pointer;
  transition: background .12s;
}
.score-cell:hover { background: rgba(255,255,255,0.04); }
.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 26px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
  border: 1px solid;
}
.score-empty {
  color: var(--text-muted, #5c5f73);
  font-size: 14px;
}
.score-empty:hover { color: var(--accent-blue, #3b82f6); }

/* 按项目区分行背景 */
.proj-bg-0 td { background: rgba(59,130,246,0.06) !important; }
.proj-bg-1 td { background: rgba(34,197,94,0.06) !important; }
.proj-bg-2 td { background: rgba(234,179,8,0.06) !important; }
.proj-bg-3 td { background: rgba(168,85,247,0.06) !important; }
.proj-bg-4 td { background: rgba(6,182,212,0.06) !important; }
.proj-bg-5 td { background: rgba(249,115,22,0.06) !important; }
.proj-bg-6 td { background: rgba(236,72,153,0.06) !important; }
.proj-bg-7 td { background: rgba(139,92,246,0.06) !important; }
/* 固定列保持与行同色 */
.proj-bg-0 .col-sticky, .proj-bg-0 .col-sticky { background: rgba(59,130,246,0.10) !important; }
.proj-bg-1 .col-sticky { background: rgba(34,197,94,0.10) !important; }
.proj-bg-2 .col-sticky { background: rgba(234,179,8,0.10) !important; }
.proj-bg-3 .col-sticky { background: rgba(168,85,247,0.10) !important; }
.proj-bg-4 .col-sticky { background: rgba(6,182,212,0.10) !important; }
.proj-bg-5 .col-sticky { background: rgba(249,115,22,0.10) !important; }
.proj-bg-6 .col-sticky { background: rgba(236,72,153,0.10) !important; }
.proj-bg-7 .col-sticky { background: rgba(139,92,246,0.10) !important; }

/* 表头固定列 */
.perf-table thead .col-sticky { z-index: 11; background: var(--bg-elevated, #1c1e2e) !important; }

.tag-specialty {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(59,130,246,0.15);
  color: var(--accent-blue, #3b82f6);
  margin-left: 6px;
  vertical-align: middle;
}

/* ===== 空状态 ===== */
.empty-state {
  text-align: center;
  padding: 72px 0;
  color: var(--text-muted, #5c5f73);
}
.empty-icon { font-size: 42px; margin-bottom: 12px; }

/* ===== 弹窗 ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  backdrop-filter: blur(4px);
}
.modal-box {
  background: var(--bg-card, #161822);
  border-radius: 14px;
  width: 560px;
  max-width: 92vw;
  max-height: 84vh;
  overflow-y: auto;
  box-shadow: 0 12px 48px rgba(0,0,0,0.5);
  border: 1px solid var(--border-subtle, #1e2035);
}
.modal-lg { width: 680px; }
.modal-sm { width: 420px; }
.modal-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle, #1e2035);
  position: sticky;
  top: 0;
  background: var(--bg-card, #161822);
  z-index: 1;
}
.modal-top h3 { margin: 0; font-size: 16px; font-weight: 600; }
.btn-x {
  background: none;
  border: none;
  color: var(--text-muted, #5c5f73);
  font-size: 18px;
  cursor: pointer;
  line-height: 1;
  padding: 4px;
  border-radius: 6px;
  transition: all .12s;
}
.btn-x:hover { color: var(--text-primary, #e1e4eb); background: rgba(255,255,255,0.06); }
.modal-body { padding: 20px; }

/* 编辑弹窗内部 */
.edit-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 14px;
}
.edit-month {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 6px;
  background: rgba(59,130,246,0.12);
  color: var(--accent-blue, #3b82f6);
}
.score-picker {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.score-opt {
  flex: 1;
  padding: 8px 0;
  border-radius: 8px;
  border: 1.5px solid var(--border-subtle, #1e2035);
  background: var(--bg-elevated, #1c1e2e);
  color: var(--text-primary, #e1e4eb);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all .15s;
}
.score-opt.active {
  font-weight: 700;
  border-width: 2px;
}
.edit-field { margin-bottom: 14px; }
.edit-field label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #8b8fa3);
  margin-bottom: 6px;
}
.edit-field textarea {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle, #1e2035);
  background: var(--bg-elevated, #1c1e2e);
  color: var(--text-primary, #e1e4eb);
  font-size: 13px;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
}
.edit-field textarea:focus {
  outline: none;
  border-color: var(--accent-blue, #3b82f6);
}
.modal-btns {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 评分规则弹窗内容 */
.rules-block { margin-bottom: 22px; }
.rules-block h4 {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--text-secondary, #8b8fa3);
  font-weight: 600;
}
.level-grid {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.level-card {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid;
  background: var(--bg-elevated, #1c1e2e);
  min-width: 90px;
}
.level-badge {
  font-weight: 700;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 6px;
  display: inline-block;
  width: fit-content;
}
.level-range { font-size: 11px; color: var(--text-muted, #5c5f73); }
/* 分布比例表格 */
.tbl-dist {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.tbl-dist th, .tbl-dist td {
  padding: 8px 12px;
  border: 1px solid var(--border-subtle, #1e2035);
  text-align: center;
}
.tbl-dist th {
  background: var(--bg-elevated, #1c1e2e);
  color: var(--text-secondary, #8b8fa3);
  font-size: 12px;
}
.cond-cell { font-size: 12px; color: var(--text-muted, #5c5f73); }

/* 百分比单元格 */
.pct-cell {
  text-align: center;
  font-weight: 600;
  font-size: 13px;
}
.import-tip {
  font-size: 12px;
  color: var(--text-muted, #5c5f73);
  margin-top: 10px;
}
.leader-tip {
  font-size: 12px;
  color: var(--accent-blue, #3b82f6);
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(59,130,246,0.08);
  line-height: 1.5;
}

/* ===== Toast ===== */
.toast-msg {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 14px 18px;
  border-radius: 10px;
  z-index: 1100;
  font-size: 13px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.4);
  border: 1px solid;
  max-width: 520px;
}
.toast-content { display: flex; flex-direction: column; gap: 6px; }
.toast-summary { font-weight: 600; }
.toast-errors {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  line-height: 1.6;
  color: inherit;
  opacity: .9;
}
.toast-errors li { margin-bottom: 2px; }
.toast-more { font-style: italic; opacity: .7; }
.toast-ok { background: #0f1a14; color: #22c55e; border-color: #22c55e; }
.toast-warn { background: #1a1208; color: #f97316; border-color: #f97316; }
.toast-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 14px;
  cursor: pointer;
  opacity: .6;
  transition: opacity .12s;
}
.toast-close:hover { opacity: 1; }
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(12px); }
</style>
