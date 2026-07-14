import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Admin from '../views/Admin.vue'
import MemberPerformance from '../views/MemberPerformance.vue'
import GoalManagement from '../views/GoalManagement.vue'
import SpecialAdmin from '../views/SpecialAdmin.vue'
import SpecialProjectDetail from '../views/SpecialProjectDetail.vue'
import SpecialDashboard from '../views/SpecialDashboard.vue'
import KeyProjectAdmin from '../views/KeyProjectAdmin.vue'
import KeyProjectDetail from '../views/KeyProjectDetail.vue'
import MobileDashboard from '../views/mobile/Dashboard.vue'
import MobileProjectDetail from '../views/mobile/ProjectDetail.vue'
import MobileAlerts from '../views/mobile/Alerts.vue'
import MobileAnalysis from '../views/mobile/Analysis.vue'
import MobileMemberPerformance from '../views/mobile/MemberPerformance.vue'
import MobileGoalManagement from '../views/mobile/GoalManagement.vue'
import MobileKeyProjects from '../views/mobile/KeyProjects.vue'
import MobileKeyProjectDetail from '../views/mobile/KeyProjectDetail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/project/:id', name: 'project-detail', component: ProjectDetail },
    { path: '/admin', name: 'admin', component: Admin },
    { path: '/member-performance', name: 'member-performance', component: MemberPerformance },
    { path: '/goal-management', name: 'goal-management', component: GoalManagement },
    { path: '/special-dashboard', name: 'special-dashboard', component: SpecialDashboard },
    { path: '/special-admin', name: 'special-admin', component: SpecialAdmin },
    { path: '/special-project/:id', name: 'special-project-detail', component: SpecialProjectDetail },
    { path: '/key-projects', name: 'key-projects', component: KeyProjectAdmin },
    { path: '/key-project/:id', name: 'key-project-detail', component: KeyProjectDetail },
    { path: '/mobile', name: 'mobile', component: MobileDashboard },
    { path: '/mobile/project/:id', name: 'mobile-project', component: MobileProjectDetail },
    { path: '/mobile/alerts', name: 'mobile-alerts', component: MobileAlerts },
    { path: '/mobile/analysis', name: 'mobile-analysis', component: MobileAnalysis },
    { path: '/mobile/performance', name: 'mobile-performance', component: MobileMemberPerformance },
    { path: '/mobile/goals', name: 'mobile-goals', component: MobileGoalManagement },
    { path: '/mobile/key-projects', name: 'mobile-key-projects', component: MobileKeyProjects },
    { path: '/mobile/key-project/:id', name: 'mobile-key-project-detail', component: MobileKeyProjectDetail },
  ]
})

export default router