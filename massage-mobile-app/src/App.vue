<template>
  <!-- 移动端安全区域适配外壳 -->
  <div class="h-screen w-full flex flex-col bg-gray-50 overflow-hidden text-gray-800">
    
    <!-- 顶部状态栏（针对PWA和Capacitor适配刘海屏） -->
    <div class="pt-safe bg-white shadow-sm z-50">
      <header class="h-12 flex items-center justify-center relative">
        <h1 class="text-base font-semibold tracking-wide">
          {{ currentRouteTitle }}
        </h1>
      </header>
    </div>

    <!-- 滚动的主内容区 -->
    <main class="flex-1 overflow-y-auto no-scrollbar pb-safe relative">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部 Tab 导航栏 -->
    <nav class="h-14 bg-white border-t border-gray-100 flex justify-around items-center pb-safe-bottom shadow-[0_-2px_10px_rgba(0,0,0,0.02)] z-50">
      <router-link 
        v-for="item in tabs" 
        :key="item.path" 
        :to="item.path"
        class="flex flex-col items-center justify-center w-full h-full text-xs transition-colors duration-200"
        :class="$route.path === item.path ? 'text-indigo-600 font-medium' : 'text-gray-400'"
      >
        <span class="text-xl mb-0.5">{{ item.icon }}</span>
        <span>{{ item.title }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentRouteTitle = computed(() => route.meta.title || '盲人按摩系统')

const tabs = [
  { path: '/', title: '排班看板', icon: '📅' },
  { path: '/booking', title: '新增预约', icon: '📝' },
  { path: '/settings', title: '技师设置', icon: '⚙️' }
]
</script>

<style>
/* CSS Env variables for safe area (iPhone Notch) */
.pt-safe { padding-top: env(safe-area-inset-top, 0px); }
.pb-safe { padding-bottom: env(safe-area-inset-bottom, 0px); }
.pb-safe-bottom { padding-bottom: calc(env(safe-area-inset-bottom, 0px)); }

/* 路由切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(5px);
}
</style>
