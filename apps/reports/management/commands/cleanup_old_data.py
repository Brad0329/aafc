"""
오래된 리포트 데이터 정리 Management Command

사용법:
    python manage.py cleanup_old_data --dry-run   # 대상 건수 확인만
    python manage.py cleanup_old_data             # 실제 삭제 실행

기준: 2023년 이전 전체 삭제
대상 모델별 course_ym 형식이 다르므로 cutoff 값을 각각 지정:
  - DailyTotalData       : 'YYYY-MM' 형식 → cutoff '2024-01'
  - DailyCoachData       : 'YYYYMM'  형식 → cutoff '202401'
  - DailyCoachDataNew    : 'YYYYMM'  형식 → cutoff '202401'
  - DailyCoachDataMonth  : 'YYYYMM'  형식 → cutoff '202401'
"""

from django.core.management.base import BaseCommand
from apps.reports.models import (
    DailyTotalData, DailyCoachData, DailyCoachDataNew, DailyCoachDataMonth
)

BATCH_SIZE = 10000

# (테이블명, 모델, course_ym cutoff)
TARGETS = [
    ('reports_dailytotaldata',      DailyTotalData,      '2024-01'),
    ('reports_dailycoachdata',      DailyCoachData,      '202401'),
    ('reports_dailycoachdatanew',   DailyCoachDataNew,   '202401'),
    ('reports_dailycoachdatamonth', DailyCoachDataMonth, '202401'),
]


class Command(BaseCommand):
    help = '2023년 이전 리포트 데이터 일괄 삭제 (course_ym 기준)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 삭제 없이 대상 건수만 출력',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN 모드] 실제 삭제는 실행되지 않습니다.\n'))
        else:
            self.stdout.write(self.style.ERROR('[실제 삭제 모드] 삭제된 데이터는 복구할 수 없습니다.\n'))

        total_deleted = 0

        for table_name, model, cutoff in TARGETS:
            qs = model.objects.filter(course_ym__lt=cutoff)
            count = qs.count()

            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] {table_name}: '
                    f'{count:,}건 삭제 예정 (course_ym < {cutoff})'
                )
                continue

            if count == 0:
                self.stdout.write(f'{table_name}: 삭제 대상 없음')
                continue

            self.stdout.write(f'{table_name}: {count:,}건 삭제 시작...')
            deleted_total = 0

            while True:
                # 배치 삭제: pk 목록 조회 후 삭제 (DB 락 최소화)
                ids = list(
                    model.objects.filter(course_ym__lt=cutoff)
                    .values_list('pk', flat=True)[:BATCH_SIZE]
                )
                if not ids:
                    break

                deleted, _ = model.objects.filter(pk__in=ids).delete()
                deleted_total += deleted
                self.stdout.write(f'  {deleted_total:,}건 삭제 완료...')

            self.stdout.write(
                self.style.SUCCESS(f'  → {table_name} 완료: 총 {deleted_total:,}건 삭제')
            )
            total_deleted += deleted_total

        if not dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'=== 전체 완료: 총 {total_deleted:,}건 삭제 ==='))
            self.stdout.write('다음 단계: VACUUM ANALYZE 실행 (DATA_CLEANUP_PLAN.md STEP 5 참고)')
