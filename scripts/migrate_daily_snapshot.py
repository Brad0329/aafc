"""과거 일별 마감 데이터(스냅샷+코치정산) 벌크 이관 — MSSQL 확정본 → Postgres.

원본 lf_daily_total_data / lf_daily_coachdata_new 의 proc_dt >= FROM_DT(2026-01-01) 분을
reports_dailytotaldata / reports_dailycoachdatanew 로 복사한다(과거 시점 스냅샷 보존).
재실행 안전: 대상 기간(proc_dt>=FROM_DT)을 먼저 삭제 후 적재.

사용: python scripts/migrate_daily_snapshot.py
"""
import os
import sys

import django
import pyodbc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.reports.models import DailyTotalData, DailyCoachDataNew  # noqa: E402

MSSQL = ('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;'
         'DATABASE=2018_junior;UID=juni_db;PWD=juniordb1234')
FROM_DT = '20260101'
BATCH = 5000


def s(v):
    return '' if v is None else str(v)


def n(v):
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def migrate_total(cn_):
    print('=== lf_daily_total_data → reports_dailytotaldata ===')
    DailyTotalData.objects.filter(proc_dt__gte=FROM_DT).delete()
    cur = cn_.cursor()
    cur.execute("""SELECT proc_dt,rownum,no_seq,member_id,MEMBER_NAME,child_id,mhtel,CHILD_NAME,CARD_NUM,
        apply_gubun,sta_name,lecture_code,lecture_title,COACH_NAME,lec_cycle,lec_period,lecture_stats,
        pay_price,lec_price,join_price,lec_course_ym_amt,pay_stats,pay_method,PAY_DT,cancel_date,cancel_code,
        cancel_desc,start_dt,end_dt,course_ym,course_ym_amt,insert_id,INSERT_DT
        FROM lf_daily_total_data WHERE proc_dt >= ?""", FROM_DT)
    batch, total = [], 0
    for r in cur:
        batch.append(DailyTotalData(
            proc_dt=s(r[0]), rownum=n(r[1]), no_seq=n(r[2]), member_id=s(r[3]), member_name=s(r[4]),
            child_id=s(r[5]), mhtel=s(r[6]), child_name=s(r[7]), card_num=s(r[8]), apply_gubun=s(r[9]),
            sta_name=s(r[10]), lecture_code=n(r[11]), lecture_title=s(r[12]), coach_name=s(r[13]),
            lec_cycle=s(r[14]), lec_period=s(r[15]), lecture_stats=s(r[16]), pay_price=n(r[17]),
            lec_price=n(r[18]), join_price=n(r[19]), lec_course_ym_amt=n(r[20]), pay_stats=s(r[21]),
            pay_method=s(r[22]), pay_dt=s(r[23]), cancel_date=s(r[24]), cancel_code=s(r[25]),
            cancel_desc=s(r[26]), start_dt=s(r[27]), end_dt=s(r[28]), course_ym=s(r[29]),
            course_ym_amt=n(r[30]), insert_id=s(r[31]), insert_dt=s(r[32]),
        ))
        if len(batch) >= BATCH:
            DailyTotalData.objects.bulk_create(batch); total += len(batch); batch = []
            print(f'  ...{total:,}')
    if batch:
        DailyTotalData.objects.bulk_create(batch); total += len(batch)
    print(f'  완료: {total:,}행')


def migrate_coach(cn_):
    print('=== lf_daily_coachdata_new → reports_dailycoachdatanew ===')
    DailyCoachDataNew.objects.filter(proc_dt__gte=FROM_DT).delete()
    cur = cn_.cursor()
    cur.execute("""SELECT proc_dt,pay_seq,member_id,child_id,order_id,pay_dt,insert_dt,pay_method,course_ym,
        sta_code,lecture_code,coach_code,coach_name,cl_cnt,m1001_price,m1002_price,m1003_price,m1003_b_price,
        m1006_price,m1007_b_price,m1009_b_price,m2001_price,m2002_price,regdate
        FROM lf_daily_coachdata_new WHERE proc_dt >= ?""", FROM_DT)
    batch, total = [], 0
    for r in cur:
        batch.append(DailyCoachDataNew(
            proc_dt=s(r[0]), pay_seq=n(r[1]), member_id=s(r[2]), child_id=s(r[3]), order_id=s(r[4]),
            pay_dt=r[5], insert_dt=r[6], pay_method=s(r[7]), course_ym=s(r[8]), sta_code=n(r[9]),
            lecture_code=n(r[10]), coach_code=n(r[11]), coach_name=s(r[12]), cl_cnt=n(r[13]),
            m1001_price=n(r[14]), m1002_price=n(r[15]), m1003_price=n(r[16]), m1003_b_price=n(r[17]),
            m1006_price=n(r[18]), m1007_b_price=n(r[19]), m1009_b_price=n(r[20]), m2001_price=n(r[21]),
            m2002_price=n(r[22]), regdate=r[23],
        ))
        if len(batch) >= BATCH:
            DailyCoachDataNew.objects.bulk_create(batch); total += len(batch); batch = []
            print(f'  ...{total:,}')
    if batch:
        DailyCoachDataNew.objects.bulk_create(batch); total += len(batch)
    print(f'  완료: {total:,}행')


if __name__ == '__main__':
    conn = pyodbc.connect(MSSQL)
    migrate_total(conn)
    migrate_coach(conn)
    print('DONE')
