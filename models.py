"""
盲人按摩店排班系统 - 数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime, date, time
from enum import Enum
from typing import Optional


class AppointmentStatus(Enum):
    """预约状态"""
    PENDING = "待确认"
    CONFIRMED = "已确认"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


class BookingType(Enum):
    """预约类型"""
    APPOINTMENT = "预约"
    WALK_IN = "即时到店"


# 默认常量
DEFAULT_START_TIME = time(10, 0)  # 10:00 AM
DEFAULT_END_TIME = time(22, 0)    # 10:00 PM
TIME_SLOT_MINUTES = 30            # 时间粒度30分钟
DEFAULT_DURATION = 60             # 默认按摩时长60分钟
MAX_TECHNICIANS = 10              # 最大技师数


# 可选时长列表（分钟）
DURATION_OPTIONS = [30, 60, 90, 120]

# 生成时间段列表（供下拉框使用）
def generate_time_slots(start: time = DEFAULT_START_TIME, end: time = DEFAULT_END_TIME) -> list[str]:
    """生成从 start 到 end 的时间段列表，间隔 TIME_SLOT_MINUTES 分钟"""
    slots = []
    current_hour = start.hour
    current_minute = start.minute
    end_minutes = end.hour * 60 + end.minute

    while current_hour * 60 + current_minute <= end_minutes:
        slots.append(f"{current_hour:02d}:{current_minute:02d}")
        current_minute += TIME_SLOT_MINUTES
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute = current_minute % 60

    return slots


@dataclass
class Technician:
    """技师"""
    tech_id: int                          # 编号 1-10
    name: str = ""                        # 名称（可选）
    start_time: time = DEFAULT_START_TIME # 上班时间
    end_time: time = DEFAULT_END_TIME     # 下班时间
    is_available: bool = True             # 当天是否可用
    work_date: date = field(default_factory=date.today)

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.tech_id}号技师"


@dataclass
class Appointment:
    """预约记录"""
    appointment_id: int = 0               # 数据库自增ID
    customer_name: str = ""               # 客户姓名
    customer_phone: str = ""              # 联系方式
    tech_id: Optional[int] = None         # 分配的技师编号
    requested_tech_id: Optional[int] = None  # 点钟的技师编号
    is_named: bool = False                # 是否点钟
    booking_type: BookingType = BookingType.WALK_IN
    start_time: Optional[datetime] = None # 开始时间
    end_time: Optional[datetime] = None   # 结束时间
    duration: int = DEFAULT_DURATION      # 时长（分钟）
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    work_date: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
