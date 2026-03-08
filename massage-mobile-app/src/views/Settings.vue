<template>
  <div class="h-full flex flex-col bg-gray-50 relative">
    <!-- 日期固定顶栏 -->
    <div class="bg-white px-5 py-4 shadow-sm border-b border-gray-100 flex-none sticky top-0 z-10 flex items-center justify-between">
      <div>
        <h2 class="font-bold text-gray-800 text-lg">营业与技师设置</h2>
        <p class="text-xs text-gray-500 mt-0.5">选择排班日期进行人员配置</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="showHelp = true" class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors">
          ❓
        </button>
        <input 
          v-model="workDate" 
          type="date" 
          @change="loadTechnicians"
          class="bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg focus:ring-indigo-500 focus:border-indigo-500 block px-3 py-2 w-32" 
        />
      </div>
    </div>

    <!-- 列表 -->
    <div class="flex-1 overflow-y-auto p-4 pb-20 space-y-3 no-scrollbar">
      <div 
        v-for="tech in technicians" 
        :key="tech.tech_id"
        class="bg-white rounded-2xl p-4 shadow-sm border border-gray-50 transition-all duration-300 transform"
        :class="tech.is_available ? 'opacity-100' : 'opacity-60 grayscale-[30%]'"
      >
        <div class="flex items-center justify-between mb-3 border-b border-gray-50 pb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold" :class="tech.is_available ? 'bg-indigo-500' : 'bg-gray-300'">
              {{ tech.tech_id }}
            </div>
            <div>
              <div class="font-bold text-gray-800">{{ tech.name }}</div>
              <div class="text-[10px] text-gray-400 mt-0.5">{{ tech.is_available ? '排班中' : '休息/请假' }}</div>
            </div>
          </div>
          
          <!-- 开关 -->
          <button 
            @click="toggleStatus(tech)"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
            :class="tech.is_available ? 'bg-indigo-600' : 'bg-gray-200'"
          >
            <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="tech.is_available ? 'translate-x-6' : 'translate-x-1'"></span>
          </button>
        </div>

        <!-- 时间设置区 -->
        <div class="flex items-center gap-3" :class="{ 'opacity-50 pointer-events-none': !tech.is_available }">
          <div class="flex-1">
            <span class="block text-[10px] text-gray-500 mb-1 ml-1">上班</span>
            <input v-model="tech.start_time" type="time" class="w-full bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-700 font-medium" />
          </div>
          <span class="text-gray-300 mt-4">-</span>
          <div class="flex-1">
            <span class="block text-[10px] text-gray-500 mb-1 ml-1">下班</span>
            <input v-model="tech.end_time" type="time" class="w-full bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 text-sm text-gray-700 font-medium" />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部保存按钮 -->
    <div class="px-4 py-3 bg-white border-t border-gray-100 flex-none sticky bottom-0 z-20">
      <button 
        @click="saveSettings"
        class="w-full py-3.5 bg-gray-900 hover:bg-black active:scale-[0.98] text-white rounded-xl font-bold text-base shadow-lg shadow-gray-900/20 transition-all flex justify-center items-center gap-2"
      >
        <span>💾</span> 保存配置
      </button>
    </div>

    <!-- 提示框 -->
    <div v-if="toastMsg" class="fixed top-20 left-1/2 -translate-x-1/2 bg-gray-800 text-white px-5 py-2.5 rounded-full shadow-lg z-50 animate-fade-in text-sm font-medium">
      {{ toastMsg }}
    </div>

    <!-- 帮助与系统说明窗口 -->
    <div v-if="showHelp" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" @click="showHelp = false"></div>
      <div class="bg-white rounded-3xl w-full max-w-sm relative z-10 overflow-hidden animate-fade-in flex flex-col max-h-[85vh] shadow-2xl">
        <div class="bg-indigo-600 px-5 py-4 flex justify-between items-center text-white">
          <h3 class="font-bold text-lg">ℹ️ 软件说明与帮助</h3>
          <button @click="showHelp = false" class="text-white opacity-80 hover:opacity-100 text-2xl font-bold leading-none">&times;</button>
        </div>
        <div class="p-5 overflow-y-auto text-sm text-gray-700 space-y-4">
          <p><strong>👨‍💻 开发者：</strong>本系统由 ma 店长的老公倾情开发！跨平台架构，完美兼容苹果手机与安卓设备。</p>
          <div>
            <h4 class="font-bold text-gray-900 mb-2">【快速上手指南】</h4>
            <ol class="list-decimal pl-4 space-y-2 text-gray-600 text-xs">
              <li><strong>员工配置：</strong>在此页面调整当值排班，休息的技师可被关掉开关。</li>
              <li><strong>自动派单：</strong>在“录单”页面输入客户预约。如果不进行点钟，大数据天平系统自动挑选最空闲的技师承接；如果有专属技师，则排期验证冲突问题。</li>
              <li><strong>一键候补：</strong>点钟如有冲突，将自动计算最近的 5 个有效空档推荐，店长点击一步即可强插时段成功。</li>
              <li><strong>全局监控：</strong>在“看板”中，一目了然全体状态，红色代表当前正在服务，可随时查单。</li>
            </ol>
          </div>
          <div class="bg-indigo-50 border border-indigo-100 p-3 rounded-xl text-xs text-indigo-800">
            <strong>🔐【数据安全与离线模式】</strong><br/>
            本套 WebApp 与电脑版拥有同级数据自治性。系统采用了 IndexedDB 技术将排班数据物理加密封存在手机自带硬盘，彻底无网络时仍可使用（前提：首次打开后不能清空浏览器缓存）。
          </div>
        </div>
        <div class="p-4 bg-gray-50 border-t border-gray-100">
          <button @click="showHelp = false" class="w-full py-3.5 bg-indigo-600 text-white rounded-xl font-bold active:scale-[0.98] transition-all shadow-md">我知道了</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTechnicians, saveTechnician } from '@/db'
import { format } from 'date-fns'

const workDate = ref(format(new Date(), 'yyyy-MM-dd'))
const technicians = ref([])
const toastMsg = ref('')
const showHelp = ref(false)

const loadTechnicians = async () => {
  technicians.value = await getTechnicians(workDate.value)
}

onMounted(() => {
  loadTechnicians()
})

const toggleStatus = (tech) => {
  tech.is_available = !tech.is_available
}

const showToast = (msg) => {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 2000)
}

const saveSettings = async () => {
  for (const tech of technicians.value) {
    // 强制同步日期并去 Proxy 化
    const rawTech = JSON.parse(JSON.stringify(tech))
    rawTech.work_date = workDate.value
    await saveTechnician(rawTech)
  }
  showToast('✅ 技师排班配置已保存')
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translate(-50%, -10px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
</style>
