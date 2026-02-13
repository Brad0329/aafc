from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aafc_dev',
        'USER': 'postgres',
        'PASSWORD': '01075321111',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
