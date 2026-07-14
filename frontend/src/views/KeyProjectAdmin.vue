<template>
  <div class="admin">
    <header class="admin-header">
      <div class="header-left">
        <router-link to="/" class="back-link">&larr; 返回看板</router-link>
        <h1>关键项目管理</h1>
      </div>
      <button class="btn-sm-header btn-primary" @click="openAdd">+ 新增关键项目</button>
    </header>

    <table class="goal-table" v-if="list.length > 0">
      <thead>
        <tr>
          <th>项目名称</th>
          <th>负责人</th>
          <th>开始时间</th>
          <th>结束时间</th>
          <th>进度</th>
          <th>得分</th>
          <th>状态</th>
          <th style="width:200px">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in list" :key="item.id">
          <td>{{ item.name }}</td>
          <td class="center">{{ item.owner || '-' }}</td>
          <td class="center">{{ item.start_date || '-' }}</td>
          <td class="center">{{ item.end_date || '-' }}</td>
          <td class="center">{{ item.progress }}</td>
          <td class="center">
            <span v-if="item.score != null" class="score-badge" :class="getScoreClass(item.score)">{{ item.score.toFixed(1) }}</span>
            <span v-else class="text-muted">-</span>
          </td>
          <td class="center">
            <span class="status-badge" :class="item.status">{{ getStatusText(item.status) }}</span>
          </td>
          <td>
            <div class="action-btns">
              <router-link :to="`/key-project/${item.id}`" class="btn-sm btn-view">查看</router-link>
              <button class="btn-sm btn-edit" @click="openEdit(item)">编辑</button>
              <button class="btn-sm btn-danger" @click="handleDelete(item)">删除</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state">暂无关键项目，请点击「新增关键项目」</div>

    <transition name="modal">
      <div v-if="showModal" class="modal-mask" @click.self="showModal = false">
        <div class="modal-box">
          <h3>{{ editingId ? '编辑关键项目' : '新增关键项目' }}</h3>
          <div class="form-group">
            <label>项目名称</label>
            <input v-model="form.name" class="form-input" placeholder="关键项目名称" />
          </div>
          <div class="form-group">
            <label>负责人</label>
            <input v-model="form.owner" class="form-input" placeholder="负责人" />
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>开始时间</label>
              <input v-model="form.start_date" class="form-input" type="date" />
            </div>
            <div class="form-group half">
              <label>结束时间</label>
              <input v-model="form.end_date" class="form-input" type="date" />
            </div>
          </div>
          <div class="form-group">
            <label>进度</label>
            <select v-model="form.progress" class="form-input">
              <option value="在行">在行</option>
              <option value="关闭">关闭</option>
            </select>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showModal = false">取消</button>
            <button class="btn-primary" @click="handleSave">保存</button>
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
import { ref, reactive, onMounted } from 'vue'
import { getKeyProjects, createKeyProject, updateKeyProject, deleteKeyProject } from '@/api'
import type { KeyProject } from '@/api'

const list = ref<KeyProject[]>([])
const showModal = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', owner: '', start_date: '', end_date: '', progress: '在行' })

const toast = ref<{ msg: string; type: string } | null>(null)
const showToast = (msg: string, type = 'success') => {
  toast.value = { msg, type }
  setTimeout(() => { toast.value = null }, 2000)
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { healthy: '健康', warning: '需关注', risk: '高风险' }
  return map[status] || status
}

const getScoreClass = (score: number) => {
  if (score >= 80) return 'green'
  if (score >= 60) return 'orange'
  return 'red'
}

const load = async () => {
  const res = await getKeyProjects()
  list.value = res.data
}

const openAdd = () => {
  editingId.value = null
  form.name = ''
  form.owner = ''
  form.start_date = ''
  form.end_date = ''
  form.progress = '在行'
  showModal.value = true
}

const openEdit = (item: KeyProject) => {
  editingId.value = item.id
  form.name = item.name
  form.owner = item.owner || ''
  form.start_date = item.start_date || ''
  form.end_date = item.end_date || ''
  form.progress = item.progress
  showModal.value = true
}

const handleSave = async () => {
  if (!form.name.trim()) return
  const data: any = { name: form.name.trim(), owner: form.owner.trim() || undefined, progress: form.progress }
  if (form.start_date) data.start_date = form.start_date
  if (form.end_date) data.end_date = form.end_date
  if (editingId.value) {
    await updateKeyProject(editingId.value, data)
    showToast('已更新')
  } else {
    await createKeyProject(data)
    showToast('已创建')
  }
  showModal.value = false
  await load()
}

const handleDelete = async (item: KeyProject) => {
  if (!confirm(`确定删除关键项目「${item.name}」？`)) return
  await deleteKeyProject(item.id)
  showToast('已删除', 'warn')
  await load()
}

onMounted(load)
</script>

<style scoped>
.admin { max-width: 1200px; margin: 0 auto; padding: 20px; min-height: 100vh; }
.admin-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--border-subtle); margin-bottom: 24px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-left h1 { margin: 0; font-size: 18px; font-weight: 700; }
.back-link { color: var(--accent-blue); text-decoration: none; font-size: 13px; }
.btn-sm-header { padding: 6px 14px; border-radius: 6px; border: none; cursor: pointer; font-size: 12px; font-weight: 600; }
.btn-primary { background: var(--accent-blue); color: white; }
.goal-table { width: 100%; border-collapse: collapse; background: var(--bg-card); border-radius: 12px; overflow: hidden; }
.goal-table th, .goal-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-subtle); }
.goal-table th { color: var(--text-muted); font-size: 12px; font-weight: 600; }
.goal-table td { font-size: 13px; }
.goal-table tbody tr:hover { background: rgba(59,130,246,0.05); }
.center { text-align: center; }
.status-badge { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 600; }
.status-badge.healthy { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.status-badge.warning { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.status-badge.risk { background: rgba(239,68,68,0.15); color: var(--accent-red); }
.score-badge { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 700; }
.score-badge.green { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.score-badge.orange { background: rgba(245,158,11,0.15); color: var(--accent-orange); }
.score-badge.red { background: rgba(239,68,68,0.15); color: var(--accent-red); }
.text-muted { color: var(--text-muted); }
.action-btns { display: flex; gap: 6px; }
.btn-sm { padding: 4px 12px; border-radius: 4px; border: none; cursor: pointer; font-size: 12px; font-weight: 500; text-decoration: none; display: inline-block; }
.btn-view { background: var(--accent-purple); color: white; }
.btn-edit { background: var(--accent-blue); color: white; }
.btn-danger { background: transparent; color: var(--accent-red); border: 1px solid var(--accent-red); }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: var(--bg-secondary); border-radius: 12px; padding: 24px; width: 100%; max-width: 480px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.form-input { width: 100%; padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-subtle); background: var(--bg-primary); color: var(--text-primary); font-size: 13px; box-sizing: border-box; }
.form-row { display: flex; gap: 12px; }
.form-group.half { flex: 1; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-secondary { padding: 8px 20px; border-radius: 6px; border: 1px solid var(--border-subtle); background: transparent; color: var(--text-secondary); cursor: pointer; font-size: 13px; }
.toast { position: fixed; top: 20px; right: 20px; padding: 10px 20px; border-radius: 6px; color: white; font-size: 13px; z-index: 2000; }
.toast.success { background: var(--accent-green); }
.toast.warn { background: var(--accent-orange); }
.toast.error { background: var(--accent-red); }
</style>
