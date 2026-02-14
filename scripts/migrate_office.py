"""
MSSQL → PostgreSQL 관리자 사용자 데이터 이관 스크립트
실행: python scripts/migrate_office.py
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
from apps.office.models import OfficeUser, OfficeLoginHistory

MSSQL_CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=2018_junior;'
    'UID=juni_db;'
    'PWD=juniordb1234'
)


def safe_str(val):
    """MSSQL 필드값을 안전한 문자열로 변환"""
    if val is None:
        return ''
    return str(val).strip()


def migrate_officeuser(cursor):
    """lf_officeuser → OfficeUser"""
    cursor.execute('''
        SELECT office_code, office_name, office_id, office_pwd,
               office_part, office_mail, office_hp,
               office_auth, use_auth, coach_code, del_chk, insert_dt,
               office_realname
        FROM lf_officeuser
        ORDER BY office_code
    ''')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        OfficeUser.objects.update_or_create(
            office_code=int(row[0]) if row[0] else None,
            defaults={
                'office_name': safe_str(row[1]),
                'office_id': safe_str(row[2]),
                'office_pwd': safe_str(row[3]),
                'office_part': safe_str(row[4]),
                'office_mail': safe_str(row[5]),
                'office_hp': safe_str(row[6]),
                'power_level': safe_str(row[7]),
                'use_auth': safe_str(row[8]) or 'W',
                'coach_code': safe_str(row[9]),
                'del_chk': safe_str(row[10]) or 'N',
                'insert_dt': row[11],
                'office_realname': safe_str(row[12]) if len(row) > 12 else '',
            }
        )
        count += 1
    print(f'OfficeUser: {count}건 이관 완료')


def migrate_login_history(cursor):
    """lf_officeuser_log → OfficeLoginHistory"""
    try:
        cursor.execute('''
            SELECT office_id, login_dt, login_ip
            FROM lf_officeuser_log
            ORDER BY login_dt DESC
        ''')
        rows = cursor.fetchall()
        count = 0
        batch = []
        for row in rows:
            batch.append(OfficeLoginHistory(
                office_id=safe_str(row[0]),
                login_dt=row[1],
                login_ip=safe_str(row[2]),
            ))
            count += 1
            if len(batch) >= 5000:
                OfficeLoginHistory.objects.bulk_create(batch, batch_size=5000)
                batch = []
        if batch:
            OfficeLoginHistory.objects.bulk_create(batch, batch_size=5000)
        print(f'OfficeLoginHistory: {count}건 이관 완료')
    except pyodbc.ProgrammingError as e:
        print(f'OfficeLoginHistory: 테이블이 없거나 오류 - {e}')


def main():
    print('=== 관리자 데이터 마이그레이션 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    migrate_officeuser(cursor)
    migrate_login_history(cursor)

    cursor.close()
    conn.close()
    print('=== 관리자 데이터 마이그레이션 완료 ===')

    # 결과 확인
    print(f'\n--- PostgreSQL 결과 ---')
    print(f'OfficeUser: {OfficeUser.objects.count()}건')
    print(f'OfficeLoginHistory: {OfficeLoginHistory.objects.count()}건')

    # 관리자 목록 출력
    print(f'\n--- 관리자 목록 ---')
    for u in OfficeUser.objects.filter(del_chk='N'):
        print(f'  {u.office_id} ({u.office_name}) - 권한: {u.power_level}')


if __name__ == '__main__':
    main()
