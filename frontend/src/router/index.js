import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/DashboardView.vue'),
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('../views/ProjectsView.vue'),
      },
      {
        path: 'projects/:id',
        name: 'project-detail',
        component: () => import('../views/ProjectDetailView.vue'),
      },
      {
        path: 'projects/:id/suites/new',
        name: 'suite-new',
        component: () => import('../views/SuiteEditorView.vue'),
      },
      {
        path: 'projects/:id/suites/:suiteId',
        name: 'suite-edit',
        component: () => import('../views/SuiteEditorView.vue'),
      },
      {
        path: 'runs',
        name: 'runs',
        component: () => import('../views/RunsView.vue'),
      },
      {
        path: 'runs/:runId',
        name: 'run-detail',
        component: () => import('../views/RunDetailView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
