from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .database import Base
class Employee(Base):
    __tablename__='employees'
    id: Mapped[str]=mapped_column(String, primary_key=True)
    name: Mapped[str]=mapped_column(String, index=True)
    role: Mapped[str]=mapped_column(String)
    hire_date: Mapped[str]=mapped_column(String)
    termination_date: Mapped[str|None]=mapped_column(String, nullable=True)
    status: Mapped[str]=mapped_column(String, default='재직')
    base_salary_gross: Mapped[float]=mapped_column(Float, default=0)
    ordinary_hourly_wage_gross: Mapped[float]=mapped_column(Float, default=0)
    contract_start_time: Mapped[str]=mapped_column(String, default='09:00')
    contract_end_time: Mapped[str]=mapped_column(String, default='18:00')
    break_minutes: Mapped[int]=mapped_column(Integer, default=60)
    social_insurance: Mapped[bool]=mapped_column(Boolean, default=True)
    income_tax_method: Mapped[str]=mapped_column(String, default='직접입력')
    incentive_enabled: Mapped[bool]=mapped_column(Boolean, default=True)
    memo: Mapped[str|None]=mapped_column(Text, nullable=True)
class WorkSchedule(Base):
    __tablename__='work_schedules'; id:Mapped[int]=mapped_column(primary_key=True)
    work_date:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str]=mapped_column(String,index=True)
    scheduled_start:Mapped[str]=mapped_column(String); scheduled_end:Mapped[str]=mapped_column(String)
    break_minutes:Mapped[int]=mapped_column(Integer,default=60); work_type:Mapped[str]=mapped_column(String,default='정상'); note:Mapped[str|None]=mapped_column(Text)
class AttendanceRaw(Base):
    __tablename__='attendance_raw'; id:Mapped[int]=mapped_column(primary_key=True)
    work_date:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str|None]=mapped_column(String,index=True); employee_name:Mapped[str|None]=mapped_column(String)
    original_clock_in:Mapped[str|None]=mapped_column(String); original_clock_out:Mapped[str|None]=mapped_column(String)
    adjusted_clock_in:Mapped[str|None]=mapped_column(String); adjusted_clock_out:Mapped[str|None]=mapped_column(String); source_file:Mapped[str|None]=mapped_column(String)
class AttendanceCalculated(Base):
    __tablename__='attendance_calculated'; id:Mapped[int]=mapped_column(primary_key=True)
    work_date:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str]=mapped_column(String,index=True)
    is_normal:Mapped[bool]=mapped_column(Boolean,default=False); is_late:Mapped[bool]=mapped_column(Boolean,default=False); is_early_leave:Mapped[bool]=mapped_column(Boolean,default=False)
    is_absent:Mapped[bool]=mapped_column(Boolean,default=False); is_fingerprint_missing:Mapped[bool]=mapped_column(Boolean,default=False)
    total_hours:Mapped[float]=mapped_column(Float,default=0); break_hours:Mapped[float]=mapped_column(Float,default=0); recognized_hours:Mapped[float]=mapped_column(Float,default=0)
    additional_hours:Mapped[float]=mapped_column(Float,default=0); overtime_hours:Mapped[float]=mapped_column(Float,default=0); evening_19_20_hours:Mapped[float]=mapped_column(Float,default=0)
    night_hours:Mapped[float]=mapped_column(Float,default=0); holiday_hours:Mapped[float]=mapped_column(Float,default=0)
class IncentiveRule(Base):
    __tablename__='incentive_rules'; id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String); incentive_item:Mapped[str]=mapped_column(String,index=True); calc_method:Mapped[str]=mapped_column(String)
    role:Mapped[str|None]=mapped_column(String); employee_id:Mapped[str|None]=mapped_column(String); item_name:Mapped[str|None]=mapped_column(String); shots:Mapped[int|None]=mapped_column(Integer)
    quantity_min:Mapped[int|None]=mapped_column(Integer); quantity_max:Mapped[int|None]=mapped_column(Integer); fixed_amount:Mapped[float|None]=mapped_column(Float); percent:Mapped[float|None]=mapped_column(Float)
    start_date:Mapped[str]=mapped_column(String,default='2026-01-01'); end_date:Mapped[str|None]=mapped_column(String); active:Mapped[bool]=mapped_column(Boolean,default=True); note:Mapped[str|None]=mapped_column(Text)
class IncentiveRaw(Base):
    __tablename__='incentive_raw'; id:Mapped[int]=mapped_column(primary_key=True)
    work_date:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str|None]=mapped_column(String,index=True); employee_name:Mapped[str|None]=mapped_column(String); role:Mapped[str|None]=mapped_column(String)
    incentive_item:Mapped[str]=mapped_column(String); detail_item:Mapped[str|None]=mapped_column(String); quantity:Mapped[float|None]=mapped_column(Float); shots:Mapped[int|None]=mapped_column(Integer)
    sales_amount:Mapped[float|None]=mapped_column(Float); direct_amount:Mapped[float|None]=mapped_column(Float); patient_name:Mapped[str|None]=mapped_column(String); note:Mapped[str|None]=mapped_column(Text)
class IncentiveCalculated(Base):
    __tablename__='incentive_calculated'; id:Mapped[int]=mapped_column(primary_key=True)
    pay_month:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str]=mapped_column(String,index=True); incentive_item:Mapped[str]=mapped_column(String); amount_gross:Mapped[float]=mapped_column(Float,default=0); raw_id:Mapped[int|None]=mapped_column(Integer)
class Deduction(Base):
    __tablename__='deductions'; id:Mapped[int]=mapped_column(primary_key=True)
    pay_month:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str]=mapped_column(String,index=True)
    national_pension:Mapped[float]=mapped_column(Float,default=0); health_insurance:Mapped[float]=mapped_column(Float,default=0); long_term_care:Mapped[float]=mapped_column(Float,default=0); employment_insurance:Mapped[float]=mapped_column(Float,default=0); income_tax:Mapped[float]=mapped_column(Float,default=0); local_income_tax:Mapped[float]=mapped_column(Float,default=0); other_deduction:Mapped[float]=mapped_column(Float,default=0)
class PayrollRun(Base):
    __tablename__='payroll_runs'; id:Mapped[int]=mapped_column(primary_key=True); pay_month:Mapped[str]=mapped_column(String,index=True); employee_id:Mapped[str]=mapped_column(String,index=True)
    base_salary_gross:Mapped[float]=mapped_column(Float,default=0); overtime_gross:Mapped[float]=mapped_column(Float,default=0); additional_gross:Mapped[float]=mapped_column(Float,default=0); evening_19_20_gross:Mapped[float]=mapped_column(Float,default=0); night_gross:Mapped[float]=mapped_column(Float,default=0); holiday_gross:Mapped[float]=mapped_column(Float,default=0)
    shockwave_gross:Mapped[float]=mapped_column(Float,default=0); manual_gross:Mapped[float]=mapped_column(Float,default=0); c_arm_gross:Mapped[float]=mapped_column(Float,default=0); c_arm_aftercare_gross:Mapped[float]=mapped_column(Float,default=0); injection_gross:Mapped[float]=mapped_column(Float,default=0); other_allowance_gross:Mapped[float]=mapped_column(Float,default=0)
    total_gross:Mapped[float]=mapped_column(Float,default=0); total_deduction:Mapped[float]=mapped_column(Float,default=0); net_pay:Mapped[float]=mapped_column(Float,default=0); confirmed:Mapped[bool]=mapped_column(Boolean,default=False)
class PayrollItem(Base):
    __tablename__='payroll_items'; id:Mapped[int]=mapped_column(primary_key=True); payroll_run_id:Mapped[int]=mapped_column(Integer); item_name:Mapped[str]=mapped_column(String); amount:Mapped[float]=mapped_column(Float)
class PayrollConfirmation(Base):
    __tablename__='payroll_confirmations'; id:Mapped[int]=mapped_column(primary_key=True); pay_month:Mapped[str]=mapped_column(String); confirmed_by:Mapped[str]=mapped_column(String); confirmed_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); canceled:Mapped[bool]=mapped_column(Boolean,default=False)
class ExceptionLog(Base):
    __tablename__='exception_logs'; id:Mapped[int]=mapped_column(primary_key=True)
    occurred_date:Mapped[str|None]=mapped_column(String); employee_id:Mapped[str|None]=mapped_column(String); employee_name:Mapped[str|None]=mapped_column(String); exception_type:Mapped[str]=mapped_column(String,index=True); original_value:Mapped[str|None]=mapped_column(Text); adjusted_value:Mapped[str|None]=mapped_column(Text); status:Mapped[str]=mapped_column(String,default='미확인'); admin_memo:Mapped[str|None]=mapped_column(Text)
class AuditLog(Base):
    __tablename__='audit_logs'; id:Mapped[int]=mapped_column(primary_key=True); changed_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); changed_by:Mapped[str]=mapped_column(String); before_value:Mapped[str]=mapped_column(Text); after_value:Mapped[str]=mapped_column(Text); reason:Mapped[str]=mapped_column(Text)
class Setting(Base):
    __tablename__='settings'; key:Mapped[str]=mapped_column(String,primary_key=True); value:Mapped[str]=mapped_column(Text)
