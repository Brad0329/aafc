"""
MSSQL → PostgreSQL 상담 데이터 이관 스크립트
실행: python scripts/migrate_consult.py
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
from apps.consult.models import Consult, ConsultAnswer, ConsultFree, ConsultRegion

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
        return int(val)
    except (ValueError, TypeError):
        return 0


def make_aware(dt):
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def migrate_consult():
    """lf_consult → Consult"""
    print('=== lf_consult → Consult 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_consult")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_consult: {total}건')

    Consult.objects.all().delete()
    print('기존 Consult 데이터 삭제')

    cursor.execute("""
        SELECT con_seq, member_id, member_name, child_id, child_name,
               consult_name, consult_tel, consult_gbn, consult_title, consult_content,
               consult_pwd, del_chk, consult_dt, manage_id,
               local_code, sta_code, stu_name, stu_sex, stu_age,
               path_code, line_code, company_name, com_employee_no
        FROM lf_consult
        ORDER BY con_seq
    """)

    # con_seq → Django id 매핑 (ConsultAnswer에서 사용)
    seq_id_map = {}
    count = 0
    for row in cursor.fetchall():
        obj = Consult.objects.create(
            member_id=safe_str(row[1]),
            member_name=safe_str(row[2]),
            child_id=safe_str(row[3]),
            child_name=safe_str(row[4]),
            consult_name=safe_str(row[5]),
            consult_tel=safe_str(row[6]),
            consult_gbn=safe_str(row[7]),
            consult_title=safe_str(row[8]),
            consult_content=safe_str(row[9]),
            consult_pwd=safe_str(row[10]),
            del_chk=safe_str(row[11]) or 'N',
            consult_dt=make_aware(row[12]) if row[12] else None,
            manage_id=safe_str(row[13]),
            local_code=safe_str(row[14]),
            sta_code=safe_str(row[15]),
            stu_name=safe_str(row[16]),
            stu_sex=safe_str(row[17]),
            stu_age=checkint(row[18]),
            path_code=checkint(row[19]),
            line_code=checkint(row[20]),
            company_name=safe_str(row[21]),
            com_employee_no=safe_str(row[22]),
        )
        seq_id_map[checkint(row[0])] = obj
        count += 1
        if count % 500 == 0:
            print(f'  {count}건 처리중...')

    conn.close()
    pg_count = Consult.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return seq_id_map


def migrate_consult_answer(seq_id_map):
    """lf_con_answer → ConsultAnswer"""
    print('\n=== lf_con_answer → ConsultAnswer 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_con_answer")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_con_answer: {total}건')

    ConsultAnswer.objects.all().delete()
    print('기존 ConsultAnswer 데이터 삭제')

    cursor.execute("""
        SELECT con_seq, con_fo_seq, consult_category, consult_answer,
               con_answer_dt, coach_code, stat_code, receive_code, cus_stat_code
        FROM lf_con_answer
        ORDER BY con_seq
    """)

    count = 0
    skip = 0
    for row in cursor.fetchall():
        con_fo_seq = checkint(row[1])
        consult = seq_id_map.get(con_fo_seq)
        if not consult:
            skip += 1
            continue

        ConsultAnswer.objects.create(
            consult=consult,
            consult_category=checkint(row[2]),
            consult_answer=safe_str(row[3]),
            con_answer_dt=make_aware(row[4]) if row[4] else None,
            coach_code=checkint(row[5]),
            stat_code=checkint(row[6]),
            receive_code=checkint(row[7]),
            cus_stat_code=checkint(row[8]),
        )
        count += 1
        if count % 500 == 0:
            print(f'  {count}건 처리중...')

    conn.close()
    pg_count = ConsultAnswer.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return pg_count


def migrate_consult_free():
    """lf_consult_free → ConsultFree"""
    print('\n=== lf_consult_free → ConsultFree 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_consult_free")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_consult_free: {total}건')

    ConsultFree.objects.all().delete()
    print('기존 ConsultFree 데이터 삭제')

    cursor.execute("""
        SELECT no_seq, jname, jphone1, jphone2, jphone3, jlocal, j_date,
               confirm_memo, confirm_yn, del_chk, confirm_id, confirm_name,
               confirm_date, consult_gbn
        FROM lf_consult_free
        ORDER BY no_seq
    """)

    count = 0
    for row in cursor.fetchall():
        ConsultFree.objects.create(
            jname=safe_str(row[1]),
            jphone1=safe_str(row[2]),
            jphone2=safe_str(row[3]),
            jphone3=safe_str(row[4]),
            jlocal=safe_str(row[5]),
            j_date=make_aware(row[6]) if row[6] else None,
            confirm_memo=safe_str(row[7]),
            confirm_yn=safe_str(row[8]) or 'N',
            del_chk=safe_str(row[9]) or 'N',
            confirm_id=safe_str(row[10]),
            confirm_name=safe_str(row[11]),
            confirm_date=make_aware(row[12]) if row[12] else None,
            consult_gbn=safe_str(row[13]),
        )
        count += 1

    conn.close()
    pg_count = ConsultFree.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return pg_count


def migrate_consult_region():
    """lf_consult_uplocal → ConsultRegion"""
    print('\n=== lf_consult_uplocal → ConsultRegion 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_consult_uplocal")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_consult_uplocal: {total}건')

    ConsultRegion.objects.all().delete()
    print('기존 ConsultRegion 데이터 삭제')

    cursor.execute("""
        SELECT no_seq, reg_gbn, reg_name, del_chk, mphone
        FROM lf_consult_uplocal
        ORDER BY no_seq
    """)

    count = 0
    for row in cursor.fetchall():
        ConsultRegion.objects.create(
            reg_gbn=safe_str(row[1]) or 'L',
            reg_name=safe_str(row[2]),
            del_chk=safe_str(row[3]) or 'N',
            mphone=safe_str(row[4]),
        )
        count += 1

    conn.close()
    pg_count = ConsultRegion.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return pg_count


if __name__ == '__main__':
    print('상담 데이터 마이그레이션 시작\n')
    migrate_consult_region()
    migrate_consult_free()
    seq_id_map = migrate_consult()
    migrate_consult_answer(seq_id_map)
    print('\n상담 데이터 마이그레이션 완료!')
