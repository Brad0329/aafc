from .base import *
from decouple import config

SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        # 커넥션 재사용 (RDS 커넥션 고갈 방지)
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
            # 30초 초과 쿼리 자동 Kill (DB 잠금 방지)
            'options': '-c statement_timeout=30000',
        },
    }
}

# 정적 파일 (collectstatic 결과물)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# S3 미디어 파일
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ap-northeast-2')
AWS_S3_CUSTOM_DOMAIN = f"{config('AWS_STORAGE_BUCKET_NAME')}.s3.{config('AWS_S3_REGION_NAME', default='ap-northeast-2')}.amazonaws.com"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

# 보안 설정 (HTTPS 적용 후 아래 주석 해제)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
