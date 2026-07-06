from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from coop_shared.audit import registrar_evento
from coop_shared.database import get_db, get_replica_db
from coop_shared.deps import (
    ROLES_CAJERO,
    ROLES_GERENTE,
    get_client_ip,
    get_current_user,
    require_empleado,
    require_roles,
    require_socio,
)
from coop_shared.schemas import (
    BloquearCuentaRequest,
    CuentaResponse,
    DepositoRequest,
    RetiroRequest,
    SocioCreateRequest,
    SocioResponse,
    TokenPayload,
    TransferenciaRequest,
    TransaccionResponse,
)

app = FastAPI(title="Cuentas y Transacciones", version="1.0.0", root_path="/api/v1/cuentas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMISION_INTERBANCARIA = Decimal("0.005")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "cuentas-svc"}


def _cuenta_from_row(row) -> CuentaResponse:
    return CuentaResponse(
        id=row["id"],
        numero_cuenta=row["numero_cuenta"],
        tipo=row["tipo"],
        saldo=row["saldo"],
        estado=row["estado"],
        id_socio=row["id_socio"],
    )


@app.get("/cuentas/{cuenta_id}", response_model=CuentaResponse)
async def obtener_cuenta(
    cuenta_id: int,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_replica_db),
):
    result = await db.execute(
        text("""
            SELECT id, numero_cuenta, tipo, saldo, estado, id_socio
            FROM core_bancario.cuenta WHERE id = :id
        """),
        {"id": cuenta_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if user.tipo == "socio" and row["id_socio"] != user.socio_id:
        raise HTTPException(status_code=403, detail="Cuenta no pertenece al socio")
    return _cuenta_from_row(row)


@app.get("/cuentas/socio/{socio_id}", response_model=list[CuentaResponse])
async def listar_cuentas_socio(
    socio_id: int,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_replica_db),
):
    if user.tipo == "socio" and user.socio_id != socio_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    result = await db.execute(
        text("""
            SELECT id, numero_cuenta, tipo, saldo, estado, id_socio
            FROM core_bancario.cuenta WHERE id_socio = :socio_id ORDER BY id
        """),
        {"socio_id": socio_id},
    )
    return [_cuenta_from_row(r) for r in result.mappings()]


@app.get("/cuentas/numero/{numero}", response_model=CuentaResponse)
async def buscar_por_numero(
    numero: str,
    _: TokenPayload = Depends(require_roles(*ROLES_CAJERO)),
    db: AsyncSession = Depends(get_replica_db),
):
    result = await db.execute(
        text("""
            SELECT id, numero_cuenta, tipo, saldo, estado, id_socio
            FROM core_bancario.cuenta WHERE numero_cuenta = :numero
        """),
        {"numero": numero},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return _cuenta_from_row(row)


@app.get("/socios/dni/{dni}", response_model=SocioResponse)
async def buscar_socio_dni(
    dni: str,
    _: TokenPayload = Depends(require_roles(*ROLES_CAJERO)),
    db: AsyncSession = Depends(get_replica_db),
):
    result = await db.execute(
        text("""
            SELECT id, dni, nombres, apellidos, email, telefono, id_sede, activo
            FROM core_bancario.socio WHERE dni = :dni
        """),
        {"dni": dni},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    return SocioResponse(**row)


@app.post("/socios", response_model=SocioResponse, status_code=201)
async def registrar_socio(
    body: SocioCreateRequest,
    request: Request,
    user: TokenPayload = Depends(require_roles(*ROLES_CAJERO)),
    db: AsyncSession = Depends(get_db),
):
    from coop_shared.auth import hash_password

    pin = body.dni[-4:]
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    result = await db.execute(
        text("""
            INSERT INTO core_bancario.socio
                (dni, nombres, apellidos, email, telefono, id_sede, pin_hash, usuario_creacion)
            VALUES (:dni, :nombres, :apellidos, :email, :telefono, :id_sede, :pin_hash, :user)
            RETURNING id, dni, nombres, apellidos, email, telefono, id_sede, activo
        """),
        {
            **body.model_dump(),
            "pin_hash": hash_password(pin),
            "user": user.sub,
        },
    )
    row = result.mappings().first()
    await registrar_evento(
        db, id_usuario=user.usuario_id, accion="INSERT", modulo="socio",
        detalle=f"Nuevo socio DNI {body.dni}", ip_origen=ip,
    )
    await db.commit()
    return SocioResponse(**row)


@app.post("/transacciones/deposito", response_model=TransaccionResponse)
async def deposito(
    body: DepositoRequest,
    request: Request,
    user: TokenPayload = Depends(require_roles(*ROLES_CAJERO)),
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    cuenta = await db.execute(
        text("SELECT id, estado FROM core_bancario.cuenta WHERE id = :id FOR UPDATE"),
        {"id": body.id_cuenta},
    )
    c = cuenta.mappings().first()
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if c["estado"] != "ACTIVA":
        raise HTTPException(status_code=400, detail="Cuenta no activa")

    await db.execute(
        text("UPDATE core_bancario.cuenta SET saldo = saldo + :monto WHERE id = :id"),
        {"monto": body.monto, "id": body.id_cuenta},
    )
    result = await db.execute(
        text("""
            INSERT INTO core_bancario.transaccion
                (monto, tipo, estado, descripcion, id_cuenta_destino, id_usuario, id_sede_origen)
            VALUES (:monto, 'DEPOSITO', 'COMPLETADA', :desc, :id, :uid, :sede)
            RETURNING id, monto, tipo, estado, descripcion, id_cuenta_origen, id_cuenta_destino, fecha_operacion
        """),
        {
            "monto": body.monto,
            "id": body.id_cuenta,
            "desc": body.descripcion or "Depósito en ventanilla",
            "uid": user.usuario_id,
            "sede": user.sede_id,
        },
    )
    row = result.mappings().first()
    await registrar_evento(
        db, id_usuario=user.usuario_id, accion="DEPOSITO", modulo="transaccion",
        detalle=f"Depósito S/ {body.monto} cuenta {body.id_cuenta}", ip_origen=ip,
    )
    await db.commit()
    return TransaccionResponse(**row)


@app.post("/transacciones/retiro", response_model=TransaccionResponse)
async def retiro(
    body: RetiroRequest,
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    if user.tipo == "empleado" and user.rol not in ROLES_CAJERO:
        raise HTTPException(status_code=403, detail="Rol no autorizado")

    cuenta = await db.execute(
        text("SELECT id, saldo, estado, id_socio FROM core_bancario.cuenta WHERE id = :id FOR UPDATE"),
        {"id": body.id_cuenta},
    )
    c = cuenta.mappings().first()
    if not c:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    if user.tipo == "socio" and c["id_socio"] != user.socio_id:
        raise HTTPException(status_code=403, detail="Cuenta no pertenece al socio")
    if c["estado"] == "BLOQUEADA":
        raise HTTPException(status_code=400, detail="Cuenta bloqueada")
    if c["saldo"] < body.monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")

    uid = user.usuario_id if user.tipo == "empleado" else 2
    sede = user.sede_id if user.tipo == "empleado" else 3

    await db.execute(
        text("UPDATE core_bancario.cuenta SET saldo = saldo - :monto WHERE id = :id"),
        {"monto": body.monto, "id": body.id_cuenta},
    )
    result = await db.execute(
        text("""
            INSERT INTO core_bancario.transaccion
                (monto, tipo, estado, descripcion, id_cuenta_origen, id_usuario, id_sede_origen)
            VALUES (:monto, 'RETIRO', 'COMPLETADA', :desc, :id, :uid, :sede)
            RETURNING id, monto, tipo, estado, descripcion, id_cuenta_origen, id_cuenta_destino, fecha_operacion
        """),
        {
            "monto": body.monto,
            "id": body.id_cuenta,
            "desc": body.descripcion or "Retiro",
            "uid": uid,
            "sede": sede,
        },
    )
    row = result.mappings().first()
    await registrar_evento(
        db, id_usuario=uid, accion="RETIRO", modulo="transaccion",
        detalle=f"Retiro S/ {body.monto} cuenta {body.id_cuenta}", ip_origen=ip,
    )
    await db.commit()
    return TransaccionResponse(**row)


@app.post("/transacciones/transferencia", response_model=TransaccionResponse)
async def transferencia(
    body: TransferenciaRequest,
    request: Request,
    user: TokenPayload = Depends(require_socio),
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    if body.id_cuenta_origen == body.id_cuenta_destino:
        raise HTTPException(status_code=400, detail="Cuentas origen y destino iguales")

    origen = await db.execute(
        text("""
            SELECT c.id, c.saldo, c.estado, c.id_socio, s.id_sede
            FROM core_bancario.cuenta c
            JOIN core_bancario.socio s ON s.id = c.id_socio
            WHERE c.id = :id FOR UPDATE
        """),
        {"id": body.id_cuenta_origen},
    )
    o = origen.mappings().first()
    if not o or o["id_socio"] != user.socio_id:
        raise HTTPException(status_code=403, detail="Cuenta origen no autorizada")
    if o["estado"] != "ACTIVA":
        raise HTTPException(status_code=400, detail="Cuenta origen no activa")

    destino = await db.execute(
        text("""
            SELECT c.id, c.estado, s.id_sede
            FROM core_bancario.cuenta c
            JOIN core_bancario.socio s ON s.id = c.id_socio
            WHERE c.id = :id FOR UPDATE
        """),
        {"id": body.id_cuenta_destino},
    )
    d = destino.mappings().first()
    if not d or d["estado"] != "ACTIVA":
        raise HTTPException(status_code=400, detail="Cuenta destino inválida")

    monto_total = body.monto
    if o["id_sede"] != d["id_sede"]:
        comision = (body.monto * COMISION_INTERBANCARIA).quantize(Decimal("0.01"))
        monto_total += comision

    if o["saldo"] < monto_total:
        raise HTTPException(status_code=400, detail="Saldo insuficiente (incluye comisión interbancaria)")

    desc = body.descripcion or "Transferencia entre cuentas"
    if o["id_sede"] != d["id_sede"]:
        desc += f" (comisión interbancaria S/ {(body.monto * COMISION_INTERBANCARIA).quantize(Decimal('0.01'))})"

    await db.execute(
        text("UPDATE core_bancario.cuenta SET saldo = saldo - :monto WHERE id = :id"),
        {"monto": monto_total, "id": body.id_cuenta_origen},
    )
    await db.execute(
        text("UPDATE core_bancario.cuenta SET saldo = saldo + :monto WHERE id = :id"),
        {"monto": body.monto, "id": body.id_cuenta_destino},
    )
    result = await db.execute(
        text("""
            INSERT INTO core_bancario.transaccion
                (monto, tipo, estado, descripcion, id_cuenta_origen, id_cuenta_destino, id_usuario, id_sede_origen)
            VALUES (:monto, 'TRANSFERENCIA', 'COMPLETADA', :desc, :origen, :destino, 2, :sede)
            RETURNING id, monto, tipo, estado, descripcion, id_cuenta_origen, id_cuenta_destino, fecha_operacion
        """),
        {
            "monto": body.monto,
            "desc": desc,
            "origen": body.id_cuenta_origen,
            "destino": body.id_cuenta_destino,
            "sede": o["id_sede"],
        },
    )
    row = result.mappings().first()
    await registrar_evento(
        db, id_usuario=None, accion="TRANSFERENCIA", modulo="transaccion",
        detalle=f"Transferencia S/ {body.monto} de {body.id_cuenta_origen} a {body.id_cuenta_destino}",
        ip_origen=ip,
    )
    await db.commit()
    return TransaccionResponse(**row)


@app.post("/cuentas/{cuenta_id}/bloquear", response_model=CuentaResponse)
async def bloquear_cuenta(
    cuenta_id: int,
    body: BloquearCuentaRequest,
    request: Request,
    user: TokenPayload = Depends(require_roles(*ROLES_GERENTE)),
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    result = await db.execute(
        text("""
            UPDATE core_bancario.cuenta SET estado = 'BLOQUEADA'
            WHERE id = :id
            RETURNING id, numero_cuenta, tipo, saldo, estado, id_socio
        """),
        {"id": cuenta_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    await registrar_evento(
        db, id_usuario=user.usuario_id, accion="BLOQUEO", modulo="cuenta",
        detalle=f"Cuenta {cuenta_id} bloqueada: {body.motivo}", ip_origen=ip,
    )
    await db.commit()
    return _cuenta_from_row(row)


@app.get("/transacciones/recientes", response_model=list[TransaccionResponse])
async def transacciones_recientes(
    socio_id: int,
    limit: int = 10,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_replica_db),
):
    if user.tipo == "socio" and user.socio_id != socio_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    result = await db.execute(
        text("""
            SELECT t.id, t.monto, t.tipo, t.estado, t.descripcion,
                   t.id_cuenta_origen, t.id_cuenta_destino, t.fecha_operacion
            FROM core_bancario.transaccion t
            JOIN core_bancario.cuenta c ON c.id = COALESCE(t.id_cuenta_origen, t.id_cuenta_destino)
            WHERE c.id_socio = :socio_id
            ORDER BY t.fecha_operacion DESC
            LIMIT :limit
        """),
        {"socio_id": socio_id, "limit": limit},
    )
    return [TransaccionResponse(**r) for r in result.mappings()]
