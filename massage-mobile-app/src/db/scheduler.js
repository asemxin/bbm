import { getTechnicians, getAppointments } from './index'

// 将"HH:mm"格式的时间转换为当天的分钟数
export function timeToMinutes(timeStr) {
  const [h, m] = timeStr.split(':').map(Number)
  return h * 60 + m
}

export function minutesToTime(mins) {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
}

/**
 * 检查指定技师在特定时段内是否空闲
 */
export async function isSlotFree(techId, dateStr, startMins, endMins) {
  const techs = await getTechnicians(dateStr)
  const tech = techs.find(t => t.tech_id === techId)
  
  if (!tech || !tech.is_available) return false
  
  const techStart = timeToMinutes(tech.start_time)
  const techEnd = timeToMinutes(tech.end_time)
  
  // 检查是否在上班时间范围内
  if (startMins < techStart || endMins > techEnd) return false
  
  const appointments = await getAppointments(dateStr)
  
  // 检查是否与已有预约冲突
  for (const appt of appointments) {
    if (appt.tech_id === techId && appt.status !== '已取消') {
      const apptStart = appt.start_minutes
      const apptEnd = appt.start_minutes + appt.duration
      // 如果重叠则返回 false
      if (startMins < apptEnd && endMins > apptStart) {
        return false
      }
    }
  }
  return true
}

/**
 * 获取某个日期最近一次排班轮到的技师号 (简单轮询)
 * 这里通过获取已有的订单来找人数最少的技师，实现简易负载均衡
 */
async function getNextRobinTech(dateStr, techs) {
  const appointments = await getAppointments(dateStr)
  
  const techWorkloads = techs.map(t => {
    const techAppts = appointments.filter(a => a.tech_id === t.tech_id && a.status !== '已取消')
    return {
      id: t.tech_id,
      count: techAppts.length
    }
  })
  
  // 找订单最少的
  techWorkloads.sort((a, b) => a.count - b.count)
  return techWorkloads.map(t => t.id)
}

/**
 * 智能规划入口：
 * 尝试为客户找满足时段要求的技师。
 * @returns { success: Boolean, data: Object, suggestions: Array }
 */
export async function scheduleAppointment(dateStr, timeStr, duration, preferredTechId = null) {
  const startMins = timeToMinutes(timeStr)
  const endMins = startMins + duration
  
  const techs = await getTechnicians(dateStr)
  const availableTechs = techs.filter(t => t.is_available)
  
  if (availableTechs.length === 0) {
    return { success: false, msg: '当天没有上班技师', suggestions: [] }
  }
  
  let assignedTechId = null
  
  // 1. 如果有点钟，优先看该技师行不行
  if (preferredTechId) {
    const isFree = await isSlotFree(preferredTechId, dateStr, startMins, endMins)
    if (isFree) {
      assignedTechId = preferredTechId
    } else {
      // 被点钟的技师没空，直接找建议时段（不轮询别人）
      const suggestions = await suggestAlternatives(dateStr, duration, preferredTechId, availableTechs)
      return { success: false, msg: `${preferredTechId}号技师在该时段已忙`, suggestions }
    }
  } else {
    // 2. 没点钟，通过负载均衡找一个最闲的技师
    const orderedTechIds = await getNextRobinTech(dateStr, availableTechs)
    
    for (const tid of orderedTechIds) {
      const isFree = await isSlotFree(tid, dateStr, startMins, endMins)
      if (isFree) {
        assignedTechId = tid
        break
      }
    }
  }
  
  // 3. 如果找到了
  if (assignedTechId) {
    return {
      success: true,
      msg: '可以排班',
      data: {
        tech_id: assignedTechId,
        start_minutes: startMins,
        duration: duration
      }
    }
  }
  
  // 4. 全部都忙，出建议时段
  const suggestions = await suggestAlternatives(dateStr, duration, null, availableTechs)
  return { success: false, msg: `所选时段所有技师都已排满`, suggestions }
}

/**
 * 找近期的可用空隙时段
 */
export async function suggestAlternatives(dateStr, duration, preferredTechId, techs) {
  const suggestions = []
  const targetTechs = preferredTechId ? techs.filter(t => t.tech_id === preferredTechId) : techs
  const appointments = await getAppointments(dateStr)
  
  for (const tech of targetTechs) {
    const techStart = timeToMinutes(tech.start_time)
    const techEnd = timeToMinutes(tech.end_time)
    
    // 该技师当天的订单时间块
    const techAppts = appointments
      .filter(a => a.tech_id === tech.tech_id && a.status !== '已取消')
      .map(a => [a.start_minutes, a.start_minutes + a.duration])
      .sort((a, b) => a[0] - b[0])
      
    let current = techStart
    
    for (const [bs, be] of techAppts) {
      // 如果当前时间加上需要的时长，还在别人开始前，说明能塞进
      if (current + duration <= bs) {
        suggestions.push({
          tech_id: tech.tech_id,
          tech_name: tech.name,
          start: minutesToTime(current),
          end: minutesToTime(current + duration)
        })
        if (suggestions.length >= 5) return suggestions
      }
      current = Math.max(current, be)
    }
    
    // 检查下班前还能不能做
    if (current + duration <= techEnd) {
      suggestions.push({
        tech_id: tech.tech_id,
        tech_name: tech.name,
        start: minutesToTime(current),
        end: minutesToTime(current + duration)
      })
      if (suggestions.length >= 5) return suggestions
    }
  }
  
  return suggestions
}
