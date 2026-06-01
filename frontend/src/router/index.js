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
      // ---- 项目工作区：进入某个项目后的统一容器 ----
      {
        path: 'projects/:id',
        component: () => import('../layouts/ProjectWorkspace.vue'),
        children: [
          { path: '', redirect: (to) => `/projects/${to.params.id}/overview` },
          {
            path: 'overview',
            name: 'project-overview',
            component: () => import('../views/workspace/ProjectOverview.vue'),
          },
          {
            path: 'suites',
            name: 'project-suites',
            component: () => import('../views/workspace/ProjectSuites.vue'),
          },
          {
            path: 'suites/new',
            name: 'suite-new',
            component: () => import('../views/SuiteEditorView.vue'),
          },
          {
            path: 'suites/:suiteId',
            name: 'suite-edit',
            component: () => import('../views/SuiteEditorView.vue'),
          },
          {
            path: 'runs',
            name: 'project-runs',
            component: () => import('../views/RunsView.vue'),
          },
          {
            path: 'runs/:runId',
            name: 'project-run-detail',
            component: () => import('../views/RunDetailView.vue'),
          },
          {
            path: 'settings',
            name: 'project-settings',
            component: () => import('../views/workspace/ProjectSettings.vue'),
          },
        ],
      },
      // ---- 全局执行记录（跨项目） ----
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
