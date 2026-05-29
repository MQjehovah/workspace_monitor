<template>
  <div class="mobile-page">
    <header class="mobile-header">
      <router-link to="/mobile" class="back-btn">&larr;</router-link>
      <h1>专项详情</h1>
      <div class="header-right">
        <span class="avatar">PMO</span>
      </div>
    </header>

    <div v-if="project" class="detail-content">
      <div class="project-hero">
        <div class="hero-left">
          <h1>{{ project.name }}</h1>
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

      <div class="kpi-grid">
        <div class="kpi-item">
          <span class="kpi-label">进度</span>
          <span class="kpi-value green">{{ project.progress.toFixed(1) }}%</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">考核得分</span>
          <span class="kpi-value">{{ project.score.toFixed(1) }}分</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">子团队个数</span>
          <span class="kpi-value">{{ project.sub_teams?.length || 0 }}</span>
        </div>
        <div class="kpi-item">
          <span class="kpi-label">最新达成团队</span>
          <span class="kpi-value green">{{ achievedTeamCount }}</span>
          <span class="kpi-hint">/ {{ project.sub_teams?.length || 0 }}</span>
        </div>
      </div>

      <div class="tab-section">
        <div class="tab-bar">
          <button class="tab-btn" :class="{ active: activeTab === 'goals' }" @click="activeTab = 'goals'">目标评分</button>
          <button class="tab-btn" :class="{ active: activeTab === 'milestones' }" @click="activeTab = 'milestones'">项目里程碑</button>
          <button class="tab-btn" :class="{ active: activeTab === 'subteams' }" @click="activeTab = 'subteams'">子团队</button>
          <button class="tab-btn" :class="{ active: activeTab === 'reports' }" @click="activeTab = 'reports'">月度报告</button>
        </div>

        <template v-if="activeTab === 'goals'">
          <div class="goals-list" v-if="project.goals && project.goals.length > 0">
            <div v-for="goal in project.goals" :key="goal.id" class="goal-item">
              <div class="goal-top">
                <span class="goal-name">{{ goal.name }}</span>
                <span v-if="goal.description" class="goal-desc-icon" @click.stop="showGoalDesc(goal)" title="查看描述">?</span>
              </div>
              <div class="goal-details">
                <div class="detail-row">
                  <span class="detail-label">评分</span>
                  <span class="detail-value score" :class="getScoreClass(goal.latest_score)">
                    {{ goal.latest_score !== null ? goal.latest_score.toFixed(1) : '未评分' }}
                  </span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">月份</span>
                  <span class="detail-value">{{ goal.latest_year && goal.latest_month ? goal.latest_month + '月' : '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">当月目标</span>
                  <span class="detail-value">{{ goal.latest_monthly_value != null ? goal.latest_monthly_value : '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">当月实际</span>
                  <span class="detail-value actual">{{ goal.latest_monthly_actual != null ? goal.latest_monthly_actual : '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">月完成率</span>
                  <span class="detail-value">{{ goal.latest_monthly_rate != null ? goal.latest_monthly_rate.toFixed(2) + '%' : '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">年度目标</span>
                  <span class="detail-value">{{ goal.yearly_target != null ? goal.yearly_target : '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">年度实际</span>
                  <span class="detail-value actual">{{ goal.latest_yearly_value != null ? goal.latest_yearly_value : '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">年完成率</span>
                  <span class="detail-value">{{ goal.latest_yearly_rate != null ? goal.latest_yearly_rate.toFixed(2) + '%' : '-' }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无目标数据</div>

          <div class="project-score-summary" v-if="project.goals && project.goals.length > 0">
            <span>项目综合得分</span>
            <span class="summary-score">{{ project.score.toFixed(1) }}</span>
          </div>
        </template>

        <template v-if="activeTab === 'milestones'">
          <div class="timeline" v-if="project.milestones && project.milestones.length > 0">
            <div v-for="(ms, idx) in sortedMilestones" :key="ms.id" class="tl-item" :class="{ last: idx === sortedMilestones.length - 1 }">
              <div class="tl-left">
                <div class="tl-dot" :class="{ done: ms.achieved }"></div>
                <div class="tl-line" v-if="idx < sortedMilestones.length - 1"></div>
              </div>
              <div class="tl-content">
                <div class="tl-date">{{ ms.due_date || '待定' }}</div>
                <div class="tl-title">{{ ms.event || ms.group_name }}</div>
                <div v-if="ms.group_name && ms.event" class="tl-group">{{ ms.group_name }}</div>
                <span v-if="ms.achieved" class="tl-badge">已完成</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无里程碑数据</div>
        </template>

        <template v-if="activeTab === 'subteams'">
          <div v-if="project.sub_teams && project.sub_teams.length > 0" class="subteams-list">
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
                <div v-for="m in st.members" :key="m.id" class="st-member-row">
                  <span class="st-member-name">{{ m.name }}<span v-if="m.role" class="st-member-role">{{ m.role }}</span></span>
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
        </template>

        <template v-if="activeTab === 'reports'">
          <div v-if="project.reports && project.reports.length > 0" class="report-list">
            <div v-for="r in project.reports" :key="r.id" class="report-item">
              <div class="report-title-row">
                <span class="report-title">{{ r.year }}年{{ r.month }}月月度报告</span>
                <a v-if="r.pdf_path" :href="getPdfUrl(r.pdf_path)" target="_blank" class="pdf-link">查看 PDF</a>
              </div>
              <div v-if="r.pdf_path" class="pdf-viewer-mobile">
                <template v-if="isAndroid">
                  <div v-if="pdfLoading[r.id]" class="pdf-loading">PDF加载中...</div>
                  <div v-else-if="pdfPageCounts[r.id]" class="pdf-pages-scroll">
                    <img v-for="idx in pdfPageCounts[r.id]" :key="idx"
                         :src="`${apiUrl}/api/reports/${r.id}/pdf-page/${idx - 1}`"
                         class="pdf-page-img" loading="lazy" />
                  </div>
                  <div v-else class="pdf-fallback">
                    <a :href="getPdfUrl(r.pdf_path)" target="_blank" class="pdf-link">下载查看PDF</a>
                  </div>
                </template>
                <iframe v-else :src="getPdfUrl(r.pdf_path)" class="pdf-iframe-mobile"></iframe>
                <button class="btn-fullscreen-mobile" @click="openFullscreenPdf(r)">全屏查看</button>
              </div>
              <div v-if="r.content" class="report-body md-preview" v-html="renderMarkdown(r.content)"></div>
              <div v-if="!r.content && !r.pdf_path" class="empty-hint">暂无内容</div>
            </div>
          </div>
          <div v-else class="empty-hint">暂无月度报告</div>
        </template>
      </div>
    </div>

    <div v-else class="loading">加载中...</div>

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

    <!-- Fullscreen PDF Overlay -->
    <div v-if="showFullscreen" class="pdf-fullscreen-overlay">
      <div class="pdf-fullscreen-header">
        <span>PDF 预览</span>
        <button class="pdf-fullscreen-close" @click="showFullscreen = false">关闭</button>
      </div>
      <template v-if="isAndroid">
        <div class="pdf-fullscreen-body">
          <div v-if="fullscreenPageCount === 0" class="pdf-loading">加载中...</div>
          <div v-else class="pdf-pages-scroll">
            <img v-for="idx in fullscreenPageCount" :key="idx"
                 :src="`${apiUrl}/api/reports/${fullscreenReportId}/pdf-page/${idx - 1}`"
                 class="pdf-page-img" />
          </div>
        </div>
      </template>
      <iframe v-else :src="fullscreenIframeSrc" class="pdf-fullscreen-iframe"></iframe>
    </div>
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { getMemberPerformance } from '@/api'
import MarkdownIt from 'markdown-it'

const isAndroid = /Android/i.test(navigator.userAgent)

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const renderMarkdown = (content: string) => md.render(content || '（暂无内容）')
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const getPdfUrl = (pdfPath: string | null) => {
  if (!pdfPath) return ''
  if (pdfPath.startsWith('http')) return pdfPath
  return apiUrl + pdfPath
}

const route = useRoute()
const store = useProjectStore()

const descGoalName = ref('')
const descGoalContent = ref('')
const showDescModal = ref(false)

const showGoalDesc = (goal: any) => {
  descGoalName.value = goal.name
  descGoalContent.value = goal.description || '暂无描述'
  showDescModal.value = true
}
const activeTab = ref<'goals' | 'milestones' | 'subteams' | 'reports'>('goals')

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getScoreClass = (score: number | null) => {
  if (score === null) return 'muted'
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const getScoreBarClass = (score: number | null) => {
  if (score === null) return 'gray'
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const getRatingClass = (rating: string) => {
  if (rating === '达成') return 'green'
  return 'red'
}

onMounted(async () => {
  const id = Number(route.params.id)
  await store.fetchProjects()
  await store.fetchProjectDetail(id)
  fetchMemberScores(id)
})

const project = computed(() => store.currentProject)

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

const showFullscreen = ref(false)
const fullscreenIframeSrc = ref('')
const fullscreenReportId = ref(0)
const fullscreenPageCount = ref(0)

const pdfPageCounts = ref<Record<number, number>>({})
const pdfLoading = ref<Record<number, boolean>>({})

async function loadPdfInfo(reportId: number) {
  if (pdfPageCounts.value[reportId] || pdfLoading.value[reportId]) return
  pdfLoading.value[reportId] = true
  try {
    const res = await fetch(`${apiUrl}/api/reports/${reportId}/pdf-info`)
    if (res.ok) {
      const data = await res.json()
      pdfPageCounts.value[reportId] = data.page_count
    }
  } catch { /* ignore */ }
  pdfLoading.value[reportId] = false
}

function openFullscreenPdf(r: any) {
  if (!isAndroid) {
    fullscreenIframeSrc.value = getPdfUrl(r.pdf_path)
    showFullscreen.value = true
    return
  }
  fullscreenReportId.value = r.id
  fullscreenPageCount.value = pdfPageCounts.value[r.id] || 0
  showFullscreen.value = true
  if (!fullscreenPageCount.value) {
    fetch(`${apiUrl}/api/reports/${r.id}/pdf-info`)
      .then(res => res.json())
      .then(data => { fullscreenPageCount.value = data.page_count })
      .catch(() => { fullscreenPageCount.value = 0 })
  }
}

watch(project, (p) => {
  if (!isAndroid || !p?.reports) return
  p.reports.forEach((r: any) => {
    if (r.pdf_path) loadPdfInfo(r.id)
  })
})

const sortedMilestones = computed(() => {
  if (!project.value?.milestones) return []
  return [...project.value.milestones].sort((a, b) => {
    if (!a.due_date) return 1
    if (!b.due_date) return -1
    return a.due_date.localeCompare(b.due_date)
  })
})

// ====== 成员每月评分相关（与电脑端保持一致）======
interface MemberScoreItem {
  member_id: number
  member_name: string
  sub_team_id: number
  sub_team_name: string
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
      scores: (row.scores || []).reduce((acc, s) => {
        acc[s.label] = s.score != null ? s.score : null
        return acc
      }, {} as Record<string, number | null>),
    }))
  } catch (e: any) {
    console.error('[MobileProjectDetail] fetchMemberScores error:', e)
    memberScores.value = []
  }
}

const getMemberScore = (memberId: number, _subTeamId: number): number | null => {
  const item = memberScores.value.find(m => m.member_id === memberId)
  if (!item || !item.scores) return null
  const months = Object.keys(item.scores).sort().reverse()
  for (const m of months) {
    if (item.scores[m] !== null && item.scores[m] !== undefined) {
      return item.scores[m]
    }
  }
  return null
}

const getMemberScoreText = (memberId: number, subTeamId: number): string => {
  const score = getMemberScore(memberId, subTeamId)
  if (score === null) return '未评'
  return `${score}分`
}

const memberScoreClass = (score: number | null): string => {
  if (score === null) return ''
  if (score >= 4) return 'score-high'
  if (score >= 3) return 'score-mid'
  return 'score-low'
}

const showMemberScoreInfo = (member: any, subTeam: any) => {
  const score = getMemberScore(member.id, subTeam.id)
  const text = score !== null ? `${score} 分` : '暂无评分'
  alert(`${member.name} (${subTeam.name})\n最新专项绩效：${text}`)
}
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
  padding: 16px;
}

.project-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
}

.hero-left h1 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
}

.hero-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item {
  font-size: 12px;
  color: var(--text-secondary);
}

.status-badge {
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.healthy { background: var(--accent-green); color: white; }
.status-badge.warning { background: var(--accent-orange); color: white; }
.status-badge.risk { background: var(--accent-red); color: white; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.kpi-item {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.kpi-label {
  display: block;
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 20px;
  font-weight: 700;
}

.kpi-value.green { color: var(--accent-green); }

.kpi-hint {
  font-size: 14px;
  color: var(--text-muted);
  margin-left: 2px;
}

.progress-bar {
  height: 6px;
  background: var(--border-subtle);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 4px;
}

.goals-section {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
}

.tab-section {
  background: var(--bg-card);
  padding: 16px;
  border-radius: 12px;
}

.tab-bar {
  display: flex;
  border-bottom: 2px solid var(--border-subtle);
  margin-bottom: 12px;
}

.tab-btn {
  flex: 1;
  padding: 10px 0;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.empty-hint {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.timeline {
  padding: 4px 0;
}

.tl-item {
  display: flex;
  gap: 12px;
  min-height: 60px;
}

.tl-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}

.tl-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--text-muted);
  border: 2px solid var(--bg-card);
  box-shadow: 0 0 0 2px var(--text-muted);
  flex-shrink: 0;
  margin-top: 4px;
}

.tl-dot.done {
  background: var(--accent-green);
  box-shadow: 0 0 0 2px var(--accent-green);
}

.tl-line {
  width: 2px;
  flex: 1;
  background: var(--border-subtle);
  margin: 4px 0;
}

.tl-content {
  flex: 1;
  padding-bottom: 16px;
}

.tl-date {
  font-size: 11px;
  color: var(--accent-blue);
  font-weight: 600;
  margin-bottom: 2px;
}

.tl-title {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

.tl-group {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.tl-badge {
  display: inline-block;
  margin-top: 4px;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
}

.goals-section h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

.goals-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.goal-item {
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
}

.goal-top {
  margin-bottom: 8px;
}

.goal-name {
  font-size: 13px;
  font-weight: 600;
}

.goal-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid rgba(128, 128, 128, 0.08);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-value {
  font-size: 13px;
  font-weight: 500;
}

.detail-value.score {
  font-size: 18px;
  font-weight: 700;
}

.detail-value.score.green { color: var(--accent-green); }
.detail-value.score.orange { color: var(--accent-orange); }
.detail-value.score.red { color: var(--accent-red); }
.detail-value.score.muted { color: var(--text-muted); font-size: 14px; }

.detail-value.actual {
  color: var(--accent-blue);
  font-weight: 600;
}

.progress-fill.green { background: var(--accent-green); }
.progress-fill.orange { background: var(--accent-orange); }
.progress-fill.red { background: var(--accent-red); }
.progress-fill.gray { background: var(--text-muted); }

.project-score-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--accent-blue);
  font-size: 13px;
}

.summary-score {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-blue);
}

.loading {
  padding: 40px;
  text-align: center;
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

/* 子团队样式 */
.subteams-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.subteam-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 14px;
}

.st-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
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
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
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
  flex-direction: column;
  gap: 4px;
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

.st-member-role {
  font-size: 11px;
  color: var(--text-secondary);
}

.st-no-members {
  color: var(--text-muted);
  font-size: 12px;
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

.report-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  overflow: hidden;
}

.report-title {
  font-size: 14px;
  font-weight: 600;
  padding: 12px 12px 0;
}

.report-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 12px 0;
}

.report-title-row .report-title {
  padding: 0;
}

.pdf-link {
  font-size: 12px;
  color: var(--accent-blue);
  text-decoration: none;
  padding: 3px 8px;
  border: 1px solid var(--accent-blue);
  border-radius: 4px;
  white-space: nowrap;
}

.pdf-viewer-mobile {
  padding: 8px 12px;
}

.pdf-iframe-mobile {
  width: 100%;
  height: 400px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  display: block;
}

.pdf-loading {
  text-align: center;
  padding: 24px 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.pdf-pages-scroll {
  -webkit-overflow-scrolling: touch;
}

.pdf-page-img {
  display: block;
  width: 100%;
  margin-bottom: 4px;
  border-radius: 4px;
}

.pdf-fallback {
  text-align: center;
  padding: 16px;
}

.btn-fullscreen-mobile {
  display: block;
  width: 100%;
  margin-top: 8px;
  padding: 8px 0;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
}

.pdf-fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  flex-direction: column;
}

.pdf-fullscreen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
}

.pdf-fullscreen-close {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.3);
  background: transparent;
  color: white;
  cursor: pointer;
  font-size: 13px;
}

.pdf-fullscreen-body {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 8px;
}

.pdf-fullscreen-iframe {
  flex: 1;
  width: 100%;
  border: none;
  display: block;
}

.report-body {
  padding: 8px 12px 12px;
}

.md-preview { font-size: 13px; line-height: 1.8; }
.md-preview :deep(h1) { font-size: 18px; font-weight: 700; margin: 12px 0 6px; }
.md-preview :deep(h2) { font-size: 16px; font-weight: 700; margin: 10px 0 4px; }
.md-preview :deep(h3) { font-size: 14px; font-weight: 600; margin: 8px 0 4px; }
.md-preview :deep(p) { margin: 4px 0; }
.md-preview :deep(ul), .md-preview :deep(ol) { padding-left: 20px; margin: 4px 0; }
.md-preview :deep(li) { margin: 2px 0; }
.md-preview :deep(table) { width: 100%; border-collapse: collapse; margin: 6px 0; }
.md-preview :deep(th), .md-preview :deep(td) { border: 1px solid var(--border-subtle); padding: 4px 8px; font-size: 12px; }
.md-preview :deep(th) { background: var(--bg-card); font-weight: 600; }
.md-preview :deep(strong) { font-weight: 700; }
.md-preview :deep(blockquote) { border-left: 3px solid var(--accent-blue); padding-left: 10px; color: var(--text-secondary); margin: 6px 0; }
.md-preview :deep(code) { background: var(--bg-card); padding: 1px 3px; border-radius: 3px; font-size: 12px; }
.md-preview :deep(pre) { background: var(--bg-card); padding: 10px; border-radius: 6px; overflow-x: auto; }
.md-preview :deep(pre code) { background: none; padding: 0; }

.goal-desc-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; margin-left: 4px; font-size: 11px; font-weight: 700;
  color: var(--accent-blue); background: rgba(59,130,246,0.12); border-radius: 50%;
  cursor: pointer; vertical-align: middle; flex-shrink: 0;
}
.desc-modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
  padding: 16px;
}
.desc-modal-box {
  background: var(--bg-card, #1e293b); border-radius: 12px; padding: 20px;
  max-width: 400px; width: 100%; max-height: 70vh;
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  display: flex; flex-direction: column;
  box-sizing: border-box;
}
.desc-modal-box h3 { margin: 0 0 12px; font-size: 15px; color: var(--text-primary, #e2e8f0); }
.desc-content {
  line-height: 1.7; color: var(--text-secondary, #94a3b8);
  white-space: pre-wrap; margin: 0 0 16px; font-size: 13px;
  overflow-y: auto; flex: 1;
}
.desc-close-btn {
  padding: 8px 0; background: var(--accent-blue, #3b82f6); color: #fff;
  border: none; border-radius: 8px; cursor: pointer; font-size: 14px; width: 100%;
}
</style>
