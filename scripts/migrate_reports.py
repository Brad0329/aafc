"""
MSSQL → PostgreSQL 리포트+통계 데이터 이관 스크립트
실행: python scripts/migrate_reports.py
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

import pyodbc
from django.utils import timezone
from apps.enrollment.models import Attendance, ChangeHistory
from apps.reports.models import (
    DailyTotalData, DailyCoachData, DailyCoachDataNew,
    DailyCoachDataMonth, MonthlyData,
)

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)

FETCH_SIZE = 10000
BULK_SIZE = 5000


def safe_str(val):
    if val is None:
        return ''
    return str(val).strip()


def checkint(val):
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def make_aware(dt):
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


# ─── 1. Attendance (lf_student_attendance) ───
def migrate_attendance(cursor):
    print('\n=== Attendance (lf_student_attendance) 이관 시작 ===')
    Attendance.objects.all().delete()

    cursor.execute("SELECT COUNT(*) FROM lf_student_attendance")
    total = cursor.fetchone()[0]
    print(f'원본 건수: {total:,}')

    cursor.execute("""
        SELECT no_seq, local_code, sta_code, lecture_code, child_id,
               attendance_dt, attendance_gbn, attendance_desc,
               insert_dt, insert_id, mata, app_month, complete_yn,
               uid, match_ymd, ticket_no, ticket_no2
          FROM lf_student_attendance
         ORDER BY no_seq
    """)

    count = 0
    while True:
        rows = cursor.fetchmany(FETCH_SIZE)
        if not rows:
            break
        batch = []
        for row in rows:
            batch.append(Attendance(
                id=checkint(row[0]),
                local_code=checkint(row[1]),
                sta_code=checkint(row[2]),
                lecture_code=checkint(row[3]),
                child_id=safe_str(row[4]),
                attendance_dt=safe_str(row[5]),
                attendance_gbn=safe_str(row[6]),
                attendance_desc=safe_str(row[7]),
                insert_dt=make_aware(row[8]),
                insert_id=safe_str(row[9]),
                mata=safe_str(row[10]),
                app_month=safe_str(row[11]),
                complete_yn=safe_str(row[12]) or 'N',
                uid=checkint(row[13]),
                match_ymd=safe_str(row[14]),
                ticket_no=safe_str(row[15]),
                ticket_no2=safe_str(row[16]),
            ))
        Attendance.objects.bulk_create(batch, batch_size=BULK_SIZE)
        count += len(batch)
        print(f'  {count:,} / {total:,} 건 완료')

    print(f'Attendance: {count:,}건 이관 완료')


# ─── 2. ChangeHistory (lf_change_history) ───
def migrate_change_history(cursor):
    print('\n=== ChangeHistory (lf_change_history) 이관 시작 ===')
    ChangeHistory.objects.all().delete()

    cursor.execute("""
        SELECT his_seq, member_id, child_id, chg_gbn, chg_desc,
               no_seq, src_seq, reg_dt, reg_id
          FROM lf_change_history
         ORDER BY his_seq
    """)

    count = 0
    for row in cursor.fetchall():
        ChangeHistory.objects.create(
            id=checkint(row[0]),
            member_id=safe_str(row[1]),
            child_id=safe_str(row[2]),
            chg_gbn=safe_str(row[3]),
            chg_desc=safe_str(row[4]),
            no_seq=checkint(row[5]),
            src_seq=checkint(row[6]),
            reg_dt=make_aware(row[7]),
            reg_id=safe_str(row[8]),
        )
        count += 1

    print(f'ChangeHistory: {count}건 이관 완료')


# ─── 3. DailyTotalData (lf_daily_total_data) ───
def migrate_daily_total_data(cursor):
    print('\n=== DailyTotalData (lf_daily_total_data) 이관 시작 ===')
    DailyTotalData.objects.all().delete()

    cursor.execute("SELECT COUNT(*) FROM lf_daily_total_data")
    total = cursor.fetchone()[0]
    print(f'원본 건수: {total:,}')

    cursor.execute("""
        SELECT proc_dt, member_id, MEMBER_NAME, child_id,
               mhtel, CHILD_NAME, CARD_NUM, apply_gubun, sta_name,
               lecture_code, lecture_title, COACH_NAME, lec_cycle, lec_period,
               lecture_stats, pay_price, lec_price, join_price, lec_course_ym_amt,
               pay_stats, pay_method, PAY_DT, cancel_date, cancel_code,
               cancel_desc, start_dt, end_dt, course_ym, course_ym_amt,
               insert_id, INSERT_DT
          FROM lf_daily_total_data
    """)

    count = 0
    while True:
        rows = cursor.fetchmany(FETCH_SIZE)
        if not rows:
            break
        batch = []
        for row in rows:
            batch.append(DailyTotalData(
                proc_dt=safe_str(row[0]),
                member_id=safe_str(row[1]),
                member_name=safe_str(row[2]),
                child_id=safe_str(row[3]),
                mhtel=safe_str(row[4]),
                child_name=safe_str(row[5]),
                card_num=safe_str(row[6]),
                apply_gubun=safe_str(row[7]),
                sta_name=safe_str(row[8]),
                lecture_code=checkint(row[9]),
                lecture_title=safe_str(row[10]),
                coach_name=safe_str(row[11]),
                lec_cycle=safe_str(row[12]),
                lec_period=safe_str(row[13]),
                lecture_stats=safe_str(row[14]),
                pay_price=checkint(row[15]),
                lec_price=checkint(row[16]),
                join_price=checkint(row[17]),
                lec_course_ym_amt=checkint(row[18]),
                pay_stats=safe_str(row[19]),
                pay_method=safe_str(row[20]),
                pay_dt=safe_str(row[21]),
                cancel_date=safe_str(row[22]),
                cancel_code=safe_str(row[23]),
                cancel_desc=safe_str(row[24]),
                start_dt=safe_str(row[25]),
                end_dt=safe_str(row[26]),
                course_ym=safe_str(row[27]),
                course_ym_amt=checkint(row[28]),
                insert_id=safe_str(row[29]),
                insert_dt=safe_str(row[30]),
            ))
        DailyTotalData.objects.bulk_create(batch, batch_size=BULK_SIZE)
        count += len(batch)
        if count % 100000 == 0 or count == total:
            print(f'  {count:,} / {total:,} 건 완료')

    print(f'DailyTotalData: {count:,}건 이관 완료')


# ─── 4. DailyCoachData (lf_daily_coachdata) ───
def migrate_daily_coachdata(cursor):
    print('\n=== DailyCoachData (lf_daily_coachdata) 이관 시작 ===')
    DailyCoachData.objects.all().delete()

    cursor.execute("""
        SELECT no_seq, course_ym, lgbn_name, sta_name, coach_name,
               member_id, child_id, cl_cnt,
               m1001_price, m1002_price, m10031_price, m10032_price,
               m1007_price, m2001_price, m2002_price,
               regdate, master_seq
          FROM lf_daily_coachdata
         ORDER BY no_seq
    """)

    count = 0
    batch = []
    for row in cursor.fetchall():
        batch.append(DailyCoachData(
            id=checkint(row[0]),
            course_ym=safe_str(row[1]),
            lgbn_name=safe_str(row[2]),
            sta_name=safe_str(row[3]),
            coach_name=safe_str(row[4]),
            member_id=safe_str(row[5]),
            child_id=safe_str(row[6]),
            cl_cnt=checkint(row[7]),
            m1001_price=checkint(row[8]),
            m1002_price=checkint(row[9]),
            m10031_price=checkint(row[10]),
            m10032_price=checkint(row[11]),
            m1007_price=checkint(row[12]),
            m2001_price=checkint(row[13]),
            m2002_price=checkint(row[14]),
            regdate=make_aware(row[15]),
            master_seq=checkint(row[16]),
        ))
        count += 1

        if len(batch) >= BULK_SIZE:
            DailyCoachData.objects.bulk_create(batch, batch_size=BULK_SIZE)
            batch = []
            if count % 50000 == 0:
                print(f'  {count:,}건 완료')

    if batch:
        DailyCoachData.objects.bulk_create(batch, batch_size=BULK_SIZE)

    print(f'DailyCoachData: {count:,}건 이관 완료')


# ─── 5. DailyCoachDataNew (lf_daily_coachdata_new) ───
def migrate_daily_coachdata_new(cursor):
    print('\n=== DailyCoachDataNew (lf_daily_coachdata_new) 이관 시작 ===')
    DailyCoachDataNew.objects.all().delete()

    cursor.execute("SELECT COUNT(*) FROM lf_daily_coachdata_new")
    total = cursor.fetchone()[0]
    print(f'원본 건수: {total:,}')

    cursor.execute("""
        SELECT proc_dt, pay_seq, member_id, child_id,
               order_id, pay_dt, insert_dt, pay_method, course_ym,
               sta_code, lecture_code, coach_code, coach_name, cl_cnt,
               m1001_price, m1002_price, m1003_price, m1003_b_price,
               m1006_price, m1007_b_price, m1009_b_price,
               m2001_price, m2002_price, regdate
          FROM lf_daily_coachdata_new
    """)

    count = 0
    while True:
        rows = cursor.fetchmany(FETCH_SIZE)
        if not rows:
            break
        batch = []
        for row in rows:
            batch.append(DailyCoachDataNew(
                proc_dt=safe_str(row[0]),
                pay_seq=checkint(row[1]),
                member_id=safe_str(row[2]),
                child_id=safe_str(row[3]),
                order_id=safe_str(row[4]),
                pay_dt=make_aware(row[5]),
                insert_dt=make_aware(row[6]),
                pay_method=safe_str(row[7]),
                course_ym=safe_str(row[8]),
                sta_code=checkint(row[9]),
                lecture_code=checkint(row[10]),
                coach_code=checkint(row[11]),
                coach_name=safe_str(row[12]),
                cl_cnt=checkint(row[13]),
                m1001_price=checkint(row[14]),
                m1002_price=checkint(row[15]),
                m1003_price=checkint(row[16]),
                m1003_b_price=checkint(row[17]),
                m1006_price=checkint(row[18]),
                m1007_b_price=checkint(row[19]),
                m1009_b_price=checkint(row[20]),
                m2001_price=checkint(row[21]),
                m2002_price=checkint(row[22]),
                regdate=make_aware(row[23]),
            ))
        DailyCoachDataNew.objects.bulk_create(batch, batch_size=BULK_SIZE)
        count += len(batch)
        if count % 100000 == 0 or count == total:
            print(f'  {count:,} / {total:,} 건 완료')

    print(f'DailyCoachDataNew: {count:,}건 이관 완료')


# ─── 6. DailyCoachDataMonth (lf_daily_coachdata_new_month) ───
def migrate_daily_coachdata_month(cursor):
    print('\n=== DailyCoachDataMonth (lf_daily_coachdata_new_month) 이관 시작 ===')
    DailyCoachDataMonth.objects.all().delete()

    cursor.execute("""
        SELECT pay_seq, member_id, child_id, order_id,
               pay_dt, insert_dt, pay_method, course_ym,
               sta_code, lecture_code, coach_code, coach_name, cl_cnt,
               m1001_price, m1002_price, m1003_price, m1003_b_price,
               m1006_price, m1007_b_price, m1009_b_price,
               m2001_price, m2002_price, regdate,
               new_coach_code, new_coach_name
          FROM lf_daily_coachdata_new_month
    """)

    count = 0
    batch = []
    for row in cursor.fetchall():
        batch.append(DailyCoachDataMonth(
            pay_seq=checkint(row[0]),
            member_id=safe_str(row[1]),
            child_id=safe_str(row[2]),
            order_id=safe_str(row[3]),
            pay_dt=make_aware(row[4]),
            insert_dt=make_aware(row[5]),
            pay_method=safe_str(row[6]),
            course_ym=safe_str(row[7]),
            sta_code=checkint(row[8]),
            lecture_code=checkint(row[9]),
            coach_code=checkint(row[10]),
            coach_name=safe_str(row[11]),
            cl_cnt=checkint(row[12]),
            m1001_price=checkint(row[13]),
            m1002_price=checkint(row[14]),
            m1003_price=checkint(row[15]),
            m1003_b_price=checkint(row[16]),
            m1006_price=checkint(row[17]),
            m1007_b_price=checkint(row[18]),
            m1009_b_price=checkint(row[19]),
            m2001_price=checkint(row[20]),
            m2002_price=checkint(row[21]),
            regdate=make_aware(row[22]),
            new_coach_code=checkint(row[23]),
            new_coach_name=safe_str(row[24]),
        ))
        count += 1

        if len(batch) >= BULK_SIZE:
            DailyCoachDataMonth.objects.bulk_create(batch, batch_size=BULK_SIZE)
            batch = []
            if count % 20000 == 0:
                print(f'  {count:,}건 완료')

    if batch:
        DailyCoachDataMonth.objects.bulk_create(batch, batch_size=BULK_SIZE)

    print(f'DailyCoachDataMonth: {count:,}건 이관 완료')


# ─── 7. MonthlyData (lf_monthly_data) ───
def migrate_monthly_data(cursor):
    print('\n=== MonthlyData (lf_monthly_data) 이관 시작 ===')
    MonthlyData.objects.all().delete()

    cursor.execute("""
        SELECT no_seq, proc_dt, code_desc, sta_name, sta_code,
               m_cnt, goal_cnt, tocl,
               newT_appl_cnt, newF_appl_cnt, renewT_appl_cnt, renewF_appl_cnt,
               again_appl_cnt, stats_tot_cnt, stats_ln_cnt, stats_lnT_cnt, stats_lnF_cnt,
               regdate
          FROM lf_monthly_data
         ORDER BY no_seq
    """)

    count = 0
    batch = []
    for row in cursor.fetchall():
        batch.append(MonthlyData(
            id=checkint(row[0]),
            proc_dt=safe_str(row[1]),
            code_desc=safe_str(row[2]),
            sta_name=safe_str(row[3]),
            sta_code=checkint(row[4]),
            m_cnt=checkint(row[5]),
            goal_cnt=checkint(row[6]),
            tocl=checkint(row[7]),
            newT_appl_cnt=checkint(row[8]),
            newF_appl_cnt=checkint(row[9]),
            renewT_appl_cnt=checkint(row[10]),
            renewF_appl_cnt=checkint(row[11]),
            again_appl_cnt=checkint(row[12]),
            stats_tot_cnt=checkint(row[13]),
            stats_ln_cnt=checkint(row[14]),
            stats_lnT_cnt=checkint(row[15]),
            stats_lnF_cnt=checkint(row[16]),
            regdate=make_aware(row[17]),
        ))
        count += 1

        if len(batch) >= BULK_SIZE:
            MonthlyData.objects.bulk_create(batch, batch_size=BULK_SIZE)
            batch = []

    if batch:
        MonthlyData.objects.bulk_create(batch, batch_size=BULK_SIZE)

    print(f'MonthlyData: {count:,}건 이관 완료')


# ─── 메인 ───
if __name__ == '__main__':
    print('=' * 60)
    print('Phase 7: 리포트+통계 데이터 이관 시작')
    print('=' * 60)

    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    try:
        migrate_attendance(cursor)
        migrate_change_history(cursor)
        migrate_daily_total_data(cursor)
        migrate_daily_coachdata(cursor)
        migrate_daily_coachdata_new(cursor)
        migrate_daily_coachdata_month(cursor)
        migrate_monthly_data(cursor)
    finally:
        cursor.close()
        conn.close()

    print('\n' + '=' * 60)
    print('이관 결과 요약')
    print('=' * 60)
    print(f'Attendance 총 건수: {Attendance.objects.count():,}')
    print(f'ChangeHistory 총 건수: {ChangeHistory.objects.count():,}')
    print(f'DailyTotalData 총 건수: {DailyTotalData.objects.count():,}')
    print(f'DailyCoachData 총 건수: {DailyCoachData.objects.count():,}')
    print(f'DailyCoachDataNew 총 건수: {DailyCoachDataNew.objects.count():,}')
    print(f'DailyCoachDataMonth 총 건수: {DailyCoachDataMonth.objects.count():,}')
    print(f'MonthlyData 총 건수: {MonthlyData.objects.count():,}')
    print('\n이관 완료!')
