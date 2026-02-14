"""
MSSQL → PostgreSQL 포인트 데이터 이관 스크립트
실행: python scripts/migrate_points.py
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
from apps.points.models import PointConfig, PointHistory
from apps.accounts.models import Member

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


def checkint(val):
    if val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def make_aware(dt):
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def migrate_point_config():
    """lf_point_set → PointConfig"""
    print('=== lf_point_set → PointConfig 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_point_set")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_point_set: {total}건')

    PointConfig.objects.all().delete()
    print('기존 PointConfig 데이터 삭제')

    cursor.execute("""
        SELECT point_seq, point_title, use_yn, app_gbn, save_gbn,
               save_point, limit_point
        FROM lf_point_set
        ORDER BY point_seq
    """)

    count = 0
    for row in cursor.fetchall():
        PointConfig.objects.create(
            point_seq=safe_str(row[0]),
            point_title=safe_str(row[1]),
            use_yn=safe_str(row[2]) or 'Y',
            app_gbn=safe_str(row[3]) or 'S',
            save_gbn=safe_str(row[4]),
            save_point=checkint(row[5]),
            limit_point=checkint(row[6]),
        )
        count += 1

    conn.close()
    print(f'PointConfig 이관 완료: {count}건')


def migrate_point_history():
    """lf_userpoint_his → PointHistory"""
    print('\n=== lf_userpoint_his → PointHistory 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_userpoint_his")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_userpoint_his: {total}건')

    PointHistory.objects.all().delete()
    print('기존 PointHistory 데이터 삭제')

    # 유효한 member_id 목록
    valid_members = set(Member.objects.values_list('username', flat=True))
    print(f'유효한 회원수: {len(valid_members)}명')

    cursor.execute("""
        SELECT his_seq, point_dt, member_id, member_name, app_gbn,
               app_point, point_desc, order_no, confirm_id,
               insert_dt, insert_id, desc_detail
        FROM lf_userpoint_his
        ORDER BY his_seq
    """)

    batch = []
    count = 0
    skip_count = 0

    for row in cursor.fetchall():
        member_id = safe_str(row[2])

        # member FK 유효성 검사
        if member_id and member_id not in valid_members:
            member_id_val = None
        else:
            member_id_val = member_id or None

        batch.append(PointHistory(
            point_dt=safe_str(row[1]),
            member_id=member_id_val,
            member_name=safe_str(row[3]),
            app_gbn=safe_str(row[4]) or 'S',
            app_point=checkint(row[5]),
            point_desc=safe_str(row[6]),
            order_no=safe_str(row[7]),
            confirm_id=safe_str(row[8]),
            insert_dt=make_aware(row[9]),
            insert_id=safe_str(row[10]),
            desc_detail=safe_str(row[11]),
        ))

        if member_id and member_id not in valid_members:
            skip_count += 1

        if len(batch) >= 100:
            PointHistory.objects.bulk_create(batch)
            count += len(batch)
            batch = []
            if count % 5000 == 0:
                print(f'  진행: {count}/{total}건')

    if batch:
        PointHistory.objects.bulk_create(batch)
        count += len(batch)

    conn.close()
    print(f'PointHistory 이관 완료: {count}건 (member 미매칭: {skip_count}건)')


if __name__ == '__main__':
    print('포인트 데이터 마이그레이션 시작\n')
    migrate_point_config()
    migrate_point_history()
    print('\n=== 최종 건수 확인 ===')
    print(f'PointConfig: {PointConfig.objects.count()}')
    print(f'PointHistory: {PointHistory.objects.count()}')
    print('\n포인트 데이터 마이그레이션 완료!')
