<template>
  <div class="admin">
    <header class="admin-header">
      <div class="header-left">
        <router-link to="/" class="back-link">&larr; 返回看板</router-link>
        <h1>专项目标管理</h1>
      </div>
      <div class="header-right">
        <select v-model="selectedProjectId" class="project-select" @change="loadGoals">
          <option value="">选择专项</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </header>

    <div v-if="!selectedProjectId" class="empty-state">
      <p>请从右上角选择一个专项进行管理</p>
    </div>

    <div v-else class="admin-content">
      <div class="toolbar">
        <div class="toolbar-left">
          <h2>{{ currentProject?.name }}</h2>
          <span class="toolbar-info">综合得分：<strong>{{ currentProject?.score?.toFixed(1) }}</strong></span>
        </div>
        <div class="toolbar-right">
          <div class="admin-tabs">
            <button class="admin-tab" :class="{ active: adminTab === 'goals' }" @click="adminTab = 'goals'">目标评分</button>
            <button class="admin-tab" :class="{ active: adminTab === 'milestones' }" @click="adminTab = 'milestones'">里程碑</button>
          </div>
          <button v-if="adminTab === 'goals'" class="btn-primary" @click="openAddGoal">+ 添加目标</button>
          <button v-else class="btn-primary" @click="openAddMilestone">+ 添加里程碑</button>
        </div>
      </div>

      <!-- Goals Tab -->
      <template v-if="adminTab === 'goals'">
        <table class="goal-table" v-if="goals.length > 0">
        <thead>
          <tr>
            <th style="width: 30px">#</th>
            <th>目标名称</th>
            <th style="width: 100px">最新评分</th>
            <th style="width: 100px">评分月份</th>
            <th style="width: 240px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(goal, idx) in goals" :key="goal.id">
            <td class="center">{{ idx + 1 }}</td>
            <td>{{ goal.name }}</td>
            <td class="center">
              <span v-if="goal.latest_score !== null" class="score-tag" :class="scoreTagClass(goal.latest_score)">
                {{ goal.latest_score.toFixed(1) }}
              </span>
              <span v-else class="score-tag none">未评分</span>
            </td>
            <td class="center muted">
              <span v-if="goal.latest_year && goal.latest_month">{{ goal.latest_year }}/{{ goal.latest_month }}</span>
              <span v-else>-</span>
            </td>
            <td>
              <div class="action-btns">
                <button class="btn-sm btn-score" @click="openScoreModal(goal)">打分</button>
                <button class="btn-sm btn-history" @click="openHistoryModal(goal)">历史</button>
                <button class="btn-sm btn-edit" @click="openEditGoal(goal)">编辑</button>
                <button class="btn-sm btn-danger" @click="handleDeleteGoal(goal)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无目标，请点击「添加目标」</div>
      </template>

      <!-- Milestones Tab -->
      <template v-if="adminTab === 'milestones'">
        <table class="goal-table" v-if="milestones.length > 0">
          <thead>
            <tr>
              <th style="width: 40px">状态</th>
              <th>里程碑</th>
              <th style="width: 120px">截止日期</th>
              <th style="width: 200px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ms in milestones" :key="ms.id">
              <td class="center">
                <button class="achieve-toggle" :class="{ done: ms.achieved }" @click="toggleMilestone(ms)">
                  {{ ms.achieved ? '✓' : '○' }}
                </button>
              </td>
              <td>
                <div class="ms-event-text">{{ ms.event || ms.group_name }}</div>
                <div v-if="ms.group_name && ms.event" class="ms-group-text">{{ ms.group_name }}</div>
              </td>
              <td class="center muted">{{ ms.due_date || '-' }}</td>
              <td>
                <div class="action-btns">
                  <button class="btn-sm btn-edit" @click="openEditMilestone(ms)">编辑</button>
                  <button class="btn-sm btn-danger" @click="handleDeleteMilestone(ms.id)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">暂无里程碑，请点击「添加里程碑」</div>
      </template>
    </div>

    <!-- Milestone Add/Edit Modal -->
    <div v-if="showMsModal" class="modal-mask" @click.self="showMsModal = false">
      <div class="modal-box">
        <h3>{{ editingMsId ? '编辑里程碑' : '添加里程碑' }}</h3>
        <div class="form-group">
          <label>里程碑名称</label>
          <input v-model="msForm.event" class="form-input" placeholder="里程碑事件描述" />
        </div>
        <div class="form-group">
          <label>分组名称（可选）</label>
          <input v-model="msForm.group_name" class="form-input" placeholder="关键里程碑分组" />
        </div>
        <div class="form-group">
          <label>截止日期</label>
          <input v-model="msForm.due_date" type="date" class="form-input" />
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showMsModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveMilestone" :disabled="!msForm.event.trim()">保存</button>
        </div>
      </div>
    </div>

    <!-- Add / Edit Goal Modal -->
    <div v-if="showGoalModal" class="modal-mask" @click.self="showGoalModal = false">
      <div class="modal-box">
        <h3>{{ editingGoalId ? '编辑目标' : '添加目标' }}</h3>
        <div class="form-group">
          <label>目标名称</label>
          <input v-model="goalForm.name" class="form-input" placeholder="请输入目标名称" />
        </div>
        <div class="form-group">
          <label>描述（可选）</label>
          <input v-model="goalForm.description" class="form-input" placeholder="可选" />
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showGoalModal = false">取消</button>
          <button class="btn-primary" @click="handleSaveGoal" :disabled="!goalForm.name.trim()">保存</button>
        </div>
      </div>
    </div>

    <!-- Score Modal -->
    <div v-if="scoringGoal" class="modal-mask" @click.self="scoringGoal = null">
      <div class="modal-box">
        <h3>为「{{ scoringGoal.name }}」打分</h3>
        <div class="form-row">
          <div class="form-group half">
            <label>年份</label>
            <select v-model.number="scoreForm.year" class="form-input">
              <option v-for="y in [2025, 2026, 2027]" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>
          <div class="form-group half">
            <label>月份</label>
            <select v-model.number="scoreForm.month" class="form-input">
              <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>评分（0-100）</label>
          <input v-model.number="scoreForm.score" type="number" min="0" max="100" step="0.1" class="form-input" />
          <div class="score-slider">
            <input type="range" v-model.number="scoreForm.score" min="0" max="100" step="1" class="slider" />
            <span class="slider-val">{{ scoreForm.score }}</span>
          </div>
        </div>
        <div class="form-group">
          <label>备注</label>
          <textarea v-model="scoreForm.comment" class="form-input form-textarea" rows="3" placeholder="评语或说明"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="scoringGoal = null">取消</button>
          <button class="btn-primary" @click="handleScore">提交评分</button>
        </div>
      </div>
    </div>

    <!-- History Modal -->
    <div v-if="historyGoal" class="modal-mask" @click.self="historyGoal = null">
      <div class="modal-box wide">
        <h3>「{{ historyGoal.name }}」评分历史</h3>
        <table v-if="historyScores.length > 0" class="history-table">
          <thead>
            <tr>
              <th>年月</th>
              <th>评分</th>
              <th>备注</th>
              <th style="width: 60px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in historyScores" :key="s.id">
              <td>{{ s.year }}年{{ s.month }}月</td>
              <td>
                <span class="score-tag" :class="scoreTagClass(s.score)">{{ s.score.toFixed(1) }}</span>
              </td>
              <td class="muted">{{ s.comment || '-' }}</td>
              <td>
                <button class="btn-sm btn-danger" @click="handleDeleteScore(s.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">暂无评分记录</div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="historyGoal = null">关闭</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useProjectStore } from '@/stores/project'
import { getGoalScores, getMilestones, createMilestone, updateMilestone, deleteMilestone } from '@/api'
import type { GoalWithLatestScore, GoalScore, Milestone as MilestoneType } from '@/api'
import dayjs from 'dayjs'

const store = useProjectStore()

const selectedProjectId = ref<number | string>('')
const goals = ref<GoalWithLatestScore[]>([])
const currentProject = computed(() =>
  store.projects.find(p => p.id === Number(selectedProjectId.value)) ?? null
)

const showGoalModal = ref(false)
const editingGoalId = ref<number | null>(null)
const goalForm = reactive({ name: '', description: '' })

const scoringGoal = ref<GoalWithLatestScore | null>(null)
const scoreForm = reactive({
  year: dayjs().year(),
  month: dayjs().month() + 1,
  score: 80,
  comment: '',
})

const historyGoal = ref<GoalWithLatestScore | null>(null)
const historyScores = ref<GoalScore[]>([])

const adminTab = ref<'goals' | 'milestones'>('goals')
const milestones = ref<MilestoneType[]>([])
const showMsModal = ref(false)
const editingMsId = ref<number | null>(null)
const msForm = reactive({ event: '', group_name: '', due_date: '' })

const toast = ref<{ msg: string; type: string } | null>(null)
const showToast = (msg: string, type = 'success') => {
  toast.value = { msg, type }
  setTimeout(() => { toast.value = null }, 2000)
}

onMounted(async () => {
  await store.fetchProjects()
})

const loadGoals = async () => {
  if (!selectedProjectId.value) {
    goals.value = []
    milestones.value = []
    return
  }
  const pid = Number(selectedProjectId.value)
  const detail = await store.fetchProjectDetail(pid)
  goals.value = detail?.goals ?? []
  milestones.value = detail?.milestones ?? []
}

const projects = computed(() => store.projects)

const scoreTagClass = (score: number) => {
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const openAddGoal = () => {
  editingGoalId.value = null
  goalForm.name = ''
  goalForm.description = ''
  showGoalModal.value = true
}

const openEditGoal = (goal: GoalWithLatestScore) => {
  editingGoalId.value = goal.id
  goalForm.name = goal.name
  goalForm.description = goal.description ?? ''
  showGoalModal.value = true
}

const handleSaveGoal = async () => {
  if (!goalForm.name.trim() || !selectedProjectId.value) return
  const pid = Number(selectedProjectId.value)
  if (editingGoalId.value) {
    await store.editGoal(editingGoalId.value, pid, {
      name: goalForm.name.trim(),
      description: goalForm.description.trim() || undefined,
    })
    showToast('目标已更新')
  } else {
    await store.addGoal(pid, goalForm.name.trim(), goalForm.description.trim() || undefined)
    showToast('目标已添加')
  }
  showGoalModal.value = false
  await loadGoals()
}

const handleDeleteGoal = async (goal: GoalWithLatestScore) => {
  if (!confirm(`确定删除目标「${goal.name}」？`)) return
  await store.removeGoal(goal.id, Number(selectedProjectId.value))
  showToast('目标已删除', 'warn')
  await loadGoals()
}

const openScoreModal = (goal: GoalWithLatestScore) => {
  scoringGoal.value = goal
  scoreForm.year = dayjs().year()
  scoreForm.month = dayjs().month() + 1
  scoreForm.score = goal.latest_score ?? 80
  scoreForm.comment = ''
}

const handleScore = async () => {
  if (!scoringGoal.value || !selectedProjectId.value) return
  await store.scoreGoal(
    scoringGoal.value.id,
    scoreForm.year,
    scoreForm.month,
    scoreForm.score,
    scoreForm.comment || undefined,
  )
  scoringGoal.value = null
  await loadGoals()
  await store.fetchProjects()
  await store.fetchStats()
  showToast('评分已提交')
}

const openAddMilestone = () => {
  editingMsId.value = null
  msForm.event = ''
  msForm.group_name = ''
  msForm.due_date = ''
  showMsModal.value = true
}

const openEditMilestone = (ms: MilestoneType) => {
  editingMsId.value = ms.id
  msForm.event = ms.event || ''
  msForm.group_name = ms.group_name || ''
  msForm.due_date = ms.due_date || ''
  showMsModal.value = true
}

const handleSaveMilestone = async () => {
  if (!msForm.event.trim() || !selectedProjectId.value) return
  const pid = Number(selectedProjectId.value)
  if (editingMsId.value) {
    await updateMilestone(editingMsId.value, {
      event: msForm.event.trim(),
      group_name: msForm.group_name.trim() || undefined,
      due_date: msForm.due_date || undefined,
    })
    showToast('里程碑已更新')
  } else {
    await createMilestone(pid, {
      event: msForm.event.trim(),
      group_name: msForm.group_name.trim() || undefined,
      due_date: msForm.due_date || undefined,
    })
    showToast('里程碑已添加')
  }
  showMsModal.value = false
  await loadGoals()
}

const handleDeleteMilestone = async (id: number) => {
  if (!confirm('确定删除该里程碑？')) return
  await deleteMilestone(id)
  showToast('里程碑已删除', 'warn')
  await loadGoals()
}

const toggleMilestone = async (ms: MilestoneType) => {
  await updateMilestone(ms.id, { achieved: !ms.achieved })
  await loadGoals()
}

const openHistoryModal = async (goal: GoalWithLatestScore) => {
  historyGoal.value = goal
  historyScores.value = await store.fetchGoalScores(goal.id)
}

const handleDeleteScore = async (scoreId: number) => {
  if (!confirm('确定删除该评分记录？')) return
  await store.removeScore(scoreId)
  if (historyGoal.value) {
    historyScores.value = await store.fetchGoalScores(historyGoal.value.id)
  }
  await loadGoals()
  await store.fetchProjects()
  await store.fetchStats()
  showToast('评分已删除', 'warn')
}
</script>

<style scoped>
.admin {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.back-link {
  color: var(--accent-blue);
  text-decoration: none;
  font-size: 13px;
}

.project-select {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 13px;
  min-width: 200px;
}

.admin-content {
  margin-top: 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-left h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.toolbar-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.toolbar-info strong {
  color: var(--accent-blue);
  font-size: 18px;
}

.btn-primary {
  padding: 8px 20px;
  border-radius: 6px;
  border: none;
  background: var(--accent-blue);
  color: white;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 8px 20px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
}

.goal-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
}

.goal-table th,
.goal-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.goal-table th {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.goal-table td {
  font-size: 13px;
}

.goal-table tbody tr:hover {
  background: rgba(59, 130, 246, 0.05);
}

.center {
  text-align: center;
}

.muted {
  color: var(--text-muted);
}

.score-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
}

.score-tag.green { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
.score-tag.orange { background: rgba(245, 158, 11, 0.15); color: var(--accent-orange); }
.score-tag.red { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
.score-tag.none { background: rgba(100, 116, 139, 0.15); color: var(--text-muted); }

.action-btns {
  display: flex;
  gap: 6px;
}

.btn-sm {
  padding: 4px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.btn-score { background: var(--accent-green); color: white; }
.btn-history { background: var(--accent-purple); color: white; }
.btn-edit { background: var(--accent-blue); color: white; }
.btn-danger { background: transparent; color: var(--accent-red); border: 1px solid var(--accent-red); }

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
  font-size: 14px;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 24px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-box.wide {
  max-width: 640px;
}

.modal-box h3 {
  margin: 0 0 20px;
  font-size: 16px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group.half {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.score-slider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.slider {
  flex: 1;
  accent-color: var(--accent-blue);
}

.slider-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-blue);
  min-width: 40px;
  text-align: right;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 13px;
}

.history-table th {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.toast {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  z-index: 2000;
}

.toast.success { background: var(--accent-green); color: white; }
.toast.warn { background: var(--accent-orange); color: white; }
.toast.error { background: var(--accent-red); color: white; }

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

.admin-tabs {
  display: flex;
  gap: 4px;
}

.admin-tab {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.admin-tab.active {
  background: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.achieve-toggle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--border-subtle);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.achieve-toggle.done {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: white;
}

.ms-event-text {
  font-size: 13px;
  color: var(--text-primary);
}

.ms-group-text {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}
</style>
