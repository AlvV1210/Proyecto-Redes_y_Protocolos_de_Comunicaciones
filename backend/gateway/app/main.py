from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from coop_shared.audit import registrar_evento
from coop_shared.auth import create_access_token, verify_password
from coop_shared.database import get_db
from coop_shared.deps import get_client_ip
from coop_shared.schemas import LoginEmpleadoRequest, LoginSocioRequest, TokenResponse

app = FastAPI(title="Cooperativa Gateway Auth", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway-auth"}


@app.get("/api/v1/auth/health")
async def health_auth():
    return {"status": "ok", "service": "gateway-auth"}


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login_empleado(
    body: LoginEmpleadoRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    result = await db.execute(
        text("""
            SELECT u.id, u.username, u.password_hash, u.activo, r.nombre_rol, u.id_sede
            FROM core_bancario.usuario u
            JOIN core_bancario.rol r ON r.id = u.id_rol
            WHERE u.username = :username
        """),
        {"username": body.username},
    )
    row = result.mappings().first()
    if not row or not row["activo"] or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token, expires = create_access_token({
        "sub": row["username"],
        "tipo": "empleado",
        "rol": row["nombre_rol"],
        "usuario_id": row["id"],
        "sede_id": row["id_sede"],
        "nombre": row["username"],
    })
    await registrar_evento(
        db, id_usuario=row["id"], accion="LOGIN", modulo="AUTENTICACION",
        detalle=f"Login empleado {row['username']}", ip_origen=ip,
    )
    await db.commit()
    return TokenResponse(
        access_token=token, expires_in=expires, rol=row["nombre_rol"],
        usuario_id=row["id"], nombre=row["username"],
    )


@app.post("/api/v1/auth/socio/login", response_model=TokenResponse)
async def login_socio(
    body: LoginSocioRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    result = await db.execute(
        text("""
            SELECT id, dni, nombres, apellidos, pin_hash, activo
            FROM core_bancario.socio
            WHERE dni = :dni
        """),
        {"dni": body.dni},
    )
    row = result.mappings().first()
    if not row or not row["activo"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Socio no encontrado")
    if not row["pin_hash"] or not verify_password(body.pin, row["pin_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="PIN inválido")

    nombre = f"{row['nombres']} {row['apellidos']}"
    token, expires = create_access_token({
        "sub": row["dni"],
        "tipo": "socio",
        "socio_id": row["id"],
        "nombre": nombre,
    })
    await registrar_evento(
        db, id_usuario=None, accion="LOGIN_SOCIO", modulo="AUTENTICACION",
        detalle=f"Login socio DNI {row['dni']}", ip_origen=ip,
    )
    await db.commit()
    return TokenResponse(
        access_token=token, expires_in=expires,
        socio_id=row["id"], nombre=nombre,
    )
