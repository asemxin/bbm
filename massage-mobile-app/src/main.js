import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { initDB } from './db'

// 启动前初始化数据库
initDB().then(() => {
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
}).catch(err => {
  console.error("数据库初始化失败", err)
  // 即使失败也尝试启动，以防浏览器不支持
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
})
