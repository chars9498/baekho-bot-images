from .database import Base, engine, SessionLocal
from .models import *
Base.metadata.create_all(engine); db=SessionLocal()
db.query(Employee).delete(); db.query(IncentiveRule).delete(); db.query(Setting).delete()
for e in [('PT01','김물리','물리치료사',2800000,18000),('PT02','이치료','물리치료사',2700000,17000),('RAD01','박방사','방사선사',3000000,19000),('NA01','최간호','간호조무사',2400000,15000),('DR01','정의사','의사',8000000,50000),('ADM01','윤행정','행정직',2600000,16000)]: db.add(Employee(id=e[0],name=e[1],role=e[2],hire_date='2026-01-01',base_salary_gross=e[3],ordinary_hourly_wage_gross=e[4]))
for shots in [1000,1500,2000,2500,3000]: db.add(IncentiveRule(name=f'충격파 {shots}타',incentive_item='충격파',calc_method='타수별금액',role='물리치료사',shots=shots,fixed_amount=shots))
db.add_all([IncentiveRule(name='도수 14%',incentive_item='도수치료',calc_method='매출비율',role='물리치료사',percent=14),IncentiveRule(name='씨암 1건',incentive_item='씨암',calc_method='건별고정금액',role='방사선사',fixed_amount=3000),IncentiveRule(name='씨암후처치 1건',incentive_item='씨암후처치',calc_method='건별고정금액',role='간호조무사',fixed_amount=1000),IncentiveRule(name='주사 A',incentive_item='주사',calc_method='항목별단가',role='의사',item_name='주사 A',fixed_amount=5000),IncentiveRule(name='주사 B',incentive_item='주사',calc_method='항목별단가',role='의사',item_name='주사 B',fixed_amount=10000),Setting(key='hospital_name',value='샘플병원')])
db.commit(); db.close(); print('seeded')
