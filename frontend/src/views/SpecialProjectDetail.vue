<template>
  <div class="detail-page">
    <header class="detail-header">
      <router-link to="/special-dashboard" class="back-btn">&larr; 返回看板</router-link>
      <span class="update-time">数据更新：{{ currentTime }}</span>
    </header>

    <div v-if="project" class="detail-content">
      <div class="project-hero">
        <div class="hero-left">
          <h1>{{ project.name }}<span class="special-badge">特殊专项</span></h1>
          <div class="hero-meta">
            <span class="meta-item">负责人：{{ project.owner }}</span>
            <span class="meta-item">部门：{{ project.department }}</span>
            <span v-if="project.target_date" class="meta-item">目标日期：{{ project.target_date }}</span>
          </div>
        </div>
        <div class="hero-right">
          <span class="status-badge" :class="project.status">{{ getStatusText(project.status) }}</span>
        </div>
      </div>

      <div class="kpi-row">
        <div class="kpi-card">
          <span class="kpi-label">进度</span>
          <span class="kpi-value">{{ project.progress.toFixed(1) }}%</span>
          <div class="progress-bar">
            <div class="progress-fill" :class="getProgressClass(project.progress)" :style="{ width: project.progress + '%' }"></div>
          </div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">考核得分</span>
          <span class="kpi-value">{{ project.score.toFixed(1) }}</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">子团队个数</span>
          <span class="kpi-value">{{ project.sub_teams?.length || 0 }}</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">最新达成团队</span>
          <span class="kpi-value green">{{ achievedTeamCount }}</span>
          <span class="kpi-hint">/ {{ project.sub_teams?.length || 0 }}</span>
        </div>
      </div>

      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: activeTab === 'goals' }" @click="activeTab = 'goals'">目标评分</button>
        <button class="tab-btn" :class="{ active: activeTab === 'milestones' }" @click="activeTab = 'milestones'">项目里程碑</button>
        <button class="tab-btn" :class="{ active: activeTab === 'subteams' }" @click="activeTab = 'subteams'">子团队</button>
        <button class="tab-btn" :class="{ active: activeTab === 'reports' }" @click="activeTab = 'reports'">月度报告</button>
      </div>

      <div v-if="activeTab === 'goals'" class="tab-content">
        <table v-if="project.goals && project.goals.length > 0" class="goal-table">
          <thead>
            <tr>
              <th style="min-width:280px">目标名称</th>
              <th style="width:90px">评分</th>
              <th style="width:80px">月份</th>
              <th style="width:90px">当月目标</th>
              <th style="width:90px">当月实际</th>
              <th style="width:75px">月完成率</th>
              <th style="width:90px">年度目标</th>
              <th style="width:90px">年度实际</th>
              <th style="width:75px">年完成率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="goal in project.goals" :key="goal.id">
              <td>
                <div class="goal-name">{{ goal.name }}<span v-if="goal.key_project_id" class="key-project-tag">{{ getKeyProjectName(goal.key_project_id) }}</span><span v-if="goal.description" class="goal-desc-icon" @click.stop="showGoalDesc(goal)" title="查看描述">?</span></div>
              </td>
              <td>
                <span class="goal-score-value" :class="getScoreClass(goal.latest_score)">
                  {{ goal.latest_score !== null ? goal.latest_score.toFixed(1) : '未评分' }}
                </span>
              </td>
              <td class="goal-score-date">
                <span v-if="goal.latest_year && goal.latest_month">{{ goal.latest_month }}月</span>
                <span v-else>-</span>
              </td>
              <td class="goal-extra-cell muted">{{ goal.latest_monthly_value != null ? goal.latest_monthly_value : '-' }}</td>
              <td class="goal-extra-cell muted">{{ goal.latest_monthly_actual != null ? goal.latest_monthly_actual : '-' }}</td>
              <td class="goal-extra-cell muted">{{ goal.latest_monthly_rate != null ? goal.latest_monthly_rate.toFixed(2) + '%' : '-' }}</td>
              <template v-if="goal.key_project_id">
                <td colspan="3" class="gap-cell">
                  <div class="gap-cell-text" :title="goal.latest_gap_analysis || ''">{{ goal.latest_gap_analysis || '-' }}</div>
                </td>
              </template>
              <template v-else>
                <td class="goal-extra-cell muted">{{ goal.yearly_target != null ? goal.yearly_target : '-' }}</td>
                <td class="goal-extra-cell muted">{{ goal.latest_yearly_value != null ? goal.latest_yearly_value : '-' }}</td>
                <td class="goal-extra-cell muted">{{ goal.latest_yearly_rate != null ? goal.latest_yearly_rate.toFixed(2) + '%' : '-' }}</td>
              </template>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-hint">暂无目标数据</div>

        <div class="goal-summary" v-if="project.goals && project.goals.length > 0">
          <span class="summary-label">项目综合得分</span>
          <span class="summary-value">{{ project.score.toFixed(1) }}</span>
          <span class="performance-badge" :class="perfLevel.class">{{ perfLevel.label }}</span>
          <span class="summary-hint">（当月已评分目标的平均值）</span>
        </div>
      </div>

      <div v-if="activeTab === 'milestones'" class="tab-content">
        <div v-if="project.milestones && project.milestones.length > 0" class="milestone-list">
          <div v-for="ms in sortedMilestones" :key="ms.id" class="milestone-item">
            <div class="ms-left">
              <span class="ms-status" :class="{ done: ms.achieved }">{{ ms.achieved ? '✓' : '○' }}</span>
            </div>
            <div class="ms-body">
              <div class="ms-event">{{ ms.event || ms.group_name }}</div>
              <div class="ms-meta">
                <span v-if="ms.group_name && ms.event" class="ms-group">{{ ms.group_name }}</span>
                <span v-if="ms.due_date" class="ms-date">{{ ms.due_date }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无里程碑数据</div>
      </div>

      <div v-if="activeTab === 'subteams'" class="tab-content">
      <div v-if="project.sub_teams && project.sub_teams.length > 0" class="subteams-grid">
          <div v-for="st in project.sub_teams" :key="st.id" class="subteam-card">
            <div class="st-card-header">
              <div>
                <h3 class="st-name">{{ st.name }}</h3>
                <span v-if="st.leader" class="st-leader">负责人：{{ st.leader }}</span>
              </div>
              <div v-if="st.ratings && st.ratings.length > 0" class="st-rating-badge-wrap">
                <span class="st-rating-badge" :class="getRatingClass(st.ratings[0].rating)">{{ st.ratings[0].rating }}</span>
                <span class="st-rating-date">{{ st.ratings[0].year }}/{{ st.ratings[0].month }}</span>
              </div>
            </div>
            <div v-if="st.members && st.members.length > 0" class="st-members">
              <div v-for="m in getSortedMembers(st.members, st.id)" :key="m.id" class="st-member-row">
                <span class="st-member-name">{{ m.name }}<span v-if="m.role && m.role !== '非核心'" class="st-member-role">{{ m.role }}</span></span>
                <span class="st-member-score"
                  :class="memberScoreClass(getMemberScore(m.id, st.id))"
                  @click="showMemberScoreInfo(m, st)">
                  {{ getMemberScoreText(m.id, st.id) }}
                </span>
              </div>
            </div>
            <div v-else class="st-no-members">暂无成员</div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无子团队数据</div>
      </div>

      <div v-if="activeTab === 'reports'" class="tab-content">
        <div v-if="project.reports && project.reports.length > 0" class="report-list">
          <div v-for="r in project.reports" :key="r.id" class="report-item">
            <div class="report-header">
              <h3 class="report-title">{{ r.year }}年{{ r.month }}月月度报告</h3>
              <div class="report-actions">
                <a v-if="r.pdf_path" :href="getPdfUrl(r.pdf_path)" target="_blank" class="pdf-download-link">新标签页打开</a>
                <button v-if="r.pdf_path" class="btn-fullscreen" @click="openFullscreenPdf(getPdfUrl(r.pdf_path))">全屏查看</button>
              </div>
            </div>
            <div v-if="r.pdf_path" class="pdf-viewer">
              <object :data="getPdfUrl(r.pdf_path)" type="application/pdf" class="pdf-iframe">
                <embed :src="getPdfUrl(r.pdf_path)" type="application/pdf" />
              </object>
            </div>
            <div v-if="r.content" class="report-body md-preview" v-html="renderMarkdown(r.content)"></div>
            <div v-if="!r.content && !r.pdf_path" class="report-empty">暂无内容</div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无月度报告</div>
      </div>
    </div>

    <div v-if="!project" class="loading">加载中...</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { getMemberPerformance, getKeyProjects } from '@/api'
import type { KeyProject } from '@/api'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const renderMarkdown = (content: string) => md.render(content || '（暂无内容）')
const basePrefix = import.meta.env.VITE_BASE_URL || '/project'
const getPdfUrl = (pdfPath: string | null) => {
  if (!pdfPath) return ''
  if (pdfPath.startsWith('http')) return pdfPath
  return basePrefix + pdfPath
}

const route = useRoute()
const store = useProjectStore()
const activeTab = ref<'goals' | 'milestones' | 'subteams' | 'reports'>('goals')

const descGoalName = ref('')
const descGoalContent = ref('')
const showDescModal = ref(false)

const showGoalDesc = (goal: any) => {
  descGoalName.value = goal.name
  descGoalContent.value = goal.description || '暂无描述'
  showDescModal.value = true
}

const currentTime = computed(() => dayjs().format('YYYY-MM-DD HH:mm'))

const achievedTeamCount = computed(() => {
  if (!project.value?.sub_teams) return 0
  const allRatings = project.value.sub_teams.flatMap(st => st.ratings || [])
  if (allRatings.length === 0) return 0
  const sorted = [...allRatings].sort((a, b) => (b.year - a.year) || (b.month - a.month))
  const latestYear = sorted[0].year
  const latestMonth = sorted[0].month
  return project.value.sub_teams.filter(st =>
    (st.ratings || []).some(r => r.year === latestYear && r.month === latestMonth && r.rating === '达成')
  ).length
})

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getProgressClass = (progress: number) => {
  if (progress < 50) return 'red'
  if (progress < 75) return 'orange'
  return 'blue'
}

const getScoreClass = (score: number | null) => {
  if (score === null) return 'muted'
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

onMounted(async () => {
  const id = Number(route.params.id)
  await store.fetchProjectDetail(id)
  fetchMemberScores(id)
  const res = await getKeyProjects()
  keyProjects.value = res.data
})

const keyProjects = ref<KeyProject[]>([])
const getKeyProjectName = (id: number) => keyProjects.value.find(kp => kp.id === id)?.name || ''

const project = computed(() => store.currentProject)

const fullscreenPdfUrl = ref('')
const openFullscreenPdf = (url: string) => {
  fullscreenPdfUrl.value = url
}

const sortedMilestones = computed(() => {
  if (!project.value?.milestones) return []
  return [...project.value.milestones].sort((a, b) => {
    if (!a.due_date) return 1
    if (!b.due_date) return -1
    return a.due_date.localeCompare(b.due_date)
  })
})

const getRatingClass = (rating: string) => {
  if (rating === '达成') return 'green'
  return 'red'
}

interface MemberScoreItem {
  member_id: number
  member_name: string
  sub_team_id: number
  sub_team_name: string
  latest_rating_month: { year: number; month: number } | null
  scores: Record<string, number | null>
}

const memberScores = ref<MemberScoreItem[]>([])

const fetchMemberScores = async (projectId: number) => {
  try {
    const res = await getMemberPerformance(projectId)
    const raw: any = res.data || []
    const rows = raw.rows || raw
    memberScores.value = (rows as any[]).map((row: any) => ({
      member_id: row.member_id,
      member_name: row.member_name,
      sub_team_id: row.sub_team_id ?? row.project_id ?? 0,
      sub_team_name: row.sub_team_name || '',
      latest_rating_month: row.latest_rating_month || null,
      scores: (row.scores || []).reduce((acc, s) => {
        acc[s.label] = s.score != null ? s.score : null
        return acc
      }, {} as Record<string, number | null>),
    }))
  } catch (e) {
    console.error('[SpecialProjectDetail] fetchMemberScores error:', e)
    memberScores.value = []
  }
}

const getMemberLatestRatingMonth = (memberId: number): { year: number; month: number } | null => {
  const item = memberScores.value.find(m => m.member_id === memberId)
  return item?.latest_rating_month || null
}

const getMemberScore = (memberId: number, _subTeamId: number): number | null => {
  const item = memberScores.value.find(m => m.member_id === memberId)
  if (!item || !item.scores) {
    return null
  }
  const lr = item.latest_rating_month
  if (lr) {
    const key = `${lr.year}-${String(lr.month).padStart(2, '0')}`
    if (item.scores[key] !== null && item.scores[key] !== undefined) {
      return item.scores[key]
    }
  }
  return null
}

const getMemberScoreText = (memberId: number, subTeamId: number): string => {
  const score = getMemberScore(memberId, subTeamId)
  if (score === null) return '非核心'
  return `${score}分`
}

const memberScoreClass = (score: number | null): string => {
  if (score === null) return 'score-non-core'
  if (score >= 4) return 'score-high'
  if (score >= 3) return 'score-mid'
  return 'score-low'
}

const getSortedMembers = (members: any[], subTeamId: number): any[] => {
  return [...members].sort((a, b) => {
    const scoreA = getMemberScore(a.id, subTeamId)
    const scoreB = getMemberScore(b.id, subTeamId)
    if (scoreA === null && scoreB === null) return 0
    if (scoreA === null) return 1
    if (scoreB === null) return -1
    return scoreB - scoreA
  })
}

const showMemberScoreInfo = (member: any, subTeam: any) => {
  const score = getMemberScore(member.id, subTeam.id)
  const lr = getMemberLatestRatingMonth(member.id)
  const monthText = lr ? `${lr.year}-${String(lr.month).padStart(2, '0')}` : '暂无评级'
  const text = score !== null ? `${score} 分` : '暂无评分'
  alert(`${member.name} (${subTeam.name})\n所在子团队最新评级月份：${monthText}\n该月绩效得分：${text}`)
}

const perfLevel = computed(() => {
  const score = project.value?.score ?? 0
  if (score < 40) return { level: 1, label: '1分 差', class: 'level-poor' }
  if (score < 55) return { level: 2, label: '2分 合格', class: 'level-pass' }
  if (score < 70) return { level: 3, label: '3分 良', class: 'level-good' }
  if (score < 85) return { level: 4, label: '4分 优秀', class: 'level-excellent' }
  return { level: 5, label: '5分 卓越', class: 'level-outstanding' }
})
</script>

<style scoped>
.detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 40px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.back-btn {
  color: var(--accent-blue);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.back-btn:hover {
  text-decoration: underline;
}

.update-time {
  color: var(--text-secondary);
  font-size: 12px;
}

.project-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-top: 24px;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
}

.hero-left h1 {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.special-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 4px;
  background: rgba(139, 92, 246, 0.15);
  color: var(--accent-purple);
}

.hero-meta {
  display: flex;
  gap: 20px;
}

.meta-item {
  font-size: 13px;
  color: var(--text-secondary);
}

.status-badge {
  padding: 6px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.status-badge.healthy { background: var(--accent-green); color: white; }
.status-badge.warning { background: var(--accent-orange); color: white; }
.status-badge.risk { background: var(--accent-red); color: white; }

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 20px;
}

.kpi-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 36px;
  font-weight: 700;
}

.kpi-value.green {
  color: var(--accent-green);
}

.kpi-hint {
  font-size: 16px;
  color: var(--text-muted);
  margin-left: 4px;
}

.progress-bar {
  height: 6px;
  background: var(--border-subtle);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 8px;
}

.progress-fill.blue { background: var(--accent-blue); }
.progress-fill.green { background: var(--accent-green); }
.progress-fill.orange { background: var(--accent-orange); }
.progress-fill.red { background: var(--accent-red); }

.tab-bar {
  display: flex;
  gap: 0;
  margin-top: 28px;
  border-bottom: 2px solid var(--border-subtle);
}

.tab-btn {
  padding: 10px 24px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.tab-content {
  margin-top: 20px;
}

.goal-table {
  width: 100%;
  border-collapse: collapse;
}

.goal-table th,
.goal-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: top;
}

.goal-table th {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.goal-table tbody tr:hover {
  background: rgba(59, 130, 246, 0.03);
}

.goal-name {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

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

.goal-score-value {
  font-size: 18px;
  font-weight: 700;
}

.goal-score-value.green { color: var(--accent-green); }
.goal-score-value.orange { color: var(--accent-orange); }
.goal-score-value.red { color: var(--accent-red); }
.goal-score-value.muted { color: var(--text-muted); }

.goal-score-date {
  font-size: 13px;
  color: var(--text-muted);
}

.goal-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--accent-blue);
  border-radius: 12px;
}

.summary-label {
  font-size: 14px;
  font-weight: 600;
}

.summary-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent-blue);
}

.summary-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
}

.milestone-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.milestone-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
}

.milestone-item:hover {
  border-color: var(--accent-blue);
}

.ms-left {
  padding-top: 2px;
}

.ms-status {
  font-size: 16px;
  color: var(--text-muted);
}

.ms-status.done {
  color: var(--accent-green);
  font-weight: 700;
}

.ms-body {
  flex: 1;
}

.ms-event {
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-line;
}

.ms-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.ms-group {
  font-size: 11px;
  color: var(--accent-purple);
  background: rgba(139, 92, 246, 0.1);
  padding: 1px 8px;
  border-radius: 4px;
}

.ms-date {
  font-size: 11px;
  color: var(--text-muted);
}

.empty-hint {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
  font-size: 13px;
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--text-muted);
  font-size: 14px;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.report-item {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  overflow: hidden;
}

.report-header {
  padding: 16px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.report-body {
  padding: 12px 20px 20px;
}

.md-preview { font-size: 14px; line-height: 1.8; }
.md-preview :deep(h1) { font-size: 20px; font-weight: 700; margin: 16px 0 8px; }
.md-preview :deep(h2) { font-size: 18px; font-weight: 700; margin: 14px 0 6px; }
.md-preview :deep(h3) { font-size: 16px; font-weight: 600; margin: 12px 0 6px; }
.md-preview :deep(p) { margin: 6px 0; }
.md-preview :deep(ul), .md-preview :deep(ol) { padding-left: 24px; margin: 6px 0; }
.md-preview :deep(li) { margin: 2px 0; }
.md-preview :deep(table) { width: 100%; border-collapse: collapse; margin: 8px 0; }
.md-preview :deep(th), .md-preview :deep(td) { border: 1px solid var(--border-subtle); padding: 6px 10px; font-size: 13px; }
.md-preview :deep(th) { background: var(--bg-card); font-weight: 600; }
.md-preview :deep(strong) { font-weight: 700; }
.md-preview :deep(blockquote) { border-left: 3px solid var(--accent-blue); padding-left: 12px; color: var(--text-secondary); margin: 8px 0; }
.md-preview :deep(code) { background: var(--bg-card); padding: 1px 4px; border-radius: 3px; font-size: 13px; }
.md-preview :deep(pre) { background: var(--bg-card); padding: 12px; border-radius: 6px; overflow-x: auto; }
.md-preview :deep(pre code) { background: none; padding: 0; }

.pdf-download-link {
  font-size: 12px;
  color: var(--accent-blue);
  text-decoration: none;
  padding: 4px 10px;
  border: 1px solid var(--accent-blue);
  border-radius: 4px;
  white-space: nowrap;
}

.pdf-download-link:hover {
  background: var(--accent-blue);
  color: white;
}

.pdf-viewer {
  padding: 0 20px;
  margin-top: 12px;
}

.pdf-iframe {
  width: 100%;
  height: 600px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  display: block;
}

.report-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-fullscreen {
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
}

.btn-fullscreen:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.report-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

.subteams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.subteam-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 20px;
}

.st-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.st-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.st-leader {
  font-size: 12px;
  color: var(--text-secondary);
}

.st-rating-badge-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.st-rating-badge {
  display: inline-block;
  padding: 2px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 800;
}

.st-rating-badge.green { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
.st-rating-badge.red { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); }

.st-rating-date {
  font-size: 11px;
  color: var(--text-muted);
}

.st-members {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.st-member-role {
  font-size: 11px;
  color: var(--text-secondary);
}

.st-no-members {
  color: var(--text-muted);
  font-size: 12px;
}

.st-member-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(128, 128, 128, 0.08);
}

.st-member-row:last-child {
  border-bottom: none;
}

.st-member-name {
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.st-member-score {
  cursor: pointer;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  transition: background 0.15s;
  user-select: none;
}

.st-member-score:hover {
  opacity: 0.85;
}

.st-member-score.score-high { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
.st-member-score.score-mid { background: rgba(245, 158, 11, 0.15); color: var(--accent-orange); }
.st-member-score.score-low { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }
.st-member-score.score-non-core { background: rgba(148, 163, 184, 0.1); color: var(--text-muted); }

.goal-extra-cell {
  text-align: center;
  font-size: 13px;
}

.gap-cell {
  max-width: 255px;
}

.gap-cell-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: help;
}

.performance-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 700;
  margin-left: 8px;
  vertical-align: middle;
}
.performance-badge.level-poor { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
.performance-badge.level-pass { background: rgba(245, 158, 11, 0.15); color: #d97706; }
.performance-badge.level-good { background: rgba(59, 130, 246, 0.15); color: #2563eb; }
.performance-badge.level-excellent { background: rgba(16, 185, 129, 0.15); color: #059669; }
.performance-badge.level-outstanding { background: rgba(139, 92, 246, 0.15); color: #7c3aed; }

.goal-desc-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 14px; height: 14px; margin-left: 4px; font-size: 10px; font-weight: 700;
  color: #3b82f6; background: rgba(59,130,246,0.12); border-radius: 50%;
  cursor: pointer; vertical-align: middle; flex-shrink: 0;
  transition: background 0.15s;
}
.goal-desc-icon:hover { background: rgba(59,130,246,0.25); }
</style>