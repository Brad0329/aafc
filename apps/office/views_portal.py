import os
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .decorators import office_login_required, office_permission_required
from apps.board.models import Board, BoardComment, BoardFile, Popup


# ── 게시판 타입 → 한글 제목 매핑 (ASP getStrBoardTitle과 동일) ──
BOARD_TITLES = {
    'Y': '공지사항',
    'E': 'AAFC 이벤트',
    'ST': '공부하는 AAFC',
    'PR': '학부모다이어리',
    'N': 'AAFC 소식',
    'P': '포토갤러리',
    'U8': 'U-8',
    'U10': 'U-10',
    'U12': 'U-12',
}


def _get_board_title(board_id):
    return BOARD_TITLES.get(board_id, board_id)


# ══════════════════════════════════════════════════════════════════
#  팝업관리
# ══════════════════════════════════════════════════════════════════

@office_login_required
@office_permission_required('P')
def popup_list(request):
    """팝업 목록"""
    page = request.GET.get('page', 1)
    popups = Popup.objects.all().order_by('-id')
    paginator = Paginator(popups, 10)
    page_obj = paginator.get_page(page)

    # 순번 계산
    start_num = paginator.count - (page_obj.number - 1) * 10
    for i, popup in enumerate(page_obj):
        popup.row_num = start_num - i

    return render(request, 'ba_office/portal/popup_list.html', {
        'page_obj': page_obj,
        'total': paginator.count,
    })


@office_login_required
@office_permission_required('P')
def popup_write(request):
    """팝업 등록/수정"""
    popup_id = request.GET.get('popup_id') or request.POST.get('popup_id')
    popup = None
    mode = 'insert'
    mode_title = '등록'

    if popup_id:
        popup = get_object_or_404(Popup, id=popup_id)
        mode = 'mod'
        mode_title = '수정'

    if request.method == 'POST':
        pop_title = request.POST.get('pop_title', '').strip()
        start_date = request.POST.get('start_date', '').strip()
        end_date = request.POST.get('end_date', '').strip()
        pop_width = request.POST.get('pop_width', '').strip()
        pop_height = request.POST.get('pop_height', '').strip()
        pop_left = request.POST.get('pop_left', '').strip()
        pop_top = request.POST.get('pop_top', '').strip()
        pop_url = request.POST.get('pop_url', '').strip()
        rd_urltype = request.POST.get('rd_urltype', 'I')
        rd_type = request.POST.get('rd_type', 'P')
        sel_state = request.POST.get('sel_state', 'Y')

        if popup is None:
            popup = Popup()

        popup.pop_title = pop_title
        popup.pop_begin_date = start_date
        popup.pop_end_date = end_date
        popup.pop_width = pop_width
        popup.pop_height = pop_height
        popup.pop_left = pop_left
        popup.pop_top = pop_top
        popup.pop_url = pop_url
        popup.pop_urltype = rd_urltype
        popup.pop_gbn = rd_type
        popup.pop_yn = sel_state

        # 이미지 업로드
        if request.FILES.get('pop_img'):
            popup.pop_img = _save_popup_image(request.FILES['pop_img'])

        office_user = request.session.get('office_user', {})
        if mode == 'insert':
            popup.insert_id = office_user.get('login_id', '')
        popup.save()

        return HttpResponse(
            f'<script>alert("{mode_title}되었습니다.");'
            f'location.href="/ba_office/portal/popup/";</script>'
        )

    return render(request, 'ba_office/portal/popup_write.html', {
        'popup': popup,
        'mode': mode,
        'mode_title': mode_title,
    })


def _save_popup_image(f):
    """팝업 이미지 업로드 헬퍼"""
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'fcdata', 'popup')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f.name
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb+') as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    return filename


@office_login_required
@office_permission_required('P')
def popup_del(request):
    """팝업 삭제"""
    popup_id = request.GET.get('popup_id')
    if popup_id:
        Popup.objects.filter(id=popup_id).delete()
    return redirect('office_popup_list')


# ══════════════════════════════════════════════════════════════════
#  게시판관리
# ══════════════════════════════════════════════════════════════════

@office_login_required
@office_permission_required('P')
def board_list(request):
    """게시판 목록 (board 파라미터로 타입 구분)"""
    board_id = request.GET.get('board', 'Y')
    page = request.GET.get('page', 1)
    skey = request.GET.get('skey', '')
    sword = request.GET.get('sword', '')

    board_title = _get_board_title(board_id)

    # 기본 필터
    qs = Board.objects.filter(b_gbn=board_id, del_chk='N')

    # 검색 조건
    if sword:
        if skey == 'subject':
            qs = qs.filter(b_title__icontains=sword)
        elif skey == 'content':
            qs = qs.filter(b_content__icontains=sword)
        elif skey == 'writer':
            qs = qs.filter(insert_name__icontains=sword)

    # 공지글 (상단 고정)
    notices = qs.filter(b_notice_yn='Y').annotate(
        commt_cnt=Count('comments', filter=Q(comments__del_chk='N'))
    ).order_by('-insert_dt')

    # 일반글
    normal_qs = qs.filter(b_notice_yn='N').annotate(
        commt_cnt=Count('comments', filter=Q(comments__del_chk='N'))
    ).order_by('-insert_dt', '-b_ref', 'b_level')

    paginator = Paginator(normal_qs, 15)
    page_obj = paginator.get_page(page)

    # 순번 계산
    start_num = paginator.count - (page_obj.number - 1) * 15
    for i, board in enumerate(page_obj):
        board.row_num = start_num - i
        board.is_new = _is_new(board.insert_dt)
        board.is_reply = board.b_level > 0

    # 공지글에도 속성 추가
    for notice in notices:
        notice.is_new = _is_new(notice.insert_dt)

    return render(request, 'ba_office/portal/board_list.html', {
        'board_id': board_id,
        'board_title': board_title,
        'notices': notices,
        'page_obj': page_obj,
        'total': paginator.count,
        'skey': skey,
        'sword': sword,
    })


def _is_new(insert_dt_str):
    """insert_dt 문자열이 오늘이면 True"""
    if not insert_dt_str:
        return False
    try:
        dt = datetime.strptime(str(insert_dt_str)[:10], '%Y-%m-%d')
        return (date.today() - dt.date()).days < 1
    except (ValueError, TypeError):
        return False


@office_login_required
@office_permission_required('P')
def board_content(request):
    """게시글 상세"""
    board_id = request.GET.get('board', '')
    seq = request.GET.get('seq')
    page = request.GET.get('page', 1)

    if not board_id or not seq:
        return HttpResponse('<script>alert("필수정보가 부족합니다.");history.back();</script>')

    board = get_object_or_404(Board, b_gbn=board_id, b_seq=int(seq))
    board_title = _get_board_title(board_id)

    # 첨부파일
    files = BoardFile.objects.filter(board=board)
    file_images = [f for f in files if f.bs_img]
    file_pdfs = [f for f in files if f.bs_file]

    # 댓글
    comments = BoardComment.objects.filter(board=board, del_chk='N').order_by('-insert_dt')

    # 이전/다음 글
    prev_post = Board.objects.filter(
        b_gbn=board_id, b_notice_yn='N', b_seq__lt=int(seq)
    ).order_by('-b_seq').first()
    next_post = Board.objects.filter(
        b_gbn=board_id, b_notice_yn='N', b_seq__gt=int(seq)
    ).order_by('b_seq').first()

    return render(request, 'ba_office/portal/board_content.html', {
        'board_id': board_id,
        'board_title': board_title,
        'board': board,
        'file_images': file_images,
        'file_pdfs': file_pdfs,
        'comments': comments,
        'prev_post': prev_post,
        'next_post': next_post,
        'page': page,
    })


@office_login_required
@office_permission_required('P')
def board_write(request):
    """게시글 등록/수정"""
    board_id = request.GET.get('board') or request.POST.get('board', '')
    seq = request.GET.get('seq') or request.POST.get('seq', '')
    page = request.GET.get('page', 1)

    if not board_id:
        return HttpResponse('<script>alert("필수정보가 부족합니다.");history.back();</script>')

    board_title = _get_board_title(board_id)
    office_user = request.session.get('office_user', {})

    mode = 'add'
    mode_title = '등록'
    board = None
    existing_files = []

    if seq:
        try:
            board = Board.objects.get(b_gbn=board_id, b_seq=int(seq))
            mode = 'edit'
            mode_title = '수정'
            existing_files = BoardFile.objects.filter(board=board)
        except Board.DoesNotExist:
            pass

    if request.method == 'POST':
        b_title = request.POST.get('b_title', '').strip()
        b_content = request.POST.get('b_content', '')
        b_writer = request.POST.get('b_writer', '').strip()
        b_regdate = request.POST.get('b_regdate', '').strip()
        sel_b_gbn = request.POST.get('sel_b_gbn', board_id)
        sel_notice_yn = request.POST.get('sel_notice_yn', 'N')
        post_mode = request.POST.get('mode', 'add')

        if post_mode == 'add':
            # 새 b_seq 채번
            max_seq = Board.objects.all().order_by('-b_seq').values_list('b_seq', flat=True).first() or 0
            new_seq = max_seq + 1
            # b_ref 채번
            max_ref = Board.objects.filter(b_gbn=sel_b_gbn).order_by('-b_ref').values_list('b_ref', flat=True).first() or 0
            new_ref = max_ref + 1

            board = Board.objects.create(
                b_seq=new_seq,
                b_ref=new_ref,
                b_level=0,
                b_step=0,
                b_gbn=sel_b_gbn,
                b_notice_yn=sel_notice_yn,
                b_title=b_title,
                b_content=b_content,
                b_hit=0,
                b_commend=0,
                insert_name=b_writer,
                insert_id=office_user.get('login_id', ''),
                insert_type='A',
                insert_dt=b_regdate or date.today().strftime('%Y-%m-%d'),
                insert_ip=request.META.get('REMOTE_ADDR', ''),
                del_chk='N',
            )

            # 이미지/첨부 업로드
            _save_board_files(request, board)

        elif post_mode == 'edit' and board:
            board.b_title = b_title
            board.b_content = b_content
            board.insert_dt = b_regdate or board.insert_dt
            board.insert_name = b_writer
            board.b_gbn = sel_b_gbn
            board.b_notice_yn = sel_notice_yn
            board.save()

            # 기존 파일 삭제 처리
            _handle_file_deletions(request, board)
            # 새 파일 업로드
            _save_board_files(request, board)

        return HttpResponse(
            f'<script>alert("{mode_title}되었습니다.");'
            f'location.href="/ba_office/portal/board/?board={sel_b_gbn}";</script>'
        )

    return render(request, 'ba_office/portal/board_write.html', {
        'board_id': board_id,
        'board_title': board_title,
        'board': board,
        'mode': mode,
        'mode_title': mode_title,
        'existing_files': existing_files,
        'page': page,
        'writer_name': board.insert_name if board else office_user.get('office_name', ''),
        'cur_date': board.insert_dt if board else date.today().strftime('%Y-%m-%d'),
    })


def _save_board_files(request, board):
    """게시글 첨부파일 저장"""
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'fcdata', 'board')
    os.makedirs(upload_dir, exist_ok=True)
    office_user = request.session.get('office_user', {})

    for i in range(1, 6):
        img_file = request.FILES.get(f'attachImg{i}')
        pds_file = request.FILES.get(f'attachPds{i}')

        if img_file or pds_file:
            bs_img_name = ''
            bs_file_name = ''

            if img_file:
                bs_img_name = f"{board.b_gbn}_img_{board.b_seq}_{i}_{img_file.name}"
                filepath = os.path.join(upload_dir, bs_img_name)
                with open(filepath, 'wb+') as dest:
                    for chunk in img_file.chunks():
                        dest.write(chunk)

            if pds_file:
                bs_file_name = f"{board.b_gbn}_pds_{pds_file.name}"
                filepath = os.path.join(upload_dir, bs_file_name)
                with open(filepath, 'wb+') as dest:
                    for chunk in pds_file.chunks():
                        dest.write(chunk)

            BoardFile.objects.create(
                board=board,
                bs_img=bs_img_name,
                bs_file=bs_file_name,
                bs_downcnt=0,
                bs_no=i,
                insert_dt=timezone.now(),
                insert_id=office_user.get('login_id', ''),
            )


def _handle_file_deletions(request, board):
    """첨부파일 삭제 체크 처리"""
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'fcdata', 'board')
    for i in range(1, 6):
        if request.POST.get(f'isDelAttachImg{i}') == 'T':
            org_name = request.POST.get(f'orgAttachImg{i}', '')
            if org_name:
                filepath = os.path.join(upload_dir, org_name)
                if os.path.exists(filepath):
                    os.remove(filepath)
                BoardFile.objects.filter(board=board, bs_img=org_name).delete()

        if request.POST.get(f'isDelAttachPds{i}') == 'T':
            org_name = request.POST.get(f'orgAttachPds{i}', '')
            if org_name:
                filepath = os.path.join(upload_dir, org_name)
                if os.path.exists(filepath):
                    os.remove(filepath)
                BoardFile.objects.filter(board=board, bs_file=org_name).delete()


@office_login_required
@office_permission_required('P')
def board_reply(request):
    """게시글 답변"""
    board_id = request.GET.get('board') or request.POST.get('board', '')
    seq = request.GET.get('seq') or request.POST.get('seq', '')
    page = request.GET.get('page', 1)

    if not board_id or not seq:
        return HttpResponse('<script>alert("필수정보가 부족합니다.");history.back();</script>')

    board_title = _get_board_title(board_id)
    office_user = request.session.get('office_user', {})
    parent = get_object_or_404(Board, b_gbn=board_id, b_seq=int(seq))

    if request.method == 'POST':
        b_title = request.POST.get('b_title', '').strip()
        b_content = request.POST.get('b_content', '')
        b_writer = request.POST.get('b_writer', '').strip()
        b_regdate = request.POST.get('b_regdate', '').strip()
        sel_notice_yn = request.POST.get('sel_notice_yn', 'N')

        # 새 b_seq 채번
        max_seq = Board.objects.all().order_by('-b_seq').values_list('b_seq', flat=True).first() or 0
        new_seq = max_seq + 1

        Board.objects.create(
            b_seq=new_seq,
            b_ref=parent.b_ref,
            b_level=parent.b_level + 1,
            b_step=parent.b_step + 1,
            b_gbn=board_id,
            b_notice_yn=sel_notice_yn,
            b_title=b_title,
            b_content=b_content,
            b_hit=0,
            b_commend=0,
            insert_name=b_writer,
            insert_id=office_user.get('login_id', ''),
            insert_type='A',
            insert_dt=b_regdate or date.today().strftime('%Y-%m-%d'),
            insert_ip=request.META.get('REMOTE_ADDR', ''),
            del_chk='N',
        )

        return HttpResponse(
            f'<script>alert("답변등록되었습니다.");'
            f'location.href="/ba_office/portal/board/?board={board_id}";</script>'
        )

    return render(request, 'ba_office/portal/board_reply.html', {
        'board_id': board_id,
        'board_title': board_title,
        'parent': parent,
        'page': page,
        'writer_name': office_user.get('office_name', ''),
        'cur_date': date.today().strftime('%Y-%m-%d'),
    })


@office_login_required
@office_permission_required('P')
def board_del(request):
    """게시글 삭제 (소프트 삭제)"""
    board_id = request.GET.get('board', '')
    seq = request.GET.get('seq')

    if not board_id or not seq:
        return HttpResponse('<script>alert("필수정보가 부족합니다.");history.back();</script>')

    Board.objects.filter(b_seq=int(seq)).update(del_chk='Y')

    return HttpResponse(
        f'<script>alert("삭제되었습니다.");'
        f'location.href="/ba_office/portal/board/?board={board_id}";</script>'
    )


@office_login_required
@office_permission_required('P')
def board_comment_add(request):
    """댓글 등록"""
    if request.method != 'POST':
        return HttpResponse('<script>alert("잘못된 접근입니다.");history.back();</script>')

    board_id = request.POST.get('board', '')
    seq = request.POST.get('seq', '')
    comment_name = request.POST.get('comment_name', '').strip()
    comment_content = request.POST.get('comment_content', '').strip()
    office_user = request.session.get('office_user', {})

    if not board_id or not seq or not comment_content:
        return HttpResponse('<script>alert("필수정보가 부족합니다.");history.back();</script>')

    board = get_object_or_404(Board, b_seq=int(seq))

    BoardComment.objects.create(
        board=board,
        b_gbn=board_id,
        comment=comment_content,
        insert_name=comment_name,
        insert_id=office_user.get('login_id', ''),
        insert_type='A',
        insert_dt=timezone.now(),
        insert_ip=request.META.get('REMOTE_ADDR', ''),
        del_chk='N',
    )

    return HttpResponse(
        f'<script>alert("등록되었습니다.");'
        f'location.href="/ba_office/portal/board/content/?board={board_id}&seq={seq}";</script>'
    )


@office_login_required
@office_permission_required('P')
def board_comment_del(request):
    """댓글 삭제 (소프트 삭제)"""
    board_id = request.GET.get('board', '')
    c_seq = request.GET.get('c_seq')
    seq = request.GET.get('seq', '')

    if not board_id or not c_seq or not seq:
        return HttpResponse('<script>alert("필수정보가 부족합니다.");history.back();</script>')

    BoardComment.objects.filter(id=int(c_seq)).update(del_chk='Y')

    return HttpResponse(
        f'<script>alert("삭제하였습니다.");'
        f'location.href="/ba_office/portal/board/content/?board={board_id}&seq={seq}";</script>'
    )
