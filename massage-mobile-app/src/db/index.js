import { openDB } from 'idb'
import { format } from 'date-fns'

const DB_NAME = 'massage_scheduler_db'
const DB_VERSION = 1

// 初始化数据库
export async function initDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('technicians')) {
        const store = db.createObjectStore('technicians', { keyPath: ['work_date', 'tech_id'] })
        // 索引方便按日期查找
        store.createIndex('work_date', 'work_date')
      }
      if (!db.objectStoreNames.contains('appointments')) {
        const store = db.createObjectStore('appointments', { keyPath: 'id', autoIncrement: true })
        store.createIndex('work_date', 'work_date')
        store.createIndex('tech_id', 'tech_id')
      }
    }
  })
}

// === 技师服务 ===

export async function getTechnicians(dateStr) {
  const db = await initDB()
  const tx = db.transaction('technicians', 'readonly')
  const index = tx.store.index('work_date')
  const techs = await index.getAll(dateStr)
  
  // 返回排序好的技师列表
  if (techs.length > 0) {
    return techs.sort((a, b) => a.tech_id - b.tech_id)
  }

  // 默认初始化当天1-10号
  const defaultTechs = Array.from({ length: 10 }, (_, i) => ({
    work_date: dateStr,
    tech_id: i + 1,
    name: `${i + 1}号`,
    start_time: '10:00',
    end_time: '22:00',
    is_available: true
  }))
  return defaultTechs
}

export async function saveTechnician(tech) {
  const db = await initDB()
  await db.put('technicians', tech)
}

// === 预约服务 ===

export async function addAppointment(appt) {
  const db = await initDB()
  const id = await db.add('appointments', {
    ...appt,
    status: '已确认',
    created_at: new Date().toISOString()
  })
  return id
}

export async function getAppointments(dateStr) {
  const db = await initDB()
  const tx = db.transaction('appointments', 'readonly')
  const index = tx.store.index('work_date')
  const appts = await index.getAll(dateStr)
  // 过滤已取消的并按时间排
  return appts.filter(a => a.status !== '已取消').sort((a, b) => a.start_minutes - b.start_minutes)
}

export async function cancelAppointment(id) {
  const db = await initDB()
  const appt = await db.get('appointments', id)
  if (appt) {
    appt.status = '已取消'
    await db.put('appointments', appt)
  }
}
