<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- 顶部日期选择器 -->
    <div class="bg-white shadow-xs px-4 py-3 sticky top-0 z-10 flex border-b border-gray-100 flex-none gap-2 overflow-x-auto no-scrollbar">
      <div 
        v-for="date in weekDates" 
        :key="date.full"
        @click="selectDate(date.full)"
        class="flex flex-col items-center justify-center min-w-[60px] h-[64px] rounded-2xl transition-all cursor-pointer border"
        :class="selectedDate === date.full ? 'bg-indigo-600 text-white border-indigo-600 shadow-md transform scale-105' : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'"
      >
        <span class="text-xs mb-1 opacity-90">{{ date.dayName }}</span>
        <span class="text-lg font-bold">{{ date.dayNum }}</span>
      </div>
    </div>

    <!-- 统计摘要 -->
    <div class="px-4 py-4 flex justify-between items-center flex-none">
      <h2 class="text-lg font-bold text-gray-800">今日排班概况</h2>
      <div class="flex gap-2 text-xs">
         <span class="px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">空闲: {{ freeCount }}</span>
         <span class="px-2 py-1 bg-red-100 text-red-700 rounded-full font-medium">忙碌: {{ busyCount }}</span>
      </div>
    </div>

    <!-- 技师列表 -->
    <div class="flex-1 overflow-y-auto px-4 pb-6 space-y-4">
      <div v-if="technicians.length === 0" class="text-center py-10 text-gray-400">
        <p>今日暂无上班技师，请前往"设置"调整</p>
      </div>

      <div 
        v-for="tech in technicians" 
        :key="tech.tech_id"
        class="bg-white rounded-2xl p-4 shadow-[0_2px_12px_rgba(0,0,0,0.04)] border border-gray-50 relative overflow-hidden"
      >
        <!-- 侧边颜色条 -->
        <div class="absolute left-0 top-0 bottom-0 w-1.5" :style="{ backgroundColor: getTechColor(tech.tech_id) }"></div>
        
        <div class="flex justify-between items-start mb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-inner" :style="{ backgroundColor: getTechColor(tech.tech_id) }">
              {{ tech.tech_id }}
            </div>
            <div>
              <h3 class="font-bold text-gray-800 text-base">{{ tech.name }}</h3>
              <p class="text-xs text-gray-400 mt-0.5">{{ tech.start_time }} - {{ tech.end_time }}</p>
            </div>
          </div>
          <!-- 当前状态标签 -->
          <span 
            class="px-2.5 py-1 text-xs rounded-full font-medium"
            :class="isTechBusyNow(tech) ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'"
          >
            {{ isTechBusyNow(tech) ? '上钟中' : '空闲' }}
          </span>
        </div>

        <!-- 订单时间轴精简版 -->
        <div class="mt-4 pt-4 border-t border-gray-100">
          <div v-if="getTechAppointments(tech.tech_id).length === 0" class="text-xs text-gray-400 text-center py-2 bg-gray-50 rounded-lg">
            全天暂无预约
          </div>
          <div v-else class="space-y-2">
            <div 
              v-for="appt in getTechAppointments(tech.tech_id)" 
              :key="appt.id"
              class="flex items-center gap-3 text-sm p-2 rounded-lg"
              :class="isApptDone(appt) ? 'bg-gray-50 text-gray-500' : 'bg-blue-50/50 text-gray-800'"
              @click="confirmCancel(appt)"
            >
              <div class="font-mono text-xs w-24 shrink-0 font-medium" :class="isApptDone(appt) ? 'text-gray-400' : 'text-indigo-600'">
                {{ formatTime(appt.start_minutes) }} - {{ formatTime(appt.start_minutes + appt.duration) }}
              </div>
              <div class="flex-1 truncate flex items-center gap-1">
                <span v-if="appt.is_named" class="text-yellow-500 text-xs">⭐</span>
                {{ appt.customer_name }}
              </div>
              <div class="text-xs shrink-0" :class="isApptDone(appt) ? 'text-gray-400' : 'text-blue-500 font-medium'">
            </div>
          </div>
        </div>

        <!-- 技师工作统计 -->
        <div class="mt-4 pt-3 border-t border-gray-50 flex justify-between text-xs text-gray-500 bg-gray-50/50 -mx-4 -mb-4 px-4 py-3 rounded-b-2xl">
          <div class="flex flex-col items-center">
            <span class="text-gray-400 mb-1 scale-90">已完成</span>
            <span class="font-bold text-gray-700">{{ getStats(tech.tech_id).doneCount }}单/{{ getStats(tech.tech_id).doneMins }}分</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-gray-400 mb-1 scale-90">待完成</span>
            <span class="font-bold text-gray-700">{{ getStats(tech.tech_id).pendingCount }}单/{{ getStats(tech.tech_id).pendingMins }}分</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-gray-400 mb-1 scale-90">总计</span>
            <span class="font-bold text-indigo-600">{{ getStats(tech.tech_id).totalCount }}单/{{ getStats(tech.tech_id).totalMins }}分</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { getTechnicians, getAppointments, cancelAppointment } from '@/db'
import { format, addDays, startOfToday } from 'date-fns'

const TECH_COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#eab308', '#84cc16', '#64748b', '#ec4899']

const selectedDate = ref(format(new Date(), 'yyyy-MM-dd'))
const weekDates = ref([])
const technicians = ref([])
const appointments = ref([])

const generateWeekDates = () => {
  const today = startOfToday()
  const dates = []
  const days = ['日', '一', '二', '三', '四', '五', '六']
  for (let i = 0; i < 7; i++) {
    const d = addDays(today, i)
    dates.push({
      full: format(d, 'yyyy-MM-dd'),
      dayName: i === 0 ? '今天' : `周${days[d.getDay()]}`,
      dayNum: format(d, 'dd')
    })
  }
  weekDates.value = dates
}

const loadData = async () => {
  const allTechs = await getTechnicians(selectedDate.value)
  technicians.value = allTechs.filter(t => t.is_available)
  appointments.value = await getAppointments(selectedDate.value)
}

const selectDate = (dateStr) => {
  selectedDate.value = dateStr
}

watch(selectedDate, loadData)

onMounted(() => {
  generateWeekDates()
  loadData()
  
  // 每分钟刷新一次状态
  setInterval(() => {
    technicians.value = [...technicians.value]
  }, 60000)
})

const getTechColor = (id) => TECH_COLORS[(id - 1) % 10]

const getTechAppointments = (tech_id) => {
  return appointments.value.filter(a => a.tech_id === tech_id)
}

const formatTime = (mins) => {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
}

const isApptDone = (appt) => {
  if (selectedDate.value < format(new Date(), 'yyyy-MM-dd')) return true
  if (selectedDate.value > format(new Date(), 'yyyy-MM-dd')) return false
  
  const now = new Date()
  const nowMins = now.getHours() * 60 + now.getMinutes()
  return (appt.start_minutes + appt.duration) <= nowMins
}

const isTechBusyNow = (tech) => {
  if (selectedDate.value !== format(new Date(), 'yyyy-MM-dd')) return false
  const now = new Date()
  const nowMins = now.getHours() * 60 + now.getMinutes()
  
  return appointments.value.some(a => 
    a.tech_id === tech.tech_id && 
    a.start_minutes <= nowMins && 
    (a.start_minutes + a.duration) > nowMins
  )
}

const freeCount = computed(() => technicians.value.filter(t => !isTechBusyNow(t)).length)
const busyCount = computed(() => technicians.value.length - freeCount.value)

const getStats = (tech_id) => {
  const appts = getTechAppointments(tech_id)
  let doneCount = 0, doneMins = 0
  let pendingCount = 0, pendingMins = 0
  
  appts.forEach(a => {
    if (isApptDone(a)) {
      doneCount++
      doneMins += Number(a.duration)
    } else {
      pendingCount++
      pendingMins += Number(a.duration)
    }
  })
  
  return {
    doneCount, doneMins,
    pendingCount, pendingMins,
    totalCount: appts.length,
    totalMins: doneMins + pendingMins
  }
}

const confirmCancel = async (appt) => {
  if (isApptDone(appt)) return
  if (confirm(`确定要取消客户 ${appt.customer_name} 的预约吗？`)) {
    await cancelAppointment(appt.id)
    await loadData()
  }
}
</script>
