import base64
from Cryptodome.Cipher import ChaCha20

from command_center.env import get_env_str

# https://pycryptodome.readthedocs.io/en/latest/src/cipher/chacha20.html
# ChaCha20-Poly1305 Chacha20 암호와와 인증기능까지 추가한 기능
# 추후 XChaCha20 으로 발전시킬것 2022년 12월 26일 xchacha는 draft stage임으로 아직 적용 안함

# key = get_random_bytes(32)
# cipher = ChaCha20.new(key=key)
# nonce = base64.b64encode(cipher.nonce).decode('utf-8')

default_key = get_env_str('CHACHA_DEFAULT_KEY')
default_nonce = get_env_str('CHACHA_DEFAULT_NONCE')


class ChaChaEncrypt:

    def __init__(self, key=default_key, nonce=default_nonce):
        key = self.decode_base64(key) #Base64로 인코딩된 키(문자열)을 디코딩하여 바이너리 데이터로 가져온다.
        nonce = self.decode_base64(nonce)
        self.cipher = ChaCha20.new(key=key, nonce=nonce)

    def encrypt(self, msg: bytes):
        ciphertext: bytes = self.cipher.encrypt(msg)
        return ciphertext

    def decrypt(self, msg: bytes):
        plaintext: bytes = self.cipher.decrypt(msg)
        return plaintext

    @staticmethod
    def encode_base64(msg: bytes):
        # Base64란 Binary Data를 Text로 바꾸는 Encoding(binary-to-text encoding schemes)의 하나로써 Binary Data를 Character set에
        # 영향을 받지 않는 공통 ASCII 영역의 문자로만 이루어진 문자열로 바꾸는 Encoding이다.
        # Encode the bytes-like object s using Base64 and return a bytes object.
        return base64.b64encode(msg)

    @staticmethod
    def decode_base64(msg):
        # Decode the Base64 encoded bytes-like object or ASCII string s.
        # Base64로 인코딩된 바이트열류 객체 또는 ASCII 문자열 s를 디코딩합니다.
        # The result is returned as a bytes object. A binascii.Error is raised if s is incorrectly padded.
        return base64.b64decode(msg)

    @staticmethod
    def b64encoded_bytes_to_string(msg: bytes):
        # Decode the bytes using the codec registered for encoding.
        return msg.decode('utf-8')


def encrypt_chacha(msg: bytes, key=default_key, nonce=default_nonce):
    key = base64.b64decode(key)
    nonce = base64.b64decode(nonce)
    cipher = ChaCha20.new(key=key, nonce=nonce)
    ciphertext = cipher.encrypt(msg)
    return ciphertext


def decrypt_chacha(msg: bytes, key=default_key, nonce=default_nonce):
    key = base64.b64decode(key)
    nonce = base64.b64decode(nonce)
    cipher = ChaCha20.new(key=key, nonce=nonce)
    plaintext = cipher.decrypt(msg)
    return plaintext
