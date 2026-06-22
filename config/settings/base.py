from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = 'django-insecure-y+=_o22umdcu3jju%e+mgzaqi%^z@ebq@oq^u)jq9cljbv#qu6'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    # project apps
    'apps.accounts',
    'apps.enrollment',
    'apps.courses',
    'apps.payments',
    'apps.board',
    'apps.consult',
    'apps.shop',
    'apps.points',
    'apps.notifications',
    'apps.reports',
    'apps.common',
    'apps.office',
    # 3rd party
    'django_ckeditor_5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.office.context_processors.office_user',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'config.hashers.LegacySHA256Hasher',
]

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.Member'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# 보안 설정
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# CKEditor 5
CKEDITOR_5_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
CKEDITOR_5_UPLOAD_PATH = 'uploads/ckeditor/'
customColorPalette = [
    {'color': 'hsl(4, 90%, 58%)', 'label': 'Red'},
    {'color': 'hsl(340, 82%, 52%)', 'label': 'Pink'},
    {'color': 'hsl(291, 64%, 42%)', 'label': 'Purple'},
    {'color': 'hsl(262, 52%, 47%)', 'label': 'Deep Purple'},
    {'color': 'hsl(231, 48%, 48%)', 'label': 'Indigo'},
    {'color': 'hsl(207, 90%, 54%)', 'label': 'Blue'},
]
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'fontSize', 'fontColor', '|',
            'bulletedList', 'numberedList', '|',
            'link', 'insertImage', 'mediaEmbed', '|',
            'blockQuote', 'insertTable', '|',
            'undo', 'redo',
        ],
        'image': {
            'toolbar': ['imageTextAlternative', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter',
                        'imageStyle:side'],
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties'],
        },
        'height': 400,
        'width': '100%',
    },
}

# ── Toss Payments ──
# 로컬: 아래 default(테스트 키)로 동작.
#   developers.tosspayments.com → 내 개발정보 → API 키에서 test_ck_/test_sk_ 발급 후
#   default 값에 채우거나 프로젝트 루트 .env 에 넣으면 됨. (현재는 placeholder)
# 운영(EC2): .env 에 TOSS_CLIENT_KEY / TOSS_SECRET_KEY (live_ck_/live_sk_) 설정 → override.
#   주의: live 키는 HTTPS + 등록 도메인에서만 동작.
# 시크릿 키는 콜론 없이 저장 (confirm 호출 시 HTTPBasicAuth(secret, '')로 'secret:' 인코딩 처리됨)
TOSS_CLIENT_KEY = config('TOSS_CLIENT_KEY', default='test_ck_PLACEHOLDER')
TOSS_SECRET_KEY = config('TOSS_SECRET_KEY', default='test_sk_PLACEHOLDER')
TOSS_CONFIRM_URL = 'https://api.tosspayments.com/v1/payments/confirm'

# ── NICE 통합인증 (회원가입 휴대폰 본인확인) ──
# NICE API 이용자포털(My App List)에서 발급한 client_id / client_secret.
# 값은 .env 에 설정 (채팅/git 노출 금지). 비어 있으면 본인인증 호출이 실패한다.
#   NICE_CLIENT_ID / NICE_CLIENT_SECRET : 인증키
#   NICE_RETURN_URL : 인증 결과 콜백. NICE 포털에 등록한 return_url 과 반드시 일치.
#   NICE_API_BASE   : 통합인증 API base URL (기본: 운영 도메인)
NICE_CLIENT_ID = config('NICE_CLIENT_ID', default='')
NICE_CLIENT_SECRET = config('NICE_CLIENT_SECRET', default='')
NICE_RETURN_URL = config('NICE_RETURN_URL', default='http://localhost:8000/accounts/nice/callback/')
NICE_API_BASE = config('NICE_API_BASE', default='https://auth.niceid.co.kr/ido/intc/v1.0')
