import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.http import Http404
from django.utils import timezone

from .models import Board, BoardComment, BoardFile

# 게시판 타입별 설정
BOARD_CONFIG = {
    'Y':  {'title': '공지사항', 'sub_top': 'community', 'user_write': False, 'menu_group': 'community'},
    'N':  {'title': '공지사항', 'sub_top': 'community', 'user_write': False, 'menu_group': 'community'},
    'E':  {'title': '공지사항', 'sub_top': 'community', 'user_write': False, 'menu_group': 'community'},
    'P':  {'title': '포토갤러리', 'sub_top': 'community', 'user_write': True, 'menu_group': 'community'},
    'PR': {'title': '학부모 다이어리', 'sub_top': 'community', 'user_write': True, 'menu_group': 'community'},
    'ST': {'title': '공부하는 AAFC', 'sub_top': 'community', 'user_write': False, 'menu_group': 'community'},
    'U8': {'title': 'U-8', 'sub_top': 'academy', 'user_write': False, 'menu_group': 'academy'},
    'U10': {'title': 'U-10', 'sub_top': 'academy', 'user_write': False, 'menu_group': 'academy'},
    'U12': {'title': 'U-12', 'sub_top': 'academy', 'user_write': False, 'menu_group': 'academy'},
}

# 커뮤니티 서브메뉴
COMMUNITY_MENU = [
    {'id': 'Y', 'title': '공지사항'},
    {'id': 'PR', 'title': '학부모 다이어리'},
    {'id': 'P', 'title': '포토갤러리'},
    {'id': 'ST', 'title': '공부하는 AAFC'},
]


def _extract_first_image(html_content):
    """HTML 본문에서 첫 번째 이미지 URL 추출"""
    if not html_content:
        return ''
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    if match:
        return match.group(1)
    return ''


def board_list(request, board_id):
    """게시판 목록"""
    config = BOARD_CONFIG.get(board_id)
    if not config:
        raise Http404

    # U8/U10/U12는 단일 뷰 페이지로 리다이렉트
    if board_id in ('U8', 'U10', 'U12'):
        seq_map = {'U8': 199, 'U10': 200, 'U12': 201}
        return redirect('board:view', board_id=board_id, b_seq=seq_map[board_id])

    sword = request.GET.get('sword', '').strip()
    page = request.GET.get('page', 1)

    # 기본 쿼리: 삭제되지 않은 글
    qs = Board.objects.filter(b_gbn=board_id, del_chk='N')

    # 공지사항 게시판(Y)이면 N, E 타입도 같이 보여줌
    if board_id == 'Y':
        qs = Board.objects.filter(b_gbn__in=['Y', 'N', 'E'], del_chk='N')

    # 검색
    if sword:
        qs = qs.filter(Q(b_title__icontains=sword) | Q(b_content__icontains=sword))

    # 공지사항 상단 고정
    notices = qs.filter(b_notice_yn='Y').order_by('-b_seq')
    posts = qs.filter(b_notice_yn='N').order_by('-b_seq')

    # 댓글 수 계산
    from django.db.models import Count
    posts = posts.annotate(comment_count=Count('comments', filter=Q(comments__del_chk='N')))

    paginator = Paginator(posts, 15)
    page_obj = paginator.get_page(page)

    # 포토갤러리: 각 게시글의 첫 이미지 추출
    if board_id == 'P':
        for post in page_obj:
            post.first_image = _extract_first_image(post.b_content)

    context = {
        'config': config,
        'board_id': board_id,
        'notices': notices,
        'page_obj': page_obj,
        'sword': sword,
        'community_menu': COMMUNITY_MENU,
    }
    return render(request, 'board/board_list.html', context)


def board_view(request, board_id, b_seq):
    """게시글 상세"""
    config = BOARD_CONFIG.get(board_id)
    if not config:
        raise Http404

    board = get_object_or_404(Board, b_seq=b_seq, del_chk='N')

    # 조회수 증가 (본인 글 제외)
    if request.user.is_authenticated and request.user.username != board.insert_id:
        board.b_hit += 1
        board.save(update_fields=['b_hit'])
    elif not request.user.is_authenticated:
        board.b_hit += 1
        board.save(update_fields=['b_hit'])

    # 댓글
    comments = BoardComment.objects.filter(board=board, del_chk='N')

    # 첨부파일
    files = BoardFile.objects.filter(board=board)
    images = [f for f in files if f.bs_img]
    attachments = [f for f in files if f.bs_file]

    # 이전글/다음글
    base_qs = Board.objects.filter(del_chk='N')
    if board_id in ('U8', 'U10', 'U12'):
        base_qs = base_qs.filter(b_gbn=board_id)
    elif board_id == 'Y':
        base_qs = base_qs.filter(b_gbn__in=['Y', 'N', 'E'])
    else:
        base_qs = base_qs.filter(b_gbn=board_id)

    prev_post = base_qs.filter(b_seq__lt=b_seq).order_by('-b_seq').first()
    next_post = base_qs.filter(b_seq__gt=b_seq).order_by('b_seq').first()

    # U8/U10/U12 판별
    is_classic = board_id in ('U8', 'U10', 'U12')

    context = {
        'config': config,
        'board_id': board_id,
        'board': board,
        'comments': comments,
        'images': images,
        'attachments': attachments,
        'prev_post': prev_post,
        'next_post': next_post,
        'community_menu': COMMUNITY_MENU,
        'is_classic': is_classic,
    }
    return render(request, 'board/board_view.html', context)


@login_required
def board_write(request, board_id):
    """글쓰기"""
    config = BOARD_CONFIG.get(board_id)
    if not config or not config['user_write']:
        raise Http404

    if request.method == 'POST':
        b_title = request.POST.get('b_title', '').strip()
        b_content = request.POST.get('b_content', '')

        if not b_title:
            return render(request, 'board/board_write.html', {
                'config': config,
                'board_id': board_id,
                'community_menu': COMMUNITY_MENU,
                'error': '제목을 입력하세요.',
            })

        # 새 b_seq 생성
        max_seq = Board.objects.aggregate(Max('b_seq'))['b_seq__max'] or 0
        new_seq = max_seq + 1

        # 새 b_ref 생성
        max_ref = Board.objects.aggregate(Max('b_ref'))['b_ref__max'] or 0
        new_ref = max_ref + 1

        Board.objects.create(
            b_seq=new_seq,
            b_ref=new_ref,
            b_gbn=board_id,
            b_title=b_title,
            b_content=b_content,
            insert_name=request.user.name if hasattr(request.user, 'name') else request.user.username,
            insert_id=request.user.username,
            insert_type='U',
            insert_dt=timezone.now().strftime('%Y-%m-%d'),
            insert_ip=request.META.get('REMOTE_ADDR', ''),
        )
        return redirect('board:list', board_id=board_id)

    context = {
        'config': config,
        'board_id': board_id,
        'community_menu': COMMUNITY_MENU,
    }
    return render(request, 'board/board_write.html', context)


@login_required
def board_edit(request, board_id, b_seq):
    """글수정"""
    config = BOARD_CONFIG.get(board_id)
    if not config:
        raise Http404

    board = get_object_or_404(Board, b_seq=b_seq, del_chk='N')

    # 작성자 확인
    if board.insert_id != request.user.username:
        raise Http404

    if request.method == 'POST':
        b_title = request.POST.get('b_title', '').strip()
        b_content = request.POST.get('b_content', '')

        if not b_title:
            return render(request, 'board/board_edit.html', {
                'config': config,
                'board_id': board_id,
                'board': board,
                'community_menu': COMMUNITY_MENU,
                'error': '제목을 입력하세요.',
            })

        board.b_title = b_title
        board.b_content = b_content
        board.save(update_fields=['b_title', 'b_content'])
        return redirect('board:view', board_id=board_id, b_seq=b_seq)

    context = {
        'config': config,
        'board_id': board_id,
        'board': board,
        'community_menu': COMMUNITY_MENU,
    }
    return render(request, 'board/board_edit.html', context)


@login_required
def board_delete(request, board_id, b_seq):
    """글삭제 (soft delete)"""
    board = get_object_or_404(Board, b_seq=b_seq, del_chk='N')

    if board.insert_id != request.user.username:
        raise Http404

    board.del_chk = 'Y'
    board.save(update_fields=['del_chk'])
    return redirect('board:list', board_id=board_id)


@login_required
def comment_add(request):
    """댓글 등록"""
    if request.method == 'POST':
        b_seq = request.POST.get('b_seq')
        board_id = request.POST.get('board_id')
        comment_text = request.POST.get('comment_content', '').strip()

        if not comment_text or not b_seq:
            return redirect(request.META.get('HTTP_REFERER', '/'))

        board = get_object_or_404(Board, b_seq=b_seq, del_chk='N')

        BoardComment.objects.create(
            board=board,
            b_gbn=board.b_gbn,
            comment=comment_text,
            insert_name=request.user.name if hasattr(request.user, 'name') else request.user.username,
            insert_id=request.user.username,
            insert_type='U',
            insert_dt=timezone.now(),
            insert_ip=request.META.get('REMOTE_ADDR', ''),
        )
        return redirect('board:view', board_id=board_id, b_seq=b_seq)

    return redirect('board:list', board_id='Y')


@login_required
def comment_delete(request, bc_seq):
    """댓글 삭제 (soft delete)"""
    comment = get_object_or_404(BoardComment, id=bc_seq)

    if comment.insert_id != request.user.username:
        raise Http404

    board_id = comment.b_gbn
    b_seq = comment.board.b_seq

    comment.del_chk = 'Y'
    comment.save(update_fields=['del_chk'])

    # board_id가 N이나 E면 Y로 리다이렉트
    if board_id in ('N', 'E'):
        board_id = 'Y'

    return redirect('board:view', board_id=board_id, b_seq=b_seq)
