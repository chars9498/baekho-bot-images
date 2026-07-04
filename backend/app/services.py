from datetime import datetime, time
from sqlalchemy.orm import Session
from .models import *

def minutes(t):
    h,m=map(int,str(t).split(':')[:2]); return h*60+m

def month_of(d): return str(d)[:7]

def match_employee(db:Session, emp_id, name):
    if emp_id:
        e=db.get(Employee,str(emp_id));
        if e: return e
    if name:
        rows=db.query(Employee).filter(Employee.name==str(name)).all()
        if len(rows)==1: return rows[0]
        if len(rows)>1: raise ValueError('직원명 중복')
    raise ValueError('직원마스터 없음')

def log_exception(db, date, emp_id, name, typ, original='', adjusted=''):
    db.add(ExceptionLog(occurred_date=date,employee_id=emp_id,employee_name=name,exception_type=typ,original_value=str(original),adjusted_value=str(adjusted)))

def calculate_attendance(db:Session, raw:AttendanceRaw):
    emp = db.get(Employee, raw.employee_id) if raw.employee_id else None
    sched = db.query(WorkSchedule).filter_by(work_date=raw.work_date, employee_id=raw.employee_id).first() if raw.employee_id else None
    if not sched: log_exception(db, raw.work_date, raw.employee_id, raw.employee_name, '근무표 없음')
    cin=raw.adjusted_clock_in or raw.original_clock_in or (sched.scheduled_start if sched else None)
    cout=raw.adjusted_clock_out or raw.original_clock_out or (sched.scheduled_end if sched else None)
    missing=not raw.original_clock_in or not raw.original_clock_out
    if not raw.original_clock_in: log_exception(db, raw.work_date, raw.employee_id, raw.employee_name, '출근지문 누락')
    if not raw.original_clock_out: log_exception(db, raw.work_date, raw.employee_id, raw.employee_name, '퇴근지문 누락')
    if not cin or not cout or not emp: return None
    total=max(0,(minutes(cout)-minutes(cin))/60); br=(sched.break_minutes if sched else emp.break_minutes)/60
    rec=max(0,total-br); add=max(0, minutes(cout)-max(minutes(sched.scheduled_end if sched else emp.contract_end_time), minutes(cin)))/60
    evening=max(0, min(minutes(cout),1200)-max(minutes(cin),1140))/60
    calc=AttendanceCalculated(work_date=raw.work_date,employee_id=emp.id,is_normal=not missing,is_late=sched and minutes(cin)>minutes(sched.scheduled_start),is_early_leave=sched and minutes(cout)<minutes(sched.scheduled_end),is_absent=total==0,is_fingerprint_missing=missing,total_hours=total,break_hours=br,recognized_hours=rec,additional_hours=add,overtime_hours=max(0,rec-8),evening_19_20_hours=evening)
    if total>16: log_exception(db, raw.work_date, emp.id, emp.name, '비정상적으로 긴 근무시간', total)
    db.add(calc); return calc

def find_rule(db, raw:IncentiveRaw):
    q=db.query(IncentiveRule).filter_by(active=True,incentive_item=raw.incentive_item)
    rules=q.all()
    for r in rules:
        if r.employee_id and r.employee_id!=raw.employee_id: continue
        if r.role and raw.role and r.role!=raw.role: continue
        if r.calc_method=='타수별금액' and r.shots==raw.shots: return r
        if r.calc_method=='항목별단가' and (not r.item_name or r.item_name==raw.detail_item): return r
        if r.calc_method in ('건별고정금액','매출비율','직접입력금액'): return r
    return None

def calculate_incentives(db:Session, pay_month:str):
    db.query(IncentiveCalculated).filter_by(pay_month=pay_month).delete()
    raws=db.query(IncentiveRaw).filter(IncentiveRaw.work_date.like(pay_month+'%')).all()
    for raw in raws:
        try:
            emp=match_employee(db, raw.employee_id, raw.employee_name); raw.employee_id=emp.id; raw.role=raw.role or emp.role
            if not emp.incentive_enabled: continue
        except ValueError as e:
            log_exception(db, raw.work_date, raw.employee_id, raw.employee_name, str(e)); continue
        rule=find_rule(db, raw)
        if not rule:
            log_exception(db, raw.work_date, raw.employee_id, raw.employee_name, '충격파 타수 규칙 없음' if raw.incentive_item=='충격파' else '인센티브 규칙 없음', raw.shots or raw.detail_item); continue
        if rule.calc_method=='타수별금액': amount=rule.fixed_amount or 0
        elif rule.calc_method in ('건별고정금액','항목별단가'): amount=(raw.quantity or 1)*(rule.fixed_amount or 0)
        elif rule.calc_method=='매출비율': amount=(raw.sales_amount or 0)*(rule.percent or 0)/100
        elif rule.calc_method=='직접입력금액': amount=raw.direct_amount or 0
        else: amount=0
        db.add(IncentiveCalculated(pay_month=pay_month,employee_id=emp.id,incentive_item=raw.incentive_item,amount_gross=amount,raw_id=raw.id))

def run_payroll(db:Session, pay_month:str):
    calculate_incentives(db,pay_month); db.query(PayrollRun).filter_by(pay_month=pay_month).delete()
    for emp in db.query(Employee).filter(Employee.status=='재직').all():
        att=db.query(AttendanceCalculated).filter(AttendanceCalculated.employee_id==emp.id, AttendanceCalculated.work_date.like(pay_month+'%')).all()
        evening=sum(a.evening_19_20_hours for a in att); overtime=sum(a.overtime_hours for a in att); add=sum(a.additional_hours for a in att)
        incs=db.query(IncentiveCalculated).filter_by(pay_month=pay_month,employee_id=emp.id).all()
        by={k:sum(i.amount_gross for i in incs if i.incentive_item==k) for k in ['충격파','도수치료','씨암','씨암후처치','주사','기타']}
        d=db.query(Deduction).filter_by(pay_month=pay_month,employee_id=emp.id).first() or Deduction(pay_month=pay_month,employee_id=emp.id)
        total_d=sum([d.national_pension,d.health_insurance,d.long_term_care,d.employment_insurance,d.income_tax,d.local_income_tax,d.other_deduction])
        overtime_g=overtime*emp.ordinary_hourly_wage_gross*1.5; add_g=add*emp.ordinary_hourly_wage_gross; evening_g=evening*emp.ordinary_hourly_wage_gross
        total=emp.base_salary_gross+overtime_g+add_g+evening_g+by['충격파']+by['도수치료']+by['씨암']+by['씨암후처치']+by['주사']+by['기타']
        if total_d>total: log_exception(db,pay_month,emp.id,emp.name,'공제액이 총지급액보다 큼',total_d,total)
        if total-total_d<0: log_exception(db,pay_month,emp.id,emp.name,'음수 급여')
        db.add(PayrollRun(pay_month=pay_month,employee_id=emp.id,base_salary_gross=emp.base_salary_gross,overtime_gross=overtime_g,additional_gross=add_g,evening_19_20_gross=evening_g,shockwave_gross=by['충격파'],manual_gross=by['도수치료'],c_arm_gross=by['씨암'],c_arm_aftercare_gross=by['씨암후처치'],injection_gross=by['주사'],other_allowance_gross=by['기타'],total_gross=total,total_deduction=total_d,net_pay=total-total_d))
