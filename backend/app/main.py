from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd, io, shutil, os
from openpyxl import Workbook
from .database import Base, engine, get_db
from .models import *
from .services import match_employee, log_exception, calculate_attendance, calculate_incentives, run_payroll
Base.metadata.create_all(engine)
app=FastAPI(title='Hospital Payroll')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
class EmployeeIn(BaseModel):
    id:str; name:str; role:str='기타'; hire_date:str='2026-01-01'; termination_date:str|None=None; status:str='재직'; base_salary_gross:float=0; ordinary_hourly_wage_gross:float=0; contract_start_time:str='09:00'; contract_end_time:str='18:00'; break_minutes:int=60; social_insurance:bool=True; income_tax_method:str='직접입력'; incentive_enabled:bool=True; memo:str|None=None
class ScheduleIn(BaseModel):
    work_date:str; employee_id:str; scheduled_start:str='09:00'; scheduled_end:str='18:00'; break_minutes:int=60; work_type:str='정상'; note:str|None=None
@app.get('/employees')
def employees(db:Session=Depends(get_db)): return db.query(Employee).all()
@app.post('/employees')
def upsert_employee(x:EmployeeIn, db:Session=Depends(get_db)):
    e=db.get(Employee,x.id) or Employee(id=x.id); [setattr(e,k,v) for k,v in x.model_dump().items()]; db.merge(e); db.commit(); return e
@app.get('/schedules')
def schedules(db:Session=Depends(get_db)): return db.query(WorkSchedule).all()
@app.post('/schedules')
def add_schedule(x:ScheduleIn, db:Session=Depends(get_db)):
    s=WorkSchedule(**x.model_dump()); db.add(s); db.commit(); return s
@app.post('/upload/attendance')
async def upload_attendance(file:UploadFile=File(...), db:Session=Depends(get_db)):
    df=pd.read_excel(await file.read()) if file.filename.endswith(('xlsx','xls')) else pd.read_csv(file.file)
    for _,r in df.iterrows():
        emp_id=str(r.get('직원ID','')).strip() or None; name=str(r.get('직원명','')).strip() or None
        try: emp=match_employee(db,emp_id,name); emp_id=emp.id; name=emp.name
        except ValueError as e: log_exception(db,str(r.get('날짜')),emp_id,name,str(e))
        dup=db.query(AttendanceRaw).filter_by(work_date=str(r.get('날짜'))[:10],employee_id=emp_id).first()
        if dup: log_exception(db,str(r.get('날짜'))[:10],emp_id,name,'중복 근태')
        raw=AttendanceRaw(work_date=str(r.get('날짜'))[:10],employee_id=emp_id,employee_name=name,original_clock_in=None if pd.isna(r.get('출근시간')) else str(r.get('출근시간'))[:5],original_clock_out=None if pd.isna(r.get('퇴근시간')) else str(r.get('퇴근시간'))[:5],source_file=file.filename)
        db.add(raw); db.flush(); calculate_attendance(db,raw)
    db.commit(); return {'ok':True}
@app.post('/upload/incentives')
async def upload_incentives(file:UploadFile=File(...), db:Session=Depends(get_db)):
    df=pd.read_excel(await file.read())
    for _,r in df.iterrows(): db.add(IncentiveRaw(work_date=str(r.get('날짜'))[:10],employee_id=str(r.get('직원ID','')).strip() or None,employee_name=str(r.get('직원명','')).strip() or None,role=r.get('직군'),incentive_item=r.get('인센티브항목'),detail_item=r.get('세부항목'),quantity=r.get('수량') if not pd.isna(r.get('수량')) else None,shots=r.get('타수') if not pd.isna(r.get('타수')) else None,sales_amount=r.get('매출액') if not pd.isna(r.get('매출액')) else None,direct_amount=r.get('직접입력금액') if not pd.isna(r.get('직접입력금액')) else None,patient_name=r.get('환자명'),note=r.get('비고')))
    db.commit(); return {'ok':True}
@app.get('/incentive-rules')
def rules(db:Session=Depends(get_db)): return db.query(IncentiveRule).all()
@app.post('/payroll/run/{pay_month}')
def payroll(pay_month:str, db:Session=Depends(get_db)): run_payroll(db,pay_month); db.commit(); return db.query(PayrollRun).filter_by(pay_month=pay_month).all()
@app.get('/payroll/{pay_month}')
def payrolls(pay_month:str, db:Session=Depends(get_db)): return db.query(PayrollRun).filter_by(pay_month=pay_month).all()
@app.post('/payroll/confirm/{pay_month}')
def confirm(pay_month:str, db:Session=Depends(get_db)):
    for r in db.query(PayrollRun).filter_by(pay_month=pay_month): r.confirmed=True
    db.add(PayrollConfirmation(pay_month=pay_month,confirmed_by='admin')); db.commit(); return {'confirmed':pay_month}
@app.post('/payroll/audit')
def audit(employee_id:str,pay_month:str,before:str,after:str,reason:str,db:Session=Depends(get_db)):
    db.add(AuditLog(changed_by='admin',before_value=before,after_value=after,reason=reason)); db.commit(); return {'ok':True}
@app.get('/exceptions')
def exceptions(db:Session=Depends(get_db)): return db.query(ExceptionLog).all()
@app.get('/dashboard/{pay_month}')
def dashboard(pay_month:str, db:Session=Depends(get_db)):
    rows=db.query(PayrollRun).filter_by(pay_month=pay_month).all(); return {'selected_month':pay_month,'employee_count':db.query(Employee).count(),'total_gross':sum(r.total_gross for r in rows),'total_deduction':sum(r.total_deduction for r in rows),'total_net_pay':sum(r.net_pay for r in rows),'shockwave_total':sum(r.shockwave_gross for r in rows),'manual_total':sum(r.manual_gross for r in rows),'c_arm_total':sum(r.c_arm_gross for r in rows),'c_arm_aftercare_total':sum(r.c_arm_aftercare_gross for r in rows),'injection_total':sum(r.injection_gross for r in rows),'unchecked_exceptions':db.query(ExceptionLog).filter_by(status='미확인').count(),'confirmed':all(r.confirmed for r in rows) if rows else False}
@app.get('/payslip/{pay_month}/{employee_id}.xlsx')
def payslip(pay_month:str,employee_id:str,db:Session=Depends(get_db)):
    r=db.query(PayrollRun).filter_by(pay_month=pay_month,employee_id=employee_id).first(); e=db.get(Employee,employee_id); wb=Workbook(); ws=wb.active; ws.title='급여명세서';
    data=[['병원명',db.get(Setting,'hospital_name').value if db.get(Setting,'hospital_name') else '샘플병원'],['지급월',pay_month],['직원명',e.name],['직군',e.role],['기본급',r.base_salary_gross],['연장수당',r.overtime_gross],['추가근무수당',r.additional_gross],['19-20 추가근무수당',r.evening_19_20_gross],['충격파 인센티브',r.shockwave_gross],['도수치료 인센티브',r.manual_gross],['씨암 인센티브',r.c_arm_gross],['씨암후처치 인센티브',r.c_arm_aftercare_gross],['주사 인센티브',r.injection_gross],['총지급액',r.total_gross],['총공제액',r.total_deduction],['실수령액',r.net_pay],['계산방법','총지급액_세전 - 총공제액']]
    [ws.append(x) for x in data]; bio=io.BytesIO(); wb.save(bio); bio.seek(0); return StreamingResponse(bio,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
@app.post('/backup')
def backup(): os.makedirs('backups',exist_ok=True); shutil.copyfile('hospital_payroll.db','backups/hospital_payroll.db'); return {'file':'backups/hospital_payroll.db'}
