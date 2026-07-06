from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from coop_shared.auth import decode_token
from coop_shared.database import get_db
from coop_shared.schemas import TokenPayload

security = HTTPBearer(auto_error=False)

ROLES_AUDITORIA = {"AUDITOR", "ADMIN_CORE"}
ROLES_ADMIN = {"ADMIN_CORE"}
ROLES_GERENTE = {"GERENTE_SUCURSAL", "ADMIN_CORE"}
ROLES_CAJERO = {"CAJERO", "GERENTE_SUCURSAL", "ADMIN_CORE"}


def get_client_ip(x_forwarded_for: Optional[str] = Header(None)) -> str:
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return "127.0.0.1"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    try:
        return decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def require_empleado(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if user.tipo != "empleado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso solo empleados")
    return user


def require_socio(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if user.tipo != "socio":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso solo socios")
    return user


def require_roles(*roles: str):
    def checker(user: TokenPayload = Depends(require_empleado)) -> TokenPayload:
        if user.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado")
        return user

    return checker


DbSession = AsyncSession
GetDb = Depends(get_db)
