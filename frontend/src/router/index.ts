import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Admin from '../views/Admin.vue'
import MemberPerformance from '../views/MemberPerformance.vue'
import GoalManagement from '../views/GoalManagement.vue'
import MobileDashboard from '../views/mobile/Dashboard.vue'
import MobileProjectDetail from '../views/mobile/ProjectDetail.vue'
import MobileAlerts from '../views/mobile/Alerts.vue'
import MobileAnalysis from '../views/mobile/Analysis.vue'
import MobileMemberPerformance from '../views/mobile/MemberPerformance.vue'
import MobileGoalManagement from '../views/mobile/GoalManagement.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/project/:id', name: 'project-detail', component: ProjectDetail },
    { path: '/admin', name: 'admin', component: Admin },
    { path: '/member-performance', name: 'member-performance', component: MemberPerformance },
    { path: '/goal-management', name: 'goal-management', component: GoalManagement },
    { path: '/mobile', name: 'mobile', component: MobileDashboard },
    { path: '/mobile/project/:id', name: 'mobile-project', component: MobileProjectDetail },
    { path: '/mobile/alerts', name: 'mobile-alerts', component: MobileAlerts },
    { path: '/mobile/analysis', name: 'mobile-analysis', component: MobileAnalysis },
    { path: '/mobile/performance', name: 'mobile-performance', component: MobileMemberPerformance },
    { path: '/mobile/goals', name: 'mobile-goals', component: MobileGoalManagement },
  ]
})

export default router