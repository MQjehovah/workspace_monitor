<template>
  <div class="admin">
    <header class="admin-header">
      <div class="header-left">
        <router-link to="/special-dashboard" class="back-link">&larr; 返回看板</router-link>
        <h1>特殊专项管理</h1>
      </div>
      <div class="header-right">
        <button class="btn-sm-header btn-primary" @click="openAddProject">+ 新增特殊专项</button>
        <button v-if="selectedProjectId" class="btn-sm-header btn-edit-header" @click="openEditProject">编辑专项</button>
        <button v-if="selectedProjectId" class="btn-sm-header btn-danger-header" @click="handleDeleteProject">删除专项</button>
        <select v-model="selectedProjectId" class="project-select" @change="loadGoals">
          <option value="">选择特殊专项</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </header>

    <div v-if="!selectedProjectId" class="empty-state">
      <p>请从右上角选择一个特殊专项进行管理</p>
    </div>

    <div v-else class="admin-content">
      <div class="toolbar">
        <div class="toolbar-left">
          <h2>{{ currentProject?.name }}<span class="special-badge">特殊专项</span></h2>
          <span class="toolbar-info">综合得分：<strong>{{ currentProject?.score?.toFixed(1) }}</strong></span>
          <div class="progress-setter">
            <label>进度设定</label>
            <div class="score-slider">
              <input type="range" class="slider" min="0" max="100" v-model.number="progressValue" @change="saveProgress" />
              <span class="slider-val">{{ progressValue }}%</span>
            </div>
          </div>
        </div>
        <div class="toolbar-right">
          <div class="admin-tabs">
            <button class="admin-tab" :class="{ active: adminTab === 'goals' }" @click="adminTab = 'goals'">目标评分</button>
            <button class="admin-tab" :class="{ active: adminTab === 'milestones' }" @click="adminTab = 'milestones'">里程碑</button>
            <button class="admin-tab" :class="{ active: adminTab === 'subteams' }" @click="adminTab = 'subteams'">子团队管理</button>
            <button class="admin-tab" :class="{ active: adminTab === 'reports' }" @click="adminTab = 'reports'">月度报告</button>
          </div>
          <div style="margin-top: 20px;">
              <button v-if="adminTab === 'goals'" class="btn-primary" @click="openAddGoal">+ 添加目标</button>
              <button v-else-if="adminTab === 'milestones'" class="btn-primary" @click="openAddMilestone">+ 添加里程碑</button>
              <button v-else-if="adminTab === 'subteams'" class="btn-primary" @click="openAddSubTeam">+ 添加子团队</button>
              <button v-else class="btn-primary" @click="openAddReport">+ 新增月报</button>
          </div>
        </div>
      </div>

      <template v-if="adminTab === 'goals'">
        <table class="goal-table" v-if="goals.length > 0">
        <thead>
          <tr>
            <th style="width: 30px">#</th>
            <th>目标名称</th>
            <th style="width: 100px">最新评分</th>
            <th style="width: 100px">评分月份</th>
            <th style="width: 90px">当月目标</th>
            <th style="width: 90px">当月实际</th>
            <th style="width: 80px">月完成率</th>
            <th style="width: 90px">年度实际</th>
            <th style="width: 80px">年完成率</th>
            <th style="width: 240px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(goal, idx) in goals" :key="goal.id">
            <td class="center">{{ idx + 1 }}</td>
            <td>
              {{ goal.name }}
              <span v-if="goal.unit" class="goal-unit-tag">({{ goal.unit }})</span>
              <span v-if="goal.key_project_id" class="key-project-tag">{{ getKeyProjectName(goal.key_project_id) }}</span>
              <span v-if="goal.description" class="goal-desc-icon" @click.stop="showGoalDesc(goal)" title="查看描述">?</span>
            </td>
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
            <td class="center muted">{{ goal.latest_monthly_value != null ? goal.latest_monthly_value : '-' }}</td>
            <td class="center muted">{{ goal.latest_monthly_actual != null ? goal.latest_monthly_actual : '-' }}</td>
            <td class="center muted">{{ goal.latest_monthly_rate != null ? goal.latest_monthly_rate.toFixed(1) + '%' : '-' }}</td>
            <td class="center muted">{{ goal.latest_yearly_value != null ? goal.latest_yearly_value : '-' }}</td>
            <td class="center muted">{{ goal.latest_yearly_rate != null ? goal.latest_yearly_rate.toFixed(1) + '%' : '-' }}</td>
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

      <template v-if="adminTab === 'reports'">
        <table class="goal-table" v-if="reports.length > 0">
          <thead>
            <tr>
              <th style="width: 120px">年月</th>
              <th>报告摘要</th>
              <th style="width: 80px">PDF</th>
              <th style="width: 150px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reports" :key="r.id">
              <td class="center">{{ r.year }}年{{ r.month }}月</td>
              <td class="muted" style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ r.content.substring(0, 80) || '（空）' }}</td>
              <td class="center">{{ r.pdf_path ? '已上传' : '-' }}</td>
              <td>
                <div class="action-btns">
                  <button class="btn-sm btn-edit" @click="openEditReport(r)">编辑</button>
                  <button class="btn-sm btn-danger" @click="handleDeleteReport(r.id)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">暂无月度报告，请点击「新增月报」</div>
      </template>

      <template v-if="adminTab === 'subteams'">
        <div v-if="subTeams.length > 0" class="subteams-container">
          <div v-for="st in subTeams" :key="st.id" class="subteam-card">
            <div class="subteam-header">
              <div class="subteam-info">
                <h3 class="subteam-name">{{ st.name }}</h3>
                <span v-if="st.leader" class="subteam-leader">负责人：{{ st.leader }}</span>
                <span class="subteam-member-count">{{ st.members.length }} 人</span>
              </div>
              <div class="subteam-actions">
                <button class="btn-sm btn-edit" @click="openEditSubTeam(st)">编辑</button>
                <button class="btn-sm btn-score" @click="openSubTeamRatingModal(st)">月度评级</button>
                <button class="btn-sm btn-history" @click="openSubTeamRatingHistory(st)">评级记录</button>
                <button class="btn-sm btn-danger" @click="handleDeleteSubTeam(st.id)">删除</button>
              </div>
            </div>
            <div class="subteam-members">
              <div class="members-header">
                <span class="members-title">团队成员</span>
                <button class="btn-sm btn-add-member" @click="openAddMember(st)">+ 添加成员</button>
              </div>
              <div v-if="st.members.length > 0" class="members-list">
                <div v-for="m in st.members" :key="m.id" class="member-item">
                  <span class="member-name">{{ m.name }}</span>
                  <span v-if="m.role" class="member-role">{{ m.role }}</span>
                  <div class="member-actions">
                    <button class="btn-sm btn-edit btn-member-edit" @click="openEditMember(m)">编辑</button>
                    <button class="btn-sm btn-danger btn-member-del" @click="handleDeleteMember(m.id)">移除</button>
                  </div>
                </div>
              </div>
              <div v-else class="empty-members">暂无成员，请点击「添加成员」</div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">暂无子团队，请点击「添加子团队」</div>
      </template>
    </div>

    <transition name="modal">
      <div v-if="showGoalModal" class="modal-mask" @click.self="showGoalModal = false">
        <div class="modal-box">
          <h3>{{ editingGoalId ? '编辑目标' : '添加目标' }}</h3>
          <div class="form-group">
            <label>目标名称</label>
            <input v-model="goalForm.name" class="form-input" placeholder="目标名称" />
          </div>
          <div class="form-group">
            <label>目标描述（可选）</label>
            <textarea v-model="goalForm.description" class="form-input form-textarea" placeholder="目标描述"></textarea>
          </div>
          <div class="form-group">
            <label>关键项目（可选）</label>
            <select v-model.number="goalForm.key_project_id" class="form-input">
              <option :value="null">-- 不关联 --</option>
              <option v-for="kp in keyProjects" :key="kp.id" :value="kp.id">{{ kp.name }}</option>
            </select>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showGoalModal = false">取消</button>
            <button class="btn-primary" @click="handleSaveGoal">{{ editingGoalId ? '保存' : '添加' }}</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showDescModal" class="modal-mask" @click.self="showDescModal = false">
        <div class="modal-box">
          <h3>{{ descGoalName }}</h3>
          <div class="md-preview">{{ descGoalContent }}</div>
          <div class="modal-footer">
            <button class="btn-primary" @click="showDescModal = false">关闭</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="scoringGoal" class="modal-mask" @click.self="scoringGoal = null">
        <div class="modal-box wide">
          <h3>评分：{{ scoringGoal.name }}</h3>
          <div class="form-row">
            <div class="form-group half">
              <label>年份</label>
              <select v-model="scoreForm.year" class="form-input">
                <option v-for="y in [2024, 2025, 2026, 2027]" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
            <div class="form-group half">
              <label>月份</label>
              <select v-model="scoreForm.month" class="form-input">
                <option v-for="m in 12" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>评分</label>
            <div class="score-slider">
              <input type="range" class="slider" min="0" max="100" v-model.number="scoreForm.score" />
              <span class="slider-val">{{ scoreForm.score }}</span>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>当月目标值</label>
              <input type="text" v-model="scoreForm.monthly_value" class="form-input" placeholder="如：5h" />
            </div>
            <div class="form-group half">
              <label>当月实际值</label>
              <input type="text" v-model="scoreForm.actual_value" class="form-input" placeholder="如：3.5h" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>月度完成率 (%)</label>
              <input type="number" v-model.number="scoreForm.monthly_rate" class="form-input" min="0" max="100" />
            </div>
            <div class="form-group half">
              <label>年度完成率 (%)</label>
              <input type="number" v-model.number="scoreForm.yearly_rate" class="form-input" min="0" max="100" />
            </div>
          </div>
          <div class="form-group">
            <label>年度实际值</label>
            <input type="text" v-model="scoreForm.yearly_value" class="form-input" placeholder="年度累计" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="scoreForm.comment" class="form-input form-textarea" placeholder="备注说明"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="scoringGoal = null">取消</button>
            <button class="btn-primary" @click="handleScoreGoal">保存评分</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="historyGoal" class="modal-mask" @click.self="historyGoal = null">
        <div class="modal-box wide tall">
          <h3>评分历史：{{ historyGoal.name }}</h3>
          <table class="history-table" v-if="historyScores.length > 0">
            <thead>
              <tr>
                <th>年月</th>
                <th>评分</th>
                <th>月度目标</th>
                <th>月度实际</th>
                <th>月完成率</th>
                <th>年度实际</th>
                <th>年完成率</th>
                <th>备注</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in historyScores" :key="s.id">
                <td>{{ s.year }}/{{ s.month }}</td>
                <td class="center">{{ s.score.toFixed(1) }}</td>
                <td>{{ s.monthly_value || '-' }}</td>
                <td>{{ s.actual_value || '-' }}</td>
                <td class="center">{{ s.monthly_rate != null ? s.monthly_rate.toFixed(1) + '%' : '-' }}</td>
                <td>{{ s.yearly_value || '-' }}</td>
                <td class="center">{{ s.yearly_rate != null ? s.yearly_rate.toFixed(1) + '%' : '-' }}</td>
                <td class="muted">{{ s.comment || '-' }}</td>
                <td><button class="btn-sm btn-danger" @click="handleDeleteScore(s.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">暂无评分记录</div>
          <div class="modal-footer">
            <button class="btn-primary" @click="historyGoal = null">关闭</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showMsModal" class="modal-mask" @click.self="showMsModal = false">
        <div class="modal-box">
          <h3>{{ editingMsId ? '编辑里程碑' : '添加里程碑' }}</h3>
          <div class="form-group">
            <label>分组名称（可选）</label>
            <input v-model="msForm.group_name" class="form-input" placeholder="分组名称" />
          </div>
          <div class="form-group">
            <label>事件描述</label>
            <input v-model="msForm.event" class="form-input" placeholder="事件描述" />
          </div>
          <div class="form-group">
            <label>截止日期</label>
            <input v-model="msForm.due_date" class="form-input" type="date" placeholder="截止日期" />
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showMsModal = false">取消</button>
            <button class="btn-primary" @click="handleSaveMilestone">{{ editingMsId ? '保存' : '添加' }}</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showReportModal" class="modal-mask" @click.self="showReportModal = false">
        <div class="modal-box wide tall">
          <h3>{{ editingReportId ? '编辑月度报告' : '新增月度报告' }}</h3>
          <div class="form-row" v-if="!editingReportId">
            <div class="form-group half">
              <label>年份</label>
              <select v-model.number="reportForm.year" class="form-input">
                <option v-for="y in [2025, 2026, 2027]" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
            <div class="form-group half">
              <label>月份</label>
              <select v-model.number="reportForm.month" class="form-input">
                <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
              </select>
            </div>
          </div>
          <div v-else class="report-editing-hint">
            {{ reportForm.year }}年{{ reportForm.month }}月
          </div>
          <div class="form-group">
            <label>PDF 附件</label>
            <div v-if="reportPdfPath" class="pdf-info">
              <span class="pdf-badge">PDF</span>
              <span class="pdf-name">{{ reportPdfName }}</span>
              <button class="btn-sm btn-danger" @click="handleRemovePdf" :disabled="reportUploading">删除</button>
            </div>
            <div class="pdf-upload-area">
              <input type="file" ref="pdfInputRef" accept=".pdf" @change="handlePdfSelect" class="pdf-file-input" />
              <button class="btn-primary pdf-upload-btn" @click="($refs.pdfInputRef as HTMLInputElement)?.click()" :disabled="reportUploading">
                {{ reportUploading ? '上传中...' : '选择 PDF 文件' }}
              </button>
              <span v-if="reportPendingPdf" class="pdf-pending-name">{{ reportPendingPdf.name }}</span>
            </div>
          </div>
          <div class="form-group">
            <div class="report-editor-header">
              <label>报告内容（Markdown 格式）</label>
              <div class="editor-toggle">
                <button class="toggle-btn" :class="{ active: !reportPreview }" @click="reportPreview = false">编辑</button>
                <button class="toggle-btn" :class="{ active: reportPreview }" @click="reportPreview = true">预览</button>
              </div>
            </div>
            <textarea v-if="!reportPreview" v-model="reportForm.content" class="form-input form-textarea md-editor" rows="16" placeholder="请输入 Markdown 格式的月度报告内容&#10;&#10;支持标题、列表、表格、加粗等格式"></textarea>
            <div v-else class="md-preview" v-html="renderMarkdown(reportForm.content)"></div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showReportModal = false" :disabled="reportSaving">取消</button>
            <button class="btn-primary" @click="handleSaveReport" :disabled="reportSaving">
              {{ reportSaving ? (reportUploading ? '正在上传 PDF...' : '保存中...') : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showSubTeamModal" class="modal-mask" @click.self="showSubTeamModal = false">
        <div class="modal-box">
          <h3>{{ editingSubTeamId ? '编辑子团队' : '添加子团队' }}</h3>
          <div class="form-group">
            <label>子团队名称</label>
            <input v-model="subTeamForm.name" class="form-input" placeholder="子团队名称" />
          </div>
          <div class="form-group">
            <label>负责人（可选）</label>
            <input v-model="subTeamForm.leader" class="form-input" placeholder="负责人" />
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showSubTeamModal = false">取消</button>
            <button class="btn-primary" @click="handleSaveSubTeam">{{ editingSubTeamId ? '保存' : '添加' }}</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showMemberModal" class="modal-mask" @click.self="showMemberModal = false">
        <div class="modal-box">
          <h3>添加成员</h3>
          <div class="form-group">
            <label>成员姓名</label>
            <input v-model="memberForm.name" class="form-input" placeholder="成员姓名" />
          </div>
          <div class="form-group">
            <label>角色（可选）</label>
            <input v-model="memberForm.role" class="form-input" placeholder="角色" />
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showMemberModal = false">取消</button>
            <button class="btn-primary" @click="handleAddMember">添加</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showEditMemberModal" class="modal-mask" @click.self="showEditMemberModal = false">
        <div class="modal-box">
          <h3>编辑成员</h3>
          <div class="form-group">
            <label>成员姓名</label>
            <input v-model="editMemberForm.name" class="form-input" placeholder="成员姓名" />
          </div>
          <div class="form-group">
            <label>角色（可选）</label>
            <input v-model="editMemberForm.role" class="form-input" placeholder="角色" />
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showEditMemberModal = false">取消</button>
            <button class="btn-primary" @click="handleEditMember">保存</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="ratingTargetTeam" class="modal-mask" @click.self="ratingTargetTeam = null">
        <div class="modal-box">
          <h3>月度评级：{{ ratingTargetTeam.name }}</h3>
          <div class="form-row">
            <div class="form-group half">
              <label>年份</label>
              <select v-model="ratingForm.year" class="form-input">
                <option v-for="y in [2024, 2025, 2026, 2027]" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
            <div class="form-group half">
              <label>月份</label>
              <select v-model="ratingForm.month" class="form-input">
                <option v-for="m in 12" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>评级</label>
            <select v-model="ratingForm.rating" class="form-input">
              <option value="达成">达成</option>
              <option value="未达成">未达成</option>
            </select>
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="ratingForm.comment" class="form-input form-textarea" placeholder="备注说明"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="ratingTargetTeam = null">取消</button>
            <button class="btn-primary" @click="handleSaveRating">保存评级</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="ratingHistoryTeam" class="modal-mask" @click.self="ratingHistoryTeam = null">
        <div class="modal-box">
          <h3>评级历史：{{ ratingHistoryTeam.name }}</h3>
          <table class="history-table" v-if="ratingHistoryData.length > 0">
            <thead>
              <tr>
                <th>年月</th>
                <th>评级</th>
                <th>备注</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in ratingHistoryData" :key="r.id">
                <td>{{ r.year }}/{{ r.month }}</td>
                <td class="center"><span class="rating-tag" :class="getRatingClass(r.rating)">{{ r.rating }}</span></td>
                <td class="muted">{{ r.comment || '-' }}</td>
                <td><button class="btn-sm btn-danger" @click="handleDeleteRating(r.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">暂无评级记录</div>
          <div class="modal-footer">
            <button class="btn-primary" @click="ratingHistoryTeam = null">关闭</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="modal">
      <div v-if="showProjectModal" class="modal-mask" @click.self="showProjectModal = false">
        <div class="modal-box">
          <h3>{{ editingProjectId ? '编辑专项' : '新增特殊专项' }}</h3>
          <div class="form-group">
            <label>专项名称</label>
            <input v-model="projectForm.name" class="form-input" placeholder="专项名称" />
          </div>
          <div class="form-group">
            <label>负责人（可选）</label>
            <input v-model="projectForm.owner" class="form-input" placeholder="负责人" />
          </div>
          <div class="form-group">
            <label>所属部门（可选）</label>
            <input v-model="projectForm.department" class="form-input" placeholder="所属部门" />
          </div>
          <div class="form-group">
            <label>目标日期（可选）</label>
            <input v-model="projectForm.target_date" class="form-input" type="date" placeholder="目标日期" />
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showProjectModal = false">取消</button>
            <button class="btn-primary" @click="handleSaveProject">{{ editingProjectId ? '保存' : '创建' }}</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="toast">
      <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { getSpecialProjects, getGoalScores, getMilestones, createMilestone, updateMilestone, deleteMilestone, updateProject, createProject as createProjectApi, deleteProject, createReport, updateReport, deleteReport, uploadReportPdf, deleteReportPdf, createSubTeam, updateSubTeam, deleteSubTeam, addSubTeamMember, updateSubTeamMember, deleteSubTeamMember, upsertSubTeamRating, getSubTeamRatings, deleteSubTeamRating, getProject, getProjectGoals, createGoal, updateGoal, deleteGoal, upsertGoalScore, deleteScore, getReports, getKeyProjects } from '@/api'
import type { GoalWithLatestScore, GoalScore, Milestone as MilestoneType, MonthlyReport as MonthlyReportType, SubTeam as SubTeamType, SubTeamMember as SubTeamMemberType, SubTeamRating as SubTeamRatingType, Project, KeyProject } from '@/api'
import dayjs from 'dayjs'

const projects = ref<Project[]>([])
const selectedProjectId = ref<number | string>('')
const goals = ref<GoalWithLatestScore[]>([])
const currentProject = computed(() =>
  projects.value.find(p => p.id === Number(selectedProjectId.value)) ?? null
)

const showGoalModal = ref(false)
const editingGoalId = ref<number | null>(null)
const goalForm = reactive({ name: '', description: '', unit: '', key_project_id: null as number | null })
const keyProjects = ref<KeyProject[]>([])
const loadKeyProjects = async () => {
  const res = await getKeyProjects()
  keyProjects.value = res.data
}
const getKeyProjectName = (id: number) => keyProjects.value.find(kp => kp.id === id)?.name || ''

const descGoalName = ref('')
const descGoalContent = ref('')
const showDescModal = ref(false)

const showGoalDesc = (goal: GoalWithLatestScore) => {
  descGoalName.value = goal.name
  descGoalContent.value = goal.description || '暂无描述'
  showDescModal.value = true
}

const scoringGoal = ref<GoalWithLatestScore | null>(null)
const scoreForm = reactive({
  year: dayjs().year(),
  month: dayjs().month() + 1,
  score: 80,
  comment: '',
  monthly_value: '',
  actual_value: '',
  monthly_rate: 0,
  yearly_value: '',
  yearly_rate: 0,
})

const historyGoal = ref<GoalWithLatestScore | null>(null)
const historyScores = ref<GoalScore[]>([])

const adminTab = ref<'goals' | 'milestones' | 'subteams' | 'reports'>('goals')
const milestones = ref<MilestoneType[]>([])
const reports = ref<MonthlyReportType[]>([])
const showMsModal = ref(false)
const editingMsId = ref<number | null>(null)
const msForm = reactive({ event: '', group_name: '', due_date: '' })

const showReportModal = ref(false)
const editingReportId = ref<number | null>(null)
const reportForm = reactive({ year: dayjs().year(), month: dayjs().month() + 1, content: '' })
const reportPreview = ref(false)
const reportPdfPath = ref<string | null>(null)
const reportUploading = ref(false)
const reportSaving = ref(false)
const reportPendingPdf = ref<File | null>(null)
const pdfInputRef = ref<HTMLInputElement | null>(null)

const progressValue = ref(0)

const subTeams = ref<SubTeamType[]>([])
const showSubTeamModal = ref(false)
const editingSubTeamId = ref<number | null>(null)
const subTeamForm = reactive({ name: '', leader: '', membersText: '' })

const showMemberModal = ref(false)
const memberTargetTeam = ref<SubTeamType | null>(null)
const memberForm = reactive({ name: '', role: '' })

const showEditMemberModal = ref(false)
const editingMember = ref<SubTeamMemberType | null>(null)
const editMemberForm = reactive({ name: '', role: '' })

const ratingTargetTeam = ref<SubTeamType | null>(null)
const ratingForm = reactive({ year: dayjs().year(), month: dayjs().month() + 1, rating: '达成', comment: '' })

const ratingHistoryTeam = ref<SubTeamType | null>(null)
const ratingHistoryData = ref<SubTeamRatingType[]>([])

const getRatingClass = (rating: string) => {
  if (rating === '达成') return 'green'
  return 'red'
}

const openAddSubTeam = () => {
  editingSubTeamId.value = null
  subTeamForm.name = ''
  subTeamForm.leader = ''
  subTeamForm.membersText = ''
  showSubTeamModal.value = true
}

const openEditSubTeam = (st: SubTeamType) => {
  editingSubTeamId.value = st.id
  subTeamForm.name = st.name
  subTeamForm.leader = st.leader || ''
  showSubTeamModal.value = true
}

const handleSaveSubTeam = async () => {
  if (!subTeamForm.name.trim() || !selectedProjectId.value) return
  if (editingSubTeamId.value) {
    await updateSubTeam(editingSubTeamId.value, {
      name: subTeamForm.name.trim(),
      leader: subTeamForm.leader.trim() || undefined,
    })
  } else {
    await createSubTeam(Number(selectedProjectId.value), {
      name: subTeamForm.name.trim(),
      leader: subTeamForm.leader.trim() || undefined,
      members: [],
    })
  }
  showSubTeamModal.value = false
  await loadSubTeams()
}

const handleDeleteSubTeam = async (id: number) => {
  if (!confirm('确定删除该子团队？')) return
  await deleteSubTeam(id)
  await loadSubTeams()
}

const openAddMember = (st: SubTeamType) => {
  memberTargetTeam.value = st
  memberForm.name = ''
  memberForm.role = ''
  showMemberModal.value = true
}

const openEditMember = (m: SubTeamMemberType) => {
  editingMember.value = m
  editMemberForm.name = m.name
  editMemberForm.role = m.role || ''
  showEditMemberModal.value = true
}

const handleAddMember = async () => {
  if (!memberForm.name.trim() || !memberTargetTeam.value) return
  await addSubTeamMember(memberTargetTeam.value.id, {
    name: memberForm.name.trim(),
    role: memberForm.role.trim() || undefined,
  })
  showMemberModal.value = false
  await loadSubTeams()
}

const handleEditMember = async () => {
  if (!editingMember.value) return
  await updateSubTeamMember(editingMember.value.id, {
    name: editMemberForm.name.trim(),
    role: editMemberForm.role.trim() || undefined,
  })
  showEditMemberModal.value = false
  await loadSubTeams()
}

const handleDeleteMember = async (id: number) => {
  if (!confirm('确定移除该成员？')) return
  await deleteSubTeamMember(id)
  await loadSubTeams()
}

const openSubTeamRatingModal = (st: SubTeamType) => {
  ratingTargetTeam.value = st
  ratingForm.year = dayjs().year()
  ratingForm.month = dayjs().month() + 1
  ratingForm.rating = '达成'
  ratingForm.comment = ''
}

const handleSaveRating = async () => {
  if (!ratingTargetTeam.value) return
  await upsertSubTeamRating(ratingTargetTeam.value.id, {
    year: ratingForm.year,
    month: ratingForm.month,
    rating: ratingForm.rating,
    comment: ratingForm.comment.trim() || undefined,
  })
  ratingTargetTeam.value = null
  await loadSubTeams()
}

const openSubTeamRatingHistory = async (st: SubTeamType) => {
  ratingHistoryTeam.value = st
  const res = await getSubTeamRatings(st.id)
  ratingHistoryData.value = res.data
}

const handleDeleteRating = async (id: number) => {
  if (!confirm('确定删除该评级记录？')) return
  await deleteSubTeamRating(id)
  if (ratingHistoryTeam.value) {
    await openSubTeamRatingHistory(ratingHistoryTeam.value)
  }
}

const scoreTagClass = (score: number) => {
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const openAddGoal = () => {
  editingGoalId.value = null
  goalForm.name = ''
  goalForm.description = ''
  goalForm.unit = ''
  goalForm.key_project_id = null
  showGoalModal.value = true
}

const openEditGoal = (goal: GoalWithLatestScore) => {
  editingGoalId.value = goal.id
  goalForm.name = goal.name
  goalForm.description = goal.description || ''
  goalForm.unit = goal.unit || ''
  goalForm.key_project_id = (goal as any).key_project_id ?? null
  showGoalModal.value = true
}

const handleSaveGoal = async () => {
  if (!goalForm.name.trim() || !selectedProjectId.value) return
  if (editingGoalId.value) {
    await updateGoal(editingGoalId.value, {
      name: goalForm.name.trim(),
      description: goalForm.description.trim() || undefined,
      unit: goalForm.unit.trim() || undefined,
      key_project_id: goalForm.key_project_id ?? undefined,
    })
  } else {
    await createGoal(Number(selectedProjectId.value), {
      name: goalForm.name.trim(),
      description: goalForm.description.trim() || undefined,
      key_project_id: goalForm.key_project_id ?? undefined,
    })
  }
  showGoalModal.value = false
  await loadGoals()
}

const handleDeleteGoal = async (goal: GoalWithLatestScore) => {
  if (!confirm(`确定删除目标「${goal.name}」？`)) return
  await deleteGoal(goal.id)
  await loadGoals()
}

const openScoreModal = (goal: GoalWithLatestScore) => {
  scoringGoal.value = goal
  scoreForm.year = goal.latest_year || dayjs().year()
  scoreForm.month = goal.latest_month || dayjs().month() + 1
  scoreForm.score = goal.latest_score || 80
  scoreForm.comment = goal.latest_comment || ''
  scoreForm.monthly_value = goal.latest_monthly_value || ''
  scoreForm.actual_value = goal.latest_monthly_actual || ''
  scoreForm.monthly_rate = goal.latest_monthly_rate || 0
  scoreForm.yearly_value = goal.latest_yearly_value || ''
  scoreForm.yearly_rate = goal.latest_yearly_rate || 0
}

const handleScoreGoal = async () => {
  if (!scoringGoal.value) return
  await upsertGoalScore(scoringGoal.value.id, {
    year: scoreForm.year,
    month: scoreForm.month,
    score: scoreForm.score,
    comment: scoreForm.comment.trim() || undefined,
    monthly_value: scoreForm.monthly_value.trim() || undefined,
    actual_value: scoreForm.actual_value.trim() || undefined,
    monthly_rate: scoreForm.monthly_rate || undefined,
    yearly_value: scoreForm.yearly_value.trim() || undefined,
    yearly_rate: scoreForm.yearly_rate || undefined,
  })
  scoringGoal.value = null
  await loadGoals()
}

const openHistoryModal = async (goal: GoalWithLatestScore) => {
  historyGoal.value = goal
  const res = await getGoalScores(goal.id)
  historyScores.value = res.data
}

const handleDeleteScore = async (scoreId: number) => {
  if (!confirm('确定删除该评分记录？')) return
  await deleteScore(scoreId)
  if (historyGoal.value) {
    await openHistoryModal(historyGoal.value)
  }
}

const loadGoals = async () => {
  if (!selectedProjectId.value) {
    goals.value = []
    progressValue.value = 0
    return
  }
  const res = await getProject(Number(selectedProjectId.value))
  goals.value = res.data.goals
  progressValue.value = res.data.progress || 0
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
  if (editingMsId.value) {
    await updateMilestone(editingMsId.value, {
      event: msForm.event.trim(),
      group_name: msForm.group_name.trim() || undefined,
      due_date: msForm.due_date || undefined,
    })
  } else {
    await createMilestone(Number(selectedProjectId.value), {
      event: msForm.event.trim(),
      group_name: msForm.group_name.trim() || undefined,
      due_date: msForm.due_date || undefined,
    })
  }
  showMsModal.value = false
  await loadMilestones()
}

const handleDeleteMilestone = async (id: number) => {
  if (!confirm('确定删除该里程碑？')) return
  await deleteMilestone(id)
  await loadMilestones()
}

const toggleMilestone = async (ms: MilestoneType) => {
  await updateMilestone(ms.id, { achieved: !ms.achieved })
  await loadMilestones()
}

const loadMilestones = async () => {
  if (!selectedProjectId.value) {
    milestones.value = []
    return
  }
  const res = await getMilestones(Number(selectedProjectId.value))
  milestones.value = res.data
}

const openAddReport = () => {
  editingReportId.value = null
  reportForm.year = dayjs().year()
  reportForm.month = dayjs().month() + 1
  reportForm.content = ''
  reportPdfPath.value = null
  reportPendingPdf.value = null
  reportPreview.value = false
  showReportModal.value = true
}

const openEditReport = async (r: MonthlyReportType) => {
  editingReportId.value = r.id
  reportForm.year = r.year
  reportForm.month = r.month
  reportForm.content = r.content
  reportPdfPath.value = r.pdf_path || null
  reportPendingPdf.value = null
  reportPreview.value = false
  showReportModal.value = true
}

const reportPdfName = computed(() => {
  if (!reportPdfPath.value) return ''
  return decodeURIComponent(reportPdfPath.value.split('/').pop() || 'report.pdf')
})

const handlePdfSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (editingReportId.value) {
    doPdfUpload(file)
  } else {
    reportPendingPdf.value = file
  }
  input.value = ''
}

const doPdfUpload = async (file: File) => {
  if (!editingReportId.value) return
  reportUploading.value = true
  try {
    const res = await uploadReportPdf(editingReportId.value, file)
    reportPdfPath.value = res.data.pdf_path
    reportPendingPdf.value = null
    showToast('PDF 已上传')
  } catch (e: any) {
    showToast(e?.response?.data?.detail || 'PDF 上传失败', 'error')
  } finally {
    reportUploading.value = false
  }
}

const handleRemovePdf = async () => {
  if (reportPendingPdf.value) {
    reportPendingPdf.value = null
    return
  }
  if (!editingReportId.value) return
  await deleteReportPdf(editingReportId.value)
  reportPdfPath.value = null
  showToast('PDF 已删除', 'warn')
}

const handleSaveReport = async () => {
  if (!selectedProjectId.value) return
  reportSaving.value = true
  try {
    const pid = Number(selectedProjectId.value)
    let reportId = editingReportId.value
    if (reportId) {
      await updateReport(reportId, { content: reportForm.content })
      showToast('月报已更新')
    } else {
      const res = await createReport(pid, {
        year: reportForm.year,
        month: reportForm.month,
        content: reportForm.content,
      })
      reportId = res.data.id
      editingReportId.value = res.data.id
      reportPdfPath.value = res.data.pdf_path
      showToast('月报已创建')
    }
    if (reportPendingPdf.value && reportId) {
      await doPdfUpload(reportPendingPdf.value)
    }
    showReportModal.value = false
    await loadReports()
  } finally {
    reportSaving.value = false
  }
}

const handleDeleteReport = async (id: number) => {
  if (!confirm('确定删除该月度报告？')) return
  await deleteReport(id)
  showToast('月报已删除', 'warn')
  await loadReports()
}

const toast = ref<{ msg: string; type: string } | null>(null)
const showToast = (msg: string, type = 'success') => {
  toast.value = { msg, type }
  setTimeout(() => { toast.value = null }, 2000)
}

const loadReports = async () => {
  if (!selectedProjectId.value) {
    reports.value = []
    return
  }
  const res = await getReports(Number(selectedProjectId.value))
  reports.value = res.data
}

const loadSubTeams = async () => {
  if (!selectedProjectId.value) {
    subTeams.value = []
    return
  }
  const res = await getProject(Number(selectedProjectId.value))
  subTeams.value = res.data.sub_teams
}

const showProjectModal = ref(false)
const editingProjectId = ref<number | null>(null)
const projectForm = reactive({ name: '', owner: '', department: '', target_date: '' })

const saveProgress = async () => {
  if (!selectedProjectId.value) return
  await updateProject(Number(selectedProjectId.value), { progress: progressValue.value })
  await loadProjects()
}

const openAddProject = () => {
  editingProjectId.value = null
  projectForm.name = ''
  projectForm.owner = ''
  projectForm.department = ''
  projectForm.target_date = ''
  showProjectModal.value = true
}

const openEditProject = () => {
  if (!currentProject.value) return
  editingProjectId.value = currentProject.value.id
  projectForm.name = currentProject.value.name
  projectForm.owner = currentProject.value.owner || ''
  projectForm.department = currentProject.value.department || ''
  projectForm.target_date = currentProject.value.target_date || ''
  showProjectModal.value = true
}

const handleSaveProject = async () => {
  if (!projectForm.name.trim()) return
  if (editingProjectId.value) {
    await updateProject(editingProjectId.value, {
      name: projectForm.name.trim(),
      owner: projectForm.owner.trim() || undefined,
      department: projectForm.department.trim() || undefined,
      target_date: projectForm.target_date || undefined,
    })
    selectedProjectId.value = editingProjectId.value
  } else {
    const res = await createProjectApi({
      name: projectForm.name.trim(),
      owner: projectForm.owner.trim() || undefined,
      department: projectForm.department.trim() || undefined,
      target_date: projectForm.target_date || undefined,
      special: 1,
    })
    await loadProjects()
    selectedProjectId.value = res.data.id
  }
  showProjectModal.value = false
  await loadProjects()
  await loadGoals()
}

const handleDeleteProject = async () => {
  if (!currentProject.value) return
  if (!confirm(`确定删除专项「${currentProject.value.name}」？此操作将同时删除其下所有目标、评分和里程碑！`)) return
  await deleteProject(currentProject.value.id)
  selectedProjectId.value = ''
  await loadProjects()
  goals.value = []
  milestones.value = []
}

const loadProjects = async () => {
  const res = await getSpecialProjects()
  projects.value = res.data
}

import MarkdownIt from 'markdown-it'
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const renderMarkdown = (text: string) => md.render(text)

onMounted(async () => {
  await loadProjects()
  await loadKeyProjects()
})
</script>

<style scoped>
.admin {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.goal-unit-tag {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 400;
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

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-sm-header {
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.btn-sm-header.btn-primary {
  background: var(--accent-blue);
  color: white;
}

.btn-edit-header {
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent-blue);
  border: 1px solid var(--accent-blue) !important;
}

.btn-danger-header {
  background: transparent;
  color: var(--accent-red);
  border: 1px solid var(--accent-red) !important;
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

.modal-box.tall {
  max-height: 92vh;
}

.report-editing-hint {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-blue);
  margin-bottom: 12px;
}

.report-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.report-editor-header label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.editor-toggle {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  overflow: hidden;
}

.toggle-btn {
  padding: 3px 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
}

.toggle-btn.active {
  background: var(--accent-blue);
  color: white;
}

.md-editor {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
}

.md-preview {
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 16px;
  max-height: 420px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
}

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

.pdf-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
}

.pdf-badge {
  background: #DC2626;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.pdf-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pdf-upload-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pdf-file-input {
  display: none;
}

.pdf-upload-btn {
  font-size: 12px;
  padding: 6px 14px;
  white-space: nowrap;
}

.pdf-upload-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pdf-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.pdf-pending-name {
  font-size: 12px;
  color: var(--text-secondary);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.progress-setter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid var(--border-subtle);
}

.progress-setter label {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.subteams-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.subteam-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 20px;
}

.subteam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.subteam-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.subteam-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.subteam-leader {
  font-size: 12px;
  color: var(--text-secondary);
}

.subteam-member-count {
  font-size: 11px;
  background: var(--accent-blue);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
}

.subteam-actions {
  display: flex;
  gap: 6px;
}

.subteam-members {
  border-top: 1px solid var(--border-subtle);
  padding-top: 12px;
}

.members-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.members-title {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
}

.btn-add-member {
  background: transparent;
  color: var(--accent-blue);
  border: 1px solid var(--accent-blue) !important;
}

.members-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
}

.member-name {
  font-weight: 600;
}

.member-role {
  color: var(--text-secondary);
  font-size: 11px;
}

.member-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.btn-member-del {
  font-size: 11px;
  padding: 2px 6px;
}

.btn-member-edit {
  font-size: 11px;
  padding: 2px 6px;
}

.empty-members {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

.rating-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.rating-tag.green { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
.rating-tag.red { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }

.special-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 4px;
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
  margin-left: 10px;
}
</style>