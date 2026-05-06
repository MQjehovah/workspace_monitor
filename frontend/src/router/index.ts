import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import Admin from '../views/Admin.vue'
import MobileDashboard from '../views/mobile/Dashboard.vue'
import MobileProjectDetail from '../views/mobile/ProjectDetail.vue'
import MobileAlerts from '../views/mobile/Alerts.vue'
import MobileAnalysis from '../views/mobile/Analysis.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/project/:id', name: 'project-detail', component: ProjectDetail },
    { path: '/admin', name: 'admin', component: Admin },
    { path: '/mobile', name: 'mobile', component: MobileDashboard },
    { path: '/mobile/project/:id', name: 'mobile-project', component: MobileProjectDetail },
    { path: '/mobile/alerts', name: 'mobile-alerts', component: MobileAlerts },
    { path: '/mobile/analysis', name: 'mobile-analysis', component: MobileAnalysis },
  ]
})

export default router