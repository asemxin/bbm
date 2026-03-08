"""
盲人按摩店排班系统 - 排班算法引擎
"""
from datetime import datetime, date, time, timedelta
from typing import Optional
from models import (
    Technician, Appointment, AppointmentStatus, BookingType,
    TIME_SLOT_MINUTES, DEFAULT_DURATION
)
from database import Database


class ScheduleResult:
    """排班结果"""
    def __init__(self, success: bool, appointment: Optional[Appointment] = None,
                 message: str = "", suggestions: list = None):
        self.success = success
        self.appointment = appointment
        self.message = message
        self.suggestions = suggestions or []


class Scheduler:
    def __init__(self, db: Database):
        self.db = db

    def _time_to_minutes(self, t) -> int:
        """time/datetime 转为当天分钟数"""
        if isinstance(t, datetime):
            return t.hour * 60 + t.minute
        return t.hour * 60 + t.minute

    def _minutes_to_time(self, minutes: int) -> time:
        """分钟数转 time"""
        return time(minutes // 60, minutes % 60)

    def _minutes_to_time_str(self, minutes: int) -> str:
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def is_slot_free(self, tech_id: int, work_date: date,
                     start_minutes: int, end_minutes: int) -> bool:
        """检查技师在指定时段是否空闲"""
        # 先检查技师是否在班
        techs = self.db.get_technicians(work_date)
        tech = None
        for t in techs:
            if t.tech_id == tech_id:
                tech = t
                break
        if tech is None:
            return False

        tech_start = self._time_to_minutes(tech.start_time)
        tech_end = self._time_to_minutes(tech.end_time)

        # 检查是否在技师工作时间范围内
        if start_minutes < tech_start or end_minutes > tech_end:
            return False

        # 检查是否与已有预约冲突
        appointments = self.db.get_appointments_for_tech(tech_id, work_date)
        for appt in appointments:
            if appt.status == AppointmentStatus.CANCELLED:
                continue
            appt_start = self._time_to_minutes(appt.start_time)
            appt_end = self._time_to_minutes(appt.end_time)
            # 检查重叠
            if start_minutes < appt_end and end_minutes > appt_start:
                return False
        return True

    def find_available_technician(self, work_date: date,
                                  start_minutes: int, end_minutes: int,
                                  preferred_tech_id: Optional[int] = None) -> Optional[int]:
        """
        查找空闲技师。
        如果有点钟 (preferred_tech_id)，优先检查该技师。
        否则按轮询顺序查找。
        """
        techs = self.db.get_technicians(work_date)
        if not techs:
            return None

        tech_ids = [t.tech_id for t in techs]

        # 有点钟：优先检查指定技师
        if preferred_tech_id and preferred_tech_id in tech_ids:
            if self.is_slot_free(preferred_tech_id, work_date, start_minutes, end_minutes):
                return preferred_tech_id
            return None  # 点钟技师不空闲，返回None（后续给建议）

        # 无点钟：轮询查找
        rr_index = self.db.get_round_robin_index(work_date)
        n = len(tech_ids)

        for i in range(n):
            idx = (rr_index + i) % n
            tid = tech_ids[idx]
            if self.is_slot_free(tid, work_date, start_minutes, end_minutes):
                # 移动轮询指针到下一个
                self.db.set_round_robin_index(work_date, (idx + 1) % n)
                return tid

        return None

    def schedule_appointment(self, customer_name: str, customer_phone: str,
                             work_date: date, start_time_str: str,
                             duration: int = DEFAULT_DURATION,
                             preferred_tech_id: Optional[int] = None,
                             booking_type: BookingType = BookingType.WALK_IN) -> ScheduleResult:
        """
        排班入口。
        返回 ScheduleResult，包含成功/失败信息和建议。
        """
        # 解析开始时间
        parts = start_time_str.split(":")
        start_minutes = int(parts[0]) * 60 + int(parts[1])
        end_minutes = start_minutes + duration

        is_named = preferred_tech_id is not None

        # 查找可用技师
        assigned_tech = self.find_available_technician(
            work_date, start_minutes, end_minutes, preferred_tech_id
        )

        if assigned_tech is not None:
            # 创建预约
            appt = Appointment(
                customer_name=customer_name,
                customer_phone=customer_phone,
                tech_id=assigned_tech,
                requested_tech_id=preferred_tech_id,
                is_named=is_named,
                booking_type=booking_type,
                start_time=datetime(work_date.year, work_date.month, work_date.day,
                                    start_minutes // 60, start_minutes % 60),
                end_time=datetime(work_date.year, work_date.month, work_date.day,
                                  end_minutes // 60, end_minutes % 60),
                duration=duration,
                status=AppointmentStatus.CONFIRMED,
                work_date=work_date
            )
            appt_id = self.db.add_appointment(appt)
            appt.appointment_id = appt_id

            tech_name = f"{assigned_tech}号技师"
            return ScheduleResult(
                success=True,
                appointment=appt,
                message=f"✅ 排班成功！{tech_name} {start_time_str}-{self._minutes_to_time_str(end_minutes)}"
            )
        else:
            # 无法排班，生成建议
            suggestions = self.suggest_alternatives(work_date, duration, preferred_tech_id)
            if suggestions:
                msg = "❌ 所选时段无法安排。以下是可选时段："
            else:
                msg = "❌ 今天没有可用的时段了。"
            return ScheduleResult(
                success=False,
                message=msg,
                suggestions=suggestions
            )

    def suggest_alternatives(self, work_date: date, duration: int,
                             preferred_tech_id: Optional[int] = None,
                             max_suggestions: int = 6) -> list[dict]:
        """
        生成建议时段。
        返回 [{'tech_id': x, 'tech_name': '...', 'start': '10:00', 'end': '11:00'}, ...]
        """
        techs = self.db.get_technicians(work_date)
        if not techs:
            return []

        suggestions = []

        # 如果有点钟，只在该技师上找空闲段
        if preferred_tech_id:
            target_techs = [t for t in techs if t.tech_id == preferred_tech_id]
        else:
            target_techs = techs

        for tech in target_techs:
            tech_start = self._time_to_minutes(tech.start_time)
            tech_end = self._time_to_minutes(tech.end_time)

            # 获取该技师当天的所有预约，按时间排序
            appointments = self.db.get_appointments_for_tech(tech.tech_id, work_date)
            busy_slots = []
            for appt in appointments:
                if appt.status != AppointmentStatus.CANCELLED:
                    busy_slots.append((
                        self._time_to_minutes(appt.start_time),
                        self._time_to_minutes(appt.end_time)
                    ))
            busy_slots.sort()

            # 找空闲段
            current = tech_start
            for bs, be in busy_slots:
                if current + duration <= bs:
                    # 这个空档够用
                    suggestions.append({
                        'tech_id': tech.tech_id,
                        'tech_name': tech.name,
                        'start': self._minutes_to_time_str(current),
                        'end': self._minutes_to_time_str(current + duration)
                    })
                    if len(suggestions) >= max_suggestions:
                        return suggestions
                current = max(current, be)

            # 最后一段空档
            if current + duration <= tech_end:
                suggestions.append({
                    'tech_id': tech.tech_id,
                    'tech_name': tech.name,
                    'start': self._minutes_to_time_str(current),
                    'end': self._minutes_to_time_str(current + duration)
                })
                if len(suggestions) >= max_suggestions:
                    return suggestions

        return suggestions

    def cancel_appointment(self, appointment_id: int) -> bool:
        """取消预约"""
        self.db.cancel_appointment(appointment_id)
        return True

    def adjust_appointment(self, appointment_id: int,
                           new_start_str: str, new_duration: int,
                           new_tech_id: int, work_date: date) -> ScheduleResult:
        """手动调整排班"""
        parts = new_start_str.split(":")
        start_minutes = int(parts[0]) * 60 + int(parts[1])
        end_minutes = start_minutes + new_duration

        # 临时取消当前预约以避免冲突检查自身
        appointments = self.db.get_appointments(work_date)
        target_appt = None
        for a in appointments:
            if a.appointment_id == appointment_id:
                target_appt = a
                break
        if not target_appt:
            return ScheduleResult(False, message="预约不存在")

        # 先标记取消，检查新时段是否可用
        self.db.cancel_appointment(appointment_id)

        if self.is_slot_free(new_tech_id, work_date, start_minutes, end_minutes):
            # 更新预约
            target_appt.tech_id = new_tech_id
            target_appt.start_time = datetime(work_date.year, work_date.month, work_date.day,
                                               start_minutes // 60, start_minutes % 60)
            target_appt.end_time = datetime(work_date.year, work_date.month, work_date.day,
                                             end_minutes // 60, end_minutes % 60)
            target_appt.duration = new_duration
            target_appt.status = AppointmentStatus.CONFIRMED
            self.db.update_appointment(target_appt)
            return ScheduleResult(True, appointment=target_appt, message="✅ 调整成功")
        else:
            # 恢复原状
            target_appt.status = AppointmentStatus.CONFIRMED
            self.db.update_appointment(target_appt)
            return ScheduleResult(False, message="❌ 新时段已被占用，无法调整")

    def get_technician_stats(self, work_date: date) -> list[dict]:
        """
        获取技师工作统计。
        返回 [{'tech_id', 'name', 'completed_minutes', 'completed_count',
               'scheduled_minutes', 'scheduled_count', 'total_minutes', 'total_count'}, ...]
        """
        techs = self.db.get_technicians(work_date)
        now = datetime.now()
        stats = []

        for tech in techs:
            appointments = self.db.get_appointments_for_tech(tech.tech_id, work_date)
            completed_min = 0
            completed_count = 0
            scheduled_min = 0
            scheduled_count = 0

            for appt in appointments:
                if appt.status == AppointmentStatus.CANCELLED:
                    continue
                appt_end_minutes = self._time_to_minutes(appt.end_time)
                now_minutes = now.hour * 60 + now.minute

                if appt.status == AppointmentStatus.COMPLETED or appt_end_minutes <= now_minutes:
                    completed_min += appt.duration
                    completed_count += 1
                else:
                    scheduled_min += appt.duration
                    scheduled_count += 1

            stats.append({
                'tech_id': tech.tech_id,
                'name': tech.name,
                'start_time': tech.start_time.strftime("%H:%M"),
                'end_time': tech.end_time.strftime("%H:%M"),
                'completed_minutes': completed_min,
                'completed_count': completed_count,
                'scheduled_minutes': scheduled_min,
                'scheduled_count': scheduled_count,
                'total_minutes': completed_min + scheduled_min,
                'total_count': completed_count + scheduled_count
            })

        return stats
