"""결제 미완료(pending) 쇼핑몰 주문 정리 커맨드.

Toss 전환으로 order_create가 결제 전 주문을 state=100/is_finish='F'로 먼저 생성하므로,
결제창 이탈/실패로 확정되지 않은 주문이 쌓일 수 있다. 일정 시간 지난 미결제 주문을 취소 처리한다.

운영: cron 등으로 주기 실행 예시 →
    */30 * * * *  cd /app && /app/venv/bin/python manage.py expire_pending_orders --settings=config.settings.prod
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.shop.models import Order


class Command(BaseCommand):
    help = '결제 미완료(is_finish=F, state=100) 주문을 N분 경과 시 취소(state=402) 처리'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes', type=int, default=60,
            help='이 시간(분) 이전에 생성된 미결제 주문을 취소 (기본 60)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='실제 변경 없이 대상 건수만 출력',
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        cutoff = timezone.now() - timedelta(minutes=minutes)

        qs = Order.objects.filter(is_finish='F', state=100, reg_date__lt=cutoff)
        count = qs.count()

        if options['dry_run']:
            self.stdout.write(
                f'[dry-run] 취소 대상 미결제 주문: {count}건 '
                f'(cutoff={timezone.localtime(cutoff):%Y-%m-%d %H:%M})'
            )
            return

        updated = qs.update(state=402, is_cancel='T', cancel_date=timezone.now())
        self.stdout.write(self.style.SUCCESS(
            f'미결제 주문 {updated}건 취소 처리 완료 '
            f'(cutoff={timezone.localtime(cutoff):%Y-%m-%d %H:%M})'
        ))
