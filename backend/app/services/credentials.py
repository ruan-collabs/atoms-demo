import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

class CredentialError(Exception):
    pass

def master_key():
    try:
        key=base64.urlsafe_b64decode(settings.credential_master_key) if settings.credential_master_key else Path(settings.credential_key_file).read_bytes()
        if len(key)!=32:raise ValueError()
        return key
    except (OSError,ValueError):
        raise CredentialError('加密密钥不可用，操作已拒绝') from None

def aad(owner,config_id,version):
    return f'atoms-credential:{owner}:{config_id}:{version}'.encode()

def encrypt(value,owner,config_id,version):
    nonce=os.urandom(12)
    return base64.urlsafe_b64encode(nonce+AESGCM(master_key()).encrypt(nonce,value.encode(),aad(owner,config_id,version))).decode()

def decrypt(ciphertext,owner,config_id,version):
    try:
        raw=base64.urlsafe_b64decode(ciphertext)
        return AESGCM(master_key()).decrypt(raw[:12],raw[12:],aad(owner,config_id,version)).decode()
    except CredentialError:raise
    except Exception:raise CredentialError('凭证校验失败，操作已拒绝') from None
