"""
MSSQL → PostgreSQL lf_fcjoin_course_src 데이터 이관 스크립트
실행: python scripts/migrate_course_src.py
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
from apps.enrollment.models import EnrollmentCourseSrc

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def safe_str(val):
    if val is None:
        return ''
    return str(val).strip()


def safe_date(val):
    if val is None:
        return None
    return val.date() if hasattr(val, 'date') else val


def migrate():
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_fcjoin_course_src")
    total = cursor.fetchone()[0]
    print(f"MSSQL lf_fcjoin_course_src: {total}건")

    # 기존 데이터 삭제
    deleted = EnrollmentCourseSrc.objects.all().delete()[0]
    print(f"PostgreSQL 기존 데이터 삭제: {deleted}건")

    cursor.execute("""
        SELECT src_pknum, src_seq, pknum, no_seq, bill_code,
               course_ym, course_ym_amt, lecture_code, start_ymd,
               course_stats, ch_name
        FROM lf_fcjoin_course_src
        ORDER BY src_pknum
    """)

    batch = []
    count = 0
    for row in cursor.fetchall():
        batch.append(EnrollmentCourseSrc(
            src_seq=row[1] or 0,
            pknum=row[2] or 0,
            no_seq=row[3] or 0,
            bill_code=safe_str(row[4]),
            course_ym=safe_date(row[5]),
            course_ym_amt=row[6] or 0,
            lecture_code=row[7] or 0,
            start_ymd=safe_date(row[8]),
            course_stats=safe_str(row[9]),
            ch_name=safe_str(row[10]),
        ))
        if len(batch) >= 1000:
            EnrollmentCourseSrc.objects.bulk_create(batch, batch_size=1000)
            count += len(batch)
            print(f"  {count}/{total} 이관 완료")
            batch = []

    if batch:
        EnrollmentCourseSrc.objects.bulk_create(batch, batch_size=1000)
        count += len(batch)

    conn.close()
    print(f"이관 완료: {count}건")


if __name__ == '__main__':
    migrate()
