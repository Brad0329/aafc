"""게시판 b_content/b_title ASP escape 디코드 (일회성, 이미 이관된 데이터 정규화).

원본 ASP는 저장 시 ReplaceTagText로 escape → 출력 시 text2Tag(decQuote())로 디코드.
이관 데이터는 escape 상태로 들어와 Django |safe 출력 시 태그가 글자로 보임.
→ 한 번 디코드해 정상 HTML로 보관.

★주의: 한 번만 실행. 재실행 시 과디코드 가능(변화 있을 때만 저장하므로 대체로 안전하나 권장 안 함).
로컬:  python scripts/decode_board.py
RDS:   DJANGO_SETTINGS_MODULE=config.settings.prod python scripts/decode_board.py
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

from apps.board.models import Board


def asp_decode(s):
    """ASP text2Tag(decQuote()) 동일."""
    if not s:
        return s
    s = s.replace('&#39;', "'").replace('&quot;', '"')
    s = s.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    s = s.replace('&nbsp;', ' ')
    return s


def main():
    total = Board.objects.count()
    cnt = 0
    for b in Board.objects.all().iterator():
        nc = asp_decode(b.b_content or '')
        nt = asp_decode(b.b_title or '')
        if nc != (b.b_content or '') or nt != (b.b_title or ''):
            b.b_content = nc
            b.b_title = nt
            b.save(update_fields=['b_content', 'b_title'])
            cnt += 1
    print(f'[{os.environ.get("DJANGO_SETTINGS_MODULE")}] 디코드 적용: {cnt}건 / 전체 {total}건')


if __name__ == '__main__':
    main()
