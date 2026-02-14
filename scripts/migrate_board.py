"""
MSSQL → PostgreSQL 게시판 데이터 이관 스크립트
실행: python scripts/migrate_board.py
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
from apps.board.models import Board, BoardComment, BoardFile

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


def migrate_board():
    """lf_board → Board"""
    print('=== lf_board → Board 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_board")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_board: {total}건')

    Board.objects.all().delete()
    print('기존 Board 데이터 삭제')

    cursor.execute("""
        SELECT b_seq, b_ref, b_level, b_step, b_gbn, b_notice_yn,
               b_title, b_content, b_hit, b_commend,
               insert_name, insert_id, insert_type, insert_dt, insert_ip, del_chk
        FROM lf_board
        ORDER BY b_seq
    """)

    count = 0
    batch = []
    for row in cursor.fetchall():
        batch.append(Board(
            b_seq=checkint(row[0]),
            b_ref=checkint(row[1]),
            b_level=checkint(row[2]),
            b_step=checkint(row[3]),
            b_gbn=safe_str(row[4]),
            b_notice_yn=safe_str(row[5]) or 'N',
            b_title=safe_str(row[6]),
            b_content=safe_str(row[7]),
            b_hit=checkint(row[8]),
            b_commend=checkint(row[9]),
            insert_name=safe_str(row[10]),
            insert_id=safe_str(row[11]),
            insert_type=safe_str(row[12]),
            insert_dt=safe_str(row[13]),
            insert_ip=safe_str(row[14]),
            del_chk=safe_str(row[15]) or 'N',
        ))
        count += 1
        if len(batch) >= 100:
            Board.objects.bulk_create(batch)
            batch = []
            print(f'  {count}건 처리중...')

    if batch:
        Board.objects.bulk_create(batch)

    conn.close()
    pg_count = Board.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건')
    return pg_count


def migrate_boardcomment():
    """lf_boardcomment → BoardComment"""
    print('\n=== lf_boardcomment → BoardComment 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_boardcomment")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_boardcomment: {total}건')

    BoardComment.objects.all().delete()
    print('기존 BoardComment 데이터 삭제')

    # b_seq → Board 매핑
    board_map = {b.b_seq: b for b in Board.objects.all()}

    cursor.execute("""
        SELECT bc_seq, b_seq, b_gbn, comment,
               insert_name, insert_id, insert_type, insert_dt, insert_ip, del_chk
        FROM lf_boardcomment
        ORDER BY bc_seq
    """)

    count = 0
    skip = 0
    for row in cursor.fetchall():
        b_seq = checkint(row[1])
        board = board_map.get(b_seq)
        if not board:
            skip += 1
            continue

        BoardComment.objects.create(
            board=board,
            b_gbn=safe_str(row[2]),
            comment=safe_str(row[3]),
            insert_name=safe_str(row[4]),
            insert_id=safe_str(row[5]),
            insert_type=safe_str(row[6]),
            insert_dt=make_aware(row[7]) if row[7] else None,
            insert_ip=safe_str(row[8]),
            del_chk=safe_str(row[9]) or 'N',
        )
        count += 1

    conn.close()
    pg_count = BoardComment.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return pg_count


def migrate_boardfile():
    """lf_boardsub → BoardFile"""
    print('\n=== lf_boardsub → BoardFile 이관 시작 ===')
    conn = pyodbc.connect(MSSQL_CONN_STR)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM lf_boardsub")
    total = cursor.fetchone()[0]
    print(f'MSSQL lf_boardsub: {total}건')

    BoardFile.objects.all().delete()
    print('기존 BoardFile 데이터 삭제')

    board_map = {b.b_seq: b for b in Board.objects.all()}

    cursor.execute("""
        SELECT bs_seq, b_seq, bs_img, bs_thumimg, bs_file, bs_downcnt, bs_no,
               insert_dt, insert_id,
               daum_uploadhost, daum_vid, daum_thimg, daum_width, daum_height
        FROM lf_boardsub
        ORDER BY bs_seq
    """)

    count = 0
    skip = 0
    for row in cursor.fetchall():
        b_seq = checkint(row[1])
        board = board_map.get(b_seq)
        if not board:
            skip += 1
            continue

        BoardFile.objects.create(
            board=board,
            bs_img=safe_str(row[2]),
            bs_thumimg=safe_str(row[3]),
            bs_file=safe_str(row[4]),
            bs_downcnt=checkint(row[5]),
            bs_no=checkint(row[6]),
            insert_dt=make_aware(row[7]) if row[7] else None,
            insert_id=safe_str(row[8]),
            daum_uploadhost=safe_str(row[9]),
            daum_vid=safe_str(row[10]),
            daum_thimg=safe_str(row[11]),
            daum_width=safe_str(row[12]),
            daum_height=safe_str(row[13]),
        )
        count += 1

    conn.close()
    pg_count = BoardFile.objects.count()
    print(f'완료: MSSQL {total}건 → PostgreSQL {pg_count}건 (스킵: {skip}건)')
    return pg_count


if __name__ == '__main__':
    print('게시판 데이터 마이그레이션 시작\n')
    migrate_board()
    migrate_boardcomment()
    migrate_boardfile()
    print('\n게시판 데이터 마이그레이션 완료!')
