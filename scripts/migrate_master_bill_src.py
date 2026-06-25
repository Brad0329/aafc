"""
MSSQL → PostgreSQL 변경원본 스냅샷 이관 (변경이력 '변경 전' 데이터)
  lf_fcjoin_master_src → EnrollmentSrc
  lf_fcjoin_bill_src   → EnrollmentBillSrc
실행: python scripts/migrate_master_bill_src.py
(course_src 는 migrate_course_src.py 로 별도 이관)
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
from apps.enrollment.models import EnrollmentSrc, EnrollmentBillSrc

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def safe_str(val):
    return '' if val is None else str(val).strip()


def safe_int(val):
    if val is None:
        return 0
    try:
        return int(str(val).strip() or 0)
    except (ValueError, TypeError):
        return 0


def migrate_master_src(cursor):
    cursor.execute("SELECT COUNT(*) FROM lf_fcjoin_master_src")
    total = cursor.fetchone()[0]
    deleted = EnrollmentSrc.objects.all().delete()[0]
    print(f"[master_src] MSSQL {total}건 / 기존 삭제 {deleted}건")

    cursor.execute("""
        SELECT src_seq, no_seq, member_id, child_id, pay_stats, pay_method, pay_price,
               lecture_stats, lec_cycle, lec_period, start_dt, end_dt, apply_gubun,
               cancel_code, cancel_desc, del_chk, insert_id, insert_dt
        FROM lf_fcjoin_master_src ORDER BY src_seq
    """)
    batch, count = [], 0
    for r in cursor.fetchall():
        batch.append(EnrollmentSrc(
            src_seq=r[0], no_seq=r[1] or 0,
            member_id=safe_str(r[2]), child_id=safe_str(r[3]),
            pay_stats=safe_str(r[4]), pay_method=safe_str(r[5]), pay_price=r[6] or 0,
            lecture_stats=safe_str(r[7]), lec_cycle=safe_int(r[8]), lec_period=safe_int(r[9]),
            start_dt=safe_str(r[10]), end_dt=safe_str(r[11]), apply_gubun=safe_str(r[12]),
            cancel_code=safe_str(r[13]), cancel_desc=safe_str(r[14]), del_chk=safe_str(r[15]) or 'N',
            insert_id=safe_str(r[16]), insert_dt=r[17],
        ))
        if len(batch) >= 1000:
            EnrollmentSrc.objects.bulk_create(batch, batch_size=1000)
            count += len(batch); batch = []
    if batch:
        EnrollmentSrc.objects.bulk_create(batch, batch_size=1000)
        count += len(batch)
    print(f"[master_src] 이관 완료: {count}건")


def migrate_bill_src(cursor):
    cursor.execute("SELECT COUNT(*) FROM lf_fcjoin_bill_src")
    total = cursor.fetchone()[0]
    deleted = EnrollmentBillSrc.objects.all().delete()[0]
    print(f"[bill_src] MSSQL {total}건 / 기존 삭제 {deleted}건")

    cursor.execute("""
        SELECT src_seq, no_seq, pknum, bill_code, bill_desc, bill_amt, pay_stats, insert_id, insert_dt
        FROM lf_fcjoin_bill_src ORDER BY src_pknum
    """)
    batch, count = [], 0
    for r in cursor.fetchall():
        batch.append(EnrollmentBillSrc(
            src_seq=r[0] or 0, no_seq=r[1] or 0, pknum=r[2] or 0,
            bill_code=safe_str(r[3]), bill_desc=safe_str(r[4]), bill_amt=r[5] or 0,
            pay_stats=safe_str(r[6]), insert_id=safe_str(r[7]), insert_dt=r[8],
        ))
        if len(batch) >= 1000:
            EnrollmentBillSrc.objects.bulk_create(batch, batch_size=1000)
            count += len(batch); batch = []
    if batch:
        EnrollmentBillSrc.objects.bulk_create(batch, batch_size=1000)
        count += len(batch)
    print(f"[bill_src] 이관 완료: {count}건")


def migrate():
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()
    migrate_master_src(cursor)
    migrate_bill_src(cursor)
    conn.close()


if __name__ == '__main__':
    migrate()
