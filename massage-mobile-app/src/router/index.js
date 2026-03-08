import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '排班看板', icon: '📅' }
  },
  {
    path: '/booking',
    name: 'Booking',
    component: () => import('@/views/Booking.vue'),
    meta: { title: '新增预约', icon: '📝' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '技师设置', icon: '⚙️' }
  }
]

const router = createRouter({
  // 对于手机 App/PWA, Hash 路由兼容性更好，不需要后台配置 Nginx
  history: createWebHashHistory(),
  routes
})

export default router
