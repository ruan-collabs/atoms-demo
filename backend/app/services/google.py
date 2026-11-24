"""Google OIDC server-side authorization-code + PKCE flow.
No provider access/refresh/ID tokens are stored or sent to the SPA.
"""
import hmac
import httpx
import jwt
from jwt import PyJWKClient
from pydantic import EmailStr, TypeAdapter
from app.config import settings
from app.security import digest

AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
JWKS_URL = 'https://www.googleapis.com/oauth2/v3/certs'
# Cache signing keys; fixed trusted destination, never use URLs from an unverified token.
jwks = PyJWKClient(JWKS_URL, cache_jwk_set=True, lifespan=3600, timeout=10)

class GoogleAuthError(Exception):
    pass

async def exchange_code(code: str, verifier: str):
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False) as client:
            response = await client.post(TOKEN_URL, data={
                'code': code, 'client_id': settings.google_client_id,
                'client_secret': settings.google_client_secret,
                'redirect_uri': settings.google_redirect_uri,
                'grant_type': 'authorization_code', 'code_verifier': verifier,
            })
        if response.status_code != 200:
            raise GoogleAuthError('token_exchange_failed')
        data = response.json()
        token = data.get('id_token')
        if not isinstance(token, str) or len(token) > 16384:
            raise GoogleAuthError('invalid_id_token')
        return token
    except (httpx.HTTPError, ValueError):
        raise GoogleAuthError('google_unavailable') from None

def validate_id_token(token: str, nonce_hash: str):
    try:
        key = jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key=key, algorithms=['RS256'],
            audience=settings.google_client_id,
            issuer=['https://accounts.google.com', 'accounts.google.com'],
            options={'require': ['exp', 'iat', 'iss', 'aud', 'sub', 'nonce', 'email', 'email_verified']}, leeway=20)
        nonce = claims.get('nonce')
        if not isinstance(nonce, str) or not hmac.compare_digest(digest(nonce), nonce_hash):
            raise GoogleAuthError('invalid_nonce')
        if claims.get('email_verified') is not True:
            raise GoogleAuthError('unverified_email')
        if claims.get('azp') not in (None, settings.google_client_id):
            raise GoogleAuthError('invalid_authorized_party')
        subject = claims['sub']
        if not isinstance(subject, str) or not subject or len(subject) > 255 or not subject.isascii():
            raise GoogleAuthError('invalid_subject')
        email = str(TypeAdapter(EmailStr).validate_python(claims['email'])).lower()
        return {'sub': subject, 'email': email}
    except GoogleAuthError:
        raise
    except (jwt.PyJWTError, ValueError, OSError):
        raise GoogleAuthError('invalid_id_token') from None
