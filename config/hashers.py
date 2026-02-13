import hashlib

from django.contrib.auth.hashers import BasePasswordHasher


class LegacySHA256Hasher(BasePasswordHasher):
    """기존 ASP 시스템의 KISA SHA256 해시와 호환되는 hasher"""
    algorithm = 'sha256'

    def salt(self):
        return ''

    def encode(self, password, salt):
        hash_value = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return f'{self.algorithm}${hash_value}'

    def verify(self, password, encoded):
        _, hash_value = encoded.split('$', 1)
        candidate = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return candidate.lower() == hash_value.lower()

    def safe_summary(self, encoded):
        _, hash_value = encoded.split('$', 1)
        return {
            'algorithm': self.algorithm,
            'hash': f'{hash_value[:6]}******',
        }

    def must_update(self, encoded):
        return False
