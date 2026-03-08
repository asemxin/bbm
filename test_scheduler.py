"""
排班逻辑功能测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, time, datetime
from models import Technician, BookingType, DEFAULT_DURATION
from database import Database
from scheduler import Scheduler

# 使用测试数据库
TEST_DB = "test_scheduler.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# Monkey patch
import database as db_module
db_module.DB_NAME = TEST_DB

db = Database()
scheduler = Scheduler(db)
today = date.today()

print("=" * 50)
print("排班系统功能测试")
print("=" * 50)

# 测试1: 设置技师
print("\n--- 测试1: 设置技师 ---")
for i in range(1, 6):
    tech = Technician(tech_id=i, start_time=time(10, 0), end_time=time(22, 0), work_date=today)
    db.set_technician(tech)
techs = db.get_technicians(today)
assert len(techs) == 5, f"应有5个技师，实际{len(techs)}"
print(f"✅ 成功设置 {len(techs)} 个技师")

# 测试2: 无点钟排班 - 轮询
print("\n--- 测试2: 无点钟轮询排班 ---")
for i in range(5):
    result = scheduler.schedule_appointment(
        customer_name=f"客户{i+1}",
        customer_phone=f"1380000000{i}",
        work_date=today,
        start_time_str="10:00",
        duration=60
    )
    assert result.success, f"客户{i+1}排班应成功"
    print(f"  客户{i+1} → {result.appointment.tech_id}号技师 ({result.message})")

# 验证轮询：5个客户应分别分到1-5号技师
appts = db.get_appointments(today)
assigned = sorted([a.tech_id for a in appts])
assert assigned == [1, 2, 3, 4, 5], f"应轮流分配1-5号，实际{assigned}"
print("✅ 轮询分配正确: 1,2,3,4,5号各一个")

# 测试3: 点钟排班
print("\n--- 测试3: 点钟排班 ---")
result = scheduler.schedule_appointment(
    customer_name="VIP客户",
    customer_phone="13900000001",
    work_date=today,
    start_time_str="11:00",
    duration=60,
    preferred_tech_id=3
)
assert result.success, "点钟3号应成功（11:00没有冲突）"
assert result.appointment.tech_id == 3
print(f"✅ VIP客户 → 3号技师 {result.message}")

# 测试4: 时段冲突 + 建议
print("\n--- 测试4: 时段冲突 + 建议时段 ---")
result = scheduler.schedule_appointment(
    customer_name="冲突客户",
    customer_phone="13900000002",
    work_date=today,
    start_time_str="10:00",
    duration=60,
    preferred_tech_id=1  # 1号10:00已满
)
assert not result.success, "1号10:00已满，应失败"
assert len(result.suggestions) > 0, "应有建议时段"
print(f"✅ 冲突检测成功，建议时段数: {len(result.suggestions)}")
for s in result.suggestions[:3]:
    print(f"  建议: {s['tech_name']} {s['start']}-{s['end']}")

# 测试5: 取消预约
print("\n--- 测试5: 取消预约 ---")
appts_before = db.get_appointments(today)
cancel_id = appts_before[0].appointment_id
scheduler.cancel_appointment(cancel_id)
appts_after = db.get_appointments(today)
assert len(appts_after) == len(appts_before) - 1
print(f"✅ 取消预约 #{cancel_id} 成功")

# 测试6: 统计
print("\n--- 测试6: 技师统计 ---")
stats = scheduler.get_technician_stats(today)
for s in stats:
    print(f"  {s['name']}: 总{s['total_count']}单/{s['total_minutes']}分钟")
print("✅ 统计数据正确")

# 测试7: 调整排班
print("\n--- 测试7: 调整排班 ---")
appts = db.get_appointments(today)
adjust_id = appts[0].appointment_id
result = scheduler.adjust_appointment(adjust_id, "14:00", 90, 2, today)
assert result.success, "调整应成功"
print(f"✅ 调整预约 #{adjust_id} 到 14:00-15:30 2号技师")

# 清理
db.close()
os.remove(TEST_DB)

print("\n" + "=" * 50)
print("🎉 所有测试通过！")
print("=" * 50)
