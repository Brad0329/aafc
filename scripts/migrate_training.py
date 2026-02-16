"""
MSSQL → PostgreSQL 훈련일정(LectureTraining) 데이터 이관 스크립트
실행: python scripts/migrate_training.py
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
from apps.courses.models import LectureTraining

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def safe_str(val):
    """MSSQL 필드값을 안전하게 문자열로 변환"""
    if val is None:
        return ''
    return str(val).strip()


def safe_int(val, default=0):
    """MSSQL 필드값을 안전하게 정수로 변환"""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def migrate_lecture_training():
    """lf_lectraining → LectureTraining 이관"""
    print("=" * 60)
    print("훈련일정(LectureTraining) 이관 시작")
    print("=" * 60)

    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    sql = """
        SELECT no_seq, sta_code, local_code, training_dt,
               training_desc, insert_dt, insert_id
        FROM lf_lectraining
        ORDER BY no_seq
    """
    cursor.execute(sql)
    columns = [col[0] for col in cursor.description]
    print(f"MSSQL 컬럼: {columns}")

    # 기존 데이터 삭제
    deleted = LectureTraining.objects.all().delete()
    print(f"기존 Django 데이터 삭제: {deleted}")

    batch = []
    total = 0

    while True:
        rows = cursor.fetchmany(5000)
        if not rows:
            break
        for row in rows:
            data = dict(zip(columns, row))
            obj = LectureTraining(
                id=safe_int(data.get('no_seq')),
                sta_code=safe_int(data.get('sta_code')),
                local_code=safe_int(data.get('local_code')),
                training_dt=data.get('training_dt'),
                training_desc=safe_str(data.get('training_desc')),
                insert_dt=data.get('insert_dt'),
                insert_id=safe_str(data.get('insert_id')),
            )
            batch.append(obj)

        if batch:
            LectureTraining.objects.bulk_create(batch, batch_size=5000)
            total += len(batch)
            print(f"  {total}건 처리됨")
            batch = []

    # ID 시퀀스 리셋
    from django.db import connection as pg_conn
    with pg_conn.cursor() as pg_cursor:
        pg_cursor.execute(
            "SELECT setval(pg_get_serial_sequence('courses_lecturetraining', 'id'), "
            "COALESCE((SELECT MAX(id) FROM courses_lecturetraining), 1))"
        )

    cursor.close()
    conn.close()
    print(f"\n총 {total}건 이관 완료")


if __name__ == '__main__':
    migrate_lecture_training()
