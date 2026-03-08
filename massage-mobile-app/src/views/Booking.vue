<template>
  <div class="h-full flex flex-col bg-gray-50 relative">
    <div class="flex-1 overflow-y-auto p-4 space-y-4 pb-20 no-scrollbar">
      
      <!-- 录单卡片 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
        <h2 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
          <span>📝</span> 快速录入预约
        </h2>

        <!-- 客户信息 -->
        <div class="space-y-3 mb-6">
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">客户姓名</label>
            <input v-model="form.name" type="text" placeholder="输入称呼 (必填)" class="w-full bg-gray-50 border-transparent focus:border-indigo-500 focus:bg-white focus:ring-0 rounded-xl px-4 py-3 text-sm transition-colors" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">联系电话 (可选)</label>
            <input v-model="form.phone" type="tel" placeholder="输入手机号" class="w-full bg-gray-50 border-transparent focus:border-indigo-500 focus:bg-white focus:ring-0 rounded-xl px-4 py-3 text-sm transition-colors" />
          </div>
        </div>

        <!-- 预约排期 -->
        <div class="space-y-4 mb-6 pt-4 border-t border-gray-50">
          <div class="flex gap-3">
             <div class="flex-1">
               <label class="block text-xs font-medium text-gray-500 mb-1">预约日期</label>
               <input v-model="form.date" type="date" class="w-full bg-gray-50 border-transparent rounded-xl px-3 py-3 text-sm" />
             </div>
             <div class="flex-1">
               <label class="block text-xs font-medium text-gray-500 mb-1">预约时间</label>
               <input v-model="form.time" type="time" step="1800" class="w-full bg-gray-50 border-transparent rounded-xl px-3 py-3 text-sm" />
             </div>
          </div>

          <div>
             <label class="block text-xs font-medium text-gray-500 mb-2">排钟时长</label>
             <div class="flex gap-2">
               <button 
                 v-for="d in [30, 60, 90, 120]" 
                 :key="d"
                 @click="form.duration = d"
                 class="flex-1 py-2 rounded-xl text-sm font-medium transition-colors border"
                 :class="form.duration === d ? 'bg-indigo-50 border-indigo-600 text-indigo-700' : 'bg-white border-gray-200 text-gray-600'"
               >
                 {{ d }}分钟
               </button>
             </div>
          </div>
        </div>

        <!-- 点钟 -->
        <div class="pt-4 border-t border-gray-50">
          <div class="flex items-center justify-between mb-3">
            <div>
              <label class="block text-sm font-medium text-gray-800">客人点钟</label>
              <p class="text-xs text-gray-400 mt-0.5">开启后需指定排钟技师</p>
            </div>
            <!-- Switch -->
            <button 
              @click="toggleNamed"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="form.isNamed ? 'bg-indigo-600' : 'bg-gray-200'"
            >
              <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" :class="form.isNamed ? 'translate-x-6' : 'translate-x-1'"></span>
            </button>
          </div>

          <!-- 横向滑动技师列表 -->
          <div v-show="form.isNamed" class="flex gap-3 overflow-x-auto no-scrollbar py-2">
             <div 
               v-for="tech in technicians" 
               :key="tech.tech_id"
               @click="form.techId = tech.tech_id"
               class="shrink-0 w-16 h-16 rounded-2xl flex flex-col items-center justify-center border transition-all"
               :class="form.techId === tech.tech_id ? 'bg-indigo-50 border-indigo-600 shadow-sm' : 'bg-white border-gray-100'"
             >
               <span class="text-lg font-bold" :class="form.techId === tech.tech_id ? 'text-indigo-600' : 'text-gray-600'">{{ tech.tech_id }}</span>
               <span class="text-[10px] tracking-tighter" :class="form.techId === tech.tech_id ? 'text-indigo-500' : 'text-gray-400'">号技师</span>
             </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部悬浮按钮 -->
    <div class="px-4 py-3 bg-white border-t border-gray-100 flex-none sticky bottom-0 z-20">
      <button 
        @click="submitBooking"
        :disabled="isSubmitting"
        class="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white rounded-xl font-bold text-base shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
      >
        {{ isSubmitting ? '正在安排...' : '🚀 立即排班' }}
      </button>
    </div>

    <!-- 冲突建议大弹窗 (Bottom Sheet 样式) -->
    <div v-if="showSuggestions" class="fixed inset-0 z-50 flex flex-col justify-end">
       <div class="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" @click="showSuggestions = false"></div>
       <div class="bg-white rounded-t-3xl w-full max-h-[80vh] flex flex-col relative z-10 animate-slide-up">
         <div class="w-12 h-1.5 bg-gray-300 rounded-full mx-auto mt-3 mb-1"></div>
         <div class="px-5 py-4 border-b border-gray-100">
           <h3 class="font-bold text-lg text-red-600">❌ 时段已被占用</h3>
           <p class="text-xs text-gray-500 mt-1">{{ suggestionMsg }}</p>
         </div>
         <div class="overflow-y-auto p-5 space-y-3">
            <h4 class="text-sm font-bold text-gray-800">建议选择以下空余时段：</h4>
            <div 
              v-for="(sug, idx) in suggestions" 
              :key="idx"
              @click="acceptSuggestion(sug)"
              class="flex items-center justify-between p-4 rounded-2xl bg-gray-50 border border-gray-100 active:bg-indigo-50 transition-colors"
            >
               <div class="flex items-center gap-3">
                 <div class="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center">{{ sug.tech_id }}号</div>
                 <div>
                   <div class="font-medium text-gray-800">{{ sug.start }} - {{ sug.end }}</div>
                   <div class="text-xs text-gray-500">点此直接排该技师</div>
                 </div>
               </div>
               <span class="text-indigo-600 text-xl font-bold">→</span>
            </div>
            <div v-if="suggestions.length === 0" class="text-center py-6 text-gray-400">
              抱歉，今天已经没有能够满足此时长的空档了。
            </div>
         </div>
         <div class="p-4 bg-white border-t border-gray-100 pb-safe">
           <button @click="showSuggestions = false" class="w-full py-3.5 bg-gray-100 text-gray-600 rounded-xl font-bold">暂不预约</button>
         </div>
       </div>
    </div>

    <!-- 成功提示 Toast -->
    <div v-if="successMsg" class="fixed top-20 left-1/2 -translate-x-1/2 bg-gray-800/90 text-white px-6 py-3 rounded-full shadow-xl flex items-center gap-2 z-50 animate-fade-in text-sm font-medium">
      <span>✅</span> {{ successMsg }}
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTechnicians, addAppointment } from '@/db'
import { scheduleAppointment, timeToMinutes } from '@/db/scheduler'
import { format } from 'date-fns'

const router = useRouter()
const technicians = ref([])

const form = reactive({
  name: '',
  phone: '',
  date: format(new Date(), 'yyyy-MM-dd'),
  time: format(new Date(), 'HH:mm'),
  duration: 60,
  isNamed: false,
  techId: 1
})

const isSubmitting = ref(false)
const successMsg = ref('')

const showSuggestions = ref(false)
const suggestionMsg = ref('')
const suggestions = ref([])

onMounted(async () => {
  technicians.value = await getTechnicians(form.date)
  
  // 约到半点或整点
  const now = new Date()
  let m = now.getMinutes()
  m = m < 30 ? 30 : 0
  if (m === 0) now.setHours(now.getHours() + 1)
  now.setMinutes(m)
  form.time = format(now, 'HH:mm')
})

const toggleNamed = () => {
  form.isNamed = !form.isNamed
  if (form.isNamed && technicians.value.length > 0) {
    if (!form.techId) form.techId = technicians.value[0].tech_id
  }
}

const showToast = (msg) => {
  successMsg.value = msg
  setTimeout(() => { successMsg.value = '' }, 2500)
}

const submitBooking = async () => {
  if (!form.name.trim()) {
    alert("请输入客户姓名")
    return
  }

  isSubmitting.value = true
  
  const prefTechId = form.isNamed ? form.techId : null
  
  try {
    const res = await scheduleAppointment(form.date, form.time, form.duration, prefTechId)
    
    if (res.success) {
      // 创建预约单进数据库
      await addAppointment({
        customer_name: form.name.trim(),
        customer_phone: form.phone.trim(),
        work_date: form.date,
        is_named: form.isNamed,
        start_minutes: res.data.start_minutes,
        duration: res.data.duration,
        tech_id: res.data.tech_id,
        booking_type: '预约'
      })
      
      showToast(`排班成功！分配至 ${res.data.tech_id}号技师`)
      // 重置表单
      form.name = ''
      form.phone = ''
      form.isNamed = false
      // 跳转回首页看板
      setTimeout(() => { router.push('/') }, 1000)
    } else {
      // 弹出冲突建议
      suggestionMsg.value = res.msg
      suggestions.value = res.suggestions
      showSuggestions.value = true
    }
  } catch (err) {
    console.error(err)
    alert("排班发生错误")
  } finally {
    isSubmitting.value = false
  }
}

const acceptSuggestion = async (sug) => {
  await addAppointment({
    customer_name: form.name.trim(),
    customer_phone: form.phone.trim(),
    work_date: form.date,
    is_named: true, // 接受了技师建议即相当于点钟
    start_minutes: timeToMinutes(sug.start),
    duration: form.duration,
    tech_id: sug.tech_id,
    booking_type: '预约'
  })
  
  showSuggestions.value = false
  showToast(`排班成功！分配至 ${sug.tech_id}号技师`)
  form.name = ''
  setTimeout(() => { router.push('/') }, 1000)
}
</script>

<style scoped>
.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translate(-50%, -10px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
</style>
