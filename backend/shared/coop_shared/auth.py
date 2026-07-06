import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from coop_shared.config import settings
from coop_shared.schemas import TokenPayload


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def create_access_token(payload: dict) -> tuple[str, int]:
    expire_hours = settings.jwt_expire_hours
    expire = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    data = {**payload, "exp": expire}
    token = jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expire_hours * 3600


def decode_token(token: str) -> TokenPayload:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**data)
    except JWTError as exc:
        raise ValueError("Token inválido o expirado") from exc
