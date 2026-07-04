import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import Base, engine, SessionLocal
from backend.app.models import *
from backend.app.services import calculate_attendance, calculate_incentives, run_payroll
client=TestClient(app)
@pytest.fixture(autouse=True)
def clean():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine); yield

def seed(db):
    db.add(Employee(id='E1',name='김물리',role='물리치료사',hire_date='2026-01-01',base_salary_gross=3000000,ordinary_hourly_wage_gross=20000))
    db.add(Employee(id='R1',name='박방사',role='방사선사',hire_date='2026-01-01',base_salary_gross=3000000,ordinary_hourly_wage_gross=20000))
    db.add(Employee(id='D1',name='정의사',role='의사',hire_date='2026-01-01',base_salary_gross=8000000,ordinary_hourly_wage_gross=50000))
    db.add_all([IncentiveRule(name='충격파1500',incentive_item='충격파',calc_method='타수별금액',role='물리치료사',shots=1500,fixed_amount=1500),IncentiveRule(name='도수14',incentive_item='도수치료',calc_method='매출비율',role='물리치료사',percent=14),IncentiveRule(name='씨암',incentive_item='씨암',calc_method='건별고정금액',role='방사선사',fixed_amount=3000),IncentiveRule(name='주사A',incentive_item='주사',calc_method='항목별단가',role='의사',item_name='주사 A',fixed_amount=5000)])
    db.commit()

def test_employee_create():
    r=client.post('/employees',json={'id':'A1','name':'홍길동'}); assert r.status_code==200 and r.json()['name']=='홍길동'

def test_attendance_upload_and_missing_exceptions():
    db=SessionLocal(); seed(db); raw=AttendanceRaw(work_date='2026-07-01',employee_id='E1',employee_name='김물리',original_clock_in=None,original_clock_out=None); db.add(raw); db.flush(); calculate_attendance(db,raw); db.commit();
    types=[e.exception_type for e in db.query(ExceptionLog).all()]; assert '출근지문 누락' in types and '퇴근지문 누락' in types; db.close()

def test_evening_19_20_hours():
    db=SessionLocal(); seed(db); db.add(WorkSchedule(work_date='2026-07-01',employee_id='E1',scheduled_start='09:00',scheduled_end='18:00')); raw=AttendanceRaw(work_date='2026-07-01',employee_id='E1',employee_name='김물리',original_clock_in='09:00',original_clock_out='20:00'); db.add(raw); db.flush(); c=calculate_attendance(db,raw); assert c.evening_19_20_hours==1; db.close()

def test_incentive_calculations_and_missing_shockwave_rule():
    db=SessionLocal(); seed(db); db.add_all([IncentiveRaw(work_date='2026-07-01',employee_id='E1',incentive_item='충격파',shots=1500),IncentiveRaw(work_date='2026-07-01',employee_id='E1',incentive_item='충격파',shots=1700),IncentiveRaw(work_date='2026-07-01',employee_id='E1',incentive_item='도수치료',sales_amount=100000),IncentiveRaw(work_date='2026-07-01',employee_id='R1',incentive_item='씨암',quantity=2),IncentiveRaw(work_date='2026-07-01',employee_id='D1',incentive_item='주사',detail_item='주사 A',quantity=3)]); db.commit(); calculate_incentives(db,'2026-07'); db.commit();
    vals={(i.employee_id,i.incentive_item):i.amount_gross for i in db.query(IncentiveCalculated).all()}; assert vals[('E1','충격파')]==1500; assert vals[('E1','도수치료')]==14000; assert vals[('R1','씨암')]==6000; assert vals[('D1','주사')]==15000; assert db.query(ExceptionLog).filter_by(exception_type='충격파 타수 규칙 없음').count()==1; db.close()

def test_payroll_total_net_and_audit_after_confirmation():
    db=SessionLocal(); seed(db); db.add(IncentiveRaw(work_date='2026-07-01',employee_id='E1',incentive_item='충격파',shots=1500)); db.add(Deduction(pay_month='2026-07',employee_id='E1',national_pension=1000,health_insurance=1000)); db.commit(); run_payroll(db,'2026-07'); db.commit(); p=db.query(PayrollRun).filter_by(employee_id='E1').first(); assert p.total_gross==3001500 and p.net_pay==2999500; p.confirmed=True; db.add(AuditLog(changed_by='admin',before_value='3001500',after_value='3002500',reason='수정')); db.commit(); assert db.query(AuditLog).count()==1; db.close()
