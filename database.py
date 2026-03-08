"""
盲人按摩店排班系统 - 数据库操作
"""
import sqlite3
import os
from datetime import datetime, date, time
from typing import Optional
from models import (
    Technician, Appointment, AppointmentStatus, BookingType,
    DEFAULT_START_TIME, DEFAULT_END_TIME
)


DB_NAME = "massage_scheduler.db"


def get_db_path():
    """获取数据库文件路径（与exe同目录）"""
    if getattr(os.sys, 'frozen', False):
        base = os.path.dirname(os.sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, DB_NAME)


class Database:
    def __init__(self):
        self.db_path = get_db_path()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS technicians (
                tech_id INTEGER NOT NULL,
                work_date TEXT NOT NULL,
                name TEXT DEFAULT '',
                start_time TEXT DEFAULT '10:00',
                end_time TEXT DEFAULT '22:00',
                is_available INTEGER DEFAULT 1,
                PRIMARY KEY (tech_id, work_date)
            );

            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT DEFAULT '',
                customer_phone TEXT DEFAULT '',
                tech_id INTEGER,
                requested_tech_id INTEGER,
                is_named INTEGER DEFAULT 0,
                booking_type TEXT DEFAULT '即时到店',
                start_time TEXT,
                end_time TEXT,
                duration INTEGER DEFAULT 60,
                status TEXT DEFAULT '已确认',
                work_date TEXT NOT NULL,
                created_at TEXT,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS round_robin (
                work_date TEXT PRIMARY KEY,
                next_index INTEGER DEFAULT 0
            );
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ===== 技师操作 =====

    def set_technician(self, tech: Technician):
        """设置/更新技师当日信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO technicians
            (tech_id, work_date, name, start_time, end_time, is_available)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tech.tech_id,
            tech.work_date.isoformat(),
            tech.name,
            tech.start_time.strftime("%H:%M"),
            tech.end_time.strftime("%H:%M"),
            1 if tech.is_available else 0
        ))
        self.conn.commit()

    def get_technicians(self, work_date: date) -> list[Technician]:
        """获取某天所有已设置的技师"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM technicians WHERE work_date = ? AND is_available = 1 ORDER BY tech_id",
            (work_date.isoformat(),)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            t = Technician(
                tech_id=row['tech_id'],
                name=row['name'],
                start_time=datetime.strptime(row['start_time'], "%H:%M").time(),
                end_time=datetime.strptime(row['end_time'], "%H:%M").time(),
                is_available=bool(row['is_available']),
                work_date=date.fromisoformat(row['work_date'])
            )
            result.append(t)
        return result

    def remove_technician(self, tech_id: int, work_date: date):
        """移除某天的技师"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM technicians WHERE tech_id = ? AND work_date = ?",
            (tech_id, work_date.isoformat())
        )
        self.conn.commit()

    # ===== 预约操作 =====

    def add_appointment(self, appt: Appointment) -> int:
        """添加预约，返回ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO appointments
            (customer_name, customer_phone, tech_id, requested_tech_id, is_named,
             booking_type, start_time, end_time, duration, status, work_date, created_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appt.customer_name,
            appt.customer_phone,
            appt.tech_id,
            appt.requested_tech_id,
            1 if appt.is_named else 0,
            appt.booking_type.value,
            appt.start_time.strftime("%H:%M") if appt.start_time else None,
            appt.end_time.strftime("%H:%M") if appt.end_time else None,
            appt.duration,
            appt.status.value,
            appt.work_date.isoformat(),
            appt.created_at.isoformat(),
            appt.notes
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_appointment(self, appt: Appointment):
        """更新预约"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE appointments SET
                customer_name=?, customer_phone=?, tech_id=?, requested_tech_id=?,
                is_named=?, booking_type=?, start_time=?, end_time=?, duration=?,
                status=?, notes=?
            WHERE appointment_id=?
        """, (
            appt.customer_name,
            appt.customer_phone,
            appt.tech_id,
            appt.requested_tech_id,
            1 if appt.is_named else 0,
            appt.booking_type.value,
            appt.start_time.strftime("%H:%M") if appt.start_time else None,
            appt.end_time.strftime("%H:%M") if appt.end_time else None,
            appt.duration,
            appt.status.value,
            appt.notes,
            appt.appointment_id
        ))
        self.conn.commit()

    def cancel_appointment(self, appointment_id: int):
        """取消预约"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE appointments SET status=? WHERE appointment_id=?",
            (AppointmentStatus.CANCELLED.value, appointment_id)
        )
        self.conn.commit()

    def delete_appointment(self, appointment_id: int):
        """删除预约"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE appointment_id=?", (appointment_id,))
        self.conn.commit()

    def get_appointments(self, work_date: date, include_cancelled: bool = False) -> list[Appointment]:
        """获取某天所有预约"""
        cursor = self.conn.cursor()
        if include_cancelled:
            cursor.execute(
                "SELECT * FROM appointments WHERE work_date=? ORDER BY start_time",
                (work_date.isoformat(),)
            )
        else:
            cursor.execute(
                "SELECT * FROM appointments WHERE work_date=? AND status!=? ORDER BY start_time",
                (work_date.isoformat(), AppointmentStatus.CANCELLED.value)
            )
        rows = cursor.fetchall()
        return [self._row_to_appointment(row) for row in rows]

    def get_appointments_for_tech(self, tech_id: int, work_date: date) -> list[Appointment]:
        """获取某天某技师的所有预约"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM appointments WHERE tech_id=? AND work_date=? AND status!=? ORDER BY start_time",
            (tech_id, work_date.isoformat(), AppointmentStatus.CANCELLED.value)
        )
        rows = cursor.fetchall()
        return [self._row_to_appointment(row) for row in rows]

    def _row_to_appointment(self, row) -> Appointment:
        """数据库行转预约对象"""
        booking_type = BookingType.WALK_IN
        for bt in BookingType:
            if bt.value == row['booking_type']:
                booking_type = bt
                break

        status = AppointmentStatus.CONFIRMED
        for s in AppointmentStatus:
            if s.value == row['status']:
                status = s
                break

        return Appointment(
            appointment_id=row['appointment_id'],
            customer_name=row['customer_name'] or '',
            customer_phone=row['customer_phone'] or '',
            tech_id=row['tech_id'],
            requested_tech_id=row['requested_tech_id'],
            is_named=bool(row['is_named']),
            booking_type=booking_type,
            start_time=datetime.strptime(row['start_time'], "%H:%M") if row['start_time'] else None,
            end_time=datetime.strptime(row['end_time'], "%H:%M") if row['end_time'] else None,
            duration=row['duration'],
            status=status,
            work_date=date.fromisoformat(row['work_date']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            notes=row['notes'] or ''
        )

    # ===== 轮询指针 =====

    def get_round_robin_index(self, work_date: date) -> int:
        """获取当天的轮询指针"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT next_index FROM round_robin WHERE work_date=?", (work_date.isoformat(),))
        row = cursor.fetchone()
        return row['next_index'] if row else 0

    def set_round_robin_index(self, work_date: date, index: int):
        """设置当天的轮询指针"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO round_robin (work_date, next_index) VALUES (?, ?)",
            (work_date.isoformat(), index)
        )
        self.conn.commit()
