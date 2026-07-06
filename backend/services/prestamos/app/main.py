from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from coop_shared.audit import registrar_evento
from coop_shared.database import get_db
from coop_shared.deps import ROLES_GERENTE, get_client_ip, get_current_user, require_roles, require_socio
from coop_shared.schemas import (
    CuotaResponse,
    EstadoPrestamo,
    EvaluarPrestamoResponse,
    PrestamoDetalleResponse,
    PrestamoRequest,
    PrestamoResponse,
    TokenPayload,
)

app = FastAPI(title="Préstamos y Scoring", version="1.0.0", root_path="/api/v1/prestamos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONTO_MAX_AUTO = Decimal("50000")
SCORE_MINIMO = 70.0


@app.get("/health")
async def health():
    return {"status": "ok", "service": "prestamos-svc"}


async def calcular_score(db: AsyncSession, socio_id: int, monto: Decimal) -> float:
    saldo = await db.execute(
        text("SELECT COALESCE(AVG(saldo), 0) AS prom FROM core_bancario.cuenta WHERE id_socio = :sid"),
        {"sid": socio_id},
    )
    saldo_prom = float(saldo.mappings().first()["prom"] or 0)

    antig = await db.execute(
        text("""
            SELECT EXTRACT(MONTH FROM AGE(NOW(), MIN(fecha_creacion))) AS meses
            FROM core_bancario.cuenta WHERE id_socio = :sid
        """),
        {"sid": socio_id},
    )
    meses = float(antig.mappings().first()["meses"] or 0)

    deuda = await db.execute(
        text("""
            SELECT COUNT(*) AS vencidas FROM core_bancario.cuota_prestamo cp
            JOIN core_bancario.prestamo p ON p.id = cp.id_prestamo
            WHERE p.id_socio = :sid AND cp.pagada = FALSE AND cp.fecha_vencimiento < CURRENT_DATE
        """),
        {"sid": socio_id},
    )
    vencidas = int(deuda.mappings().first()["vencidas"])

    score = 100.0
    if saldo_prom > 0:
        score -= float(monto / Decimal(str(saldo_prom))) * 20
    score -= vencidas * 10
    score += meses * 0.5
    return max(0.0, min(100.0, score))


async def generar_cuotas(db: AsyncSession, prestamo_id: int, monto: Decimal, plazo: int):
    cuota_monto = (monto / plazo).quantize(Decimal("0.01"))
    hoy = date.today()
    for i in range(1, plazo + 1):
        venc = hoy + relativedelta(months=i)
        await db.execute(
            text("""
                INSERT INTO core_bancario.cuota_prestamo
                    (id_prestamo, numero_cuota, monto, fecha_vencimiento)
                VALUES (:pid, :n, :m, :v)
            """),
            {"pid": prestamo_id, "n": i, "m": cuota_monto, "v": venc},
        )


@app.post("/prestamos/solicitar", response_model=PrestamoResponse, status_code=201)
async def solicitar_prestamo(
    body: PrestamoRequest,
    request: Request,
    user: TokenPayload = Depends(require_socio),
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    result = await db.execute(
        text("""
            INSERT INTO core_bancario.prestamo
                (monto, tasa_interes, plazo_meses, estado, id_socio, id_usuario_solicita)
            VALUES (:monto, :tasa, :plazo, 'SOLICITADO', :socio, 2)
            RETURNING id, monto, tasa_interes, plazo_meses, estado, id_socio, fecha_solicitud, fecha_aprobacion
        """),
        {
            "monto": body.monto,
            "tasa": body.tasa_interes,
            "plazo": body.plazo_meses,
            "socio": user.socio_id,
        },
    )
    row = result.mappings().first()
    await registrar_evento(
        db, id_usuario=None, accion="SOLICITUD", modulo="prestamo",
        detalle=f"Solicitud préstamo S/ {body.monto} socio {user.socio_id}", ip_origen=ip,
    )
    await db.commit()
    return PrestamoResponse(**row)


@app.get("/prestamos/{prestamo_id}", response_model=PrestamoDetalleResponse)
async def obtener_prestamo(
    prestamo_id: int,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id, monto, tasa_interes, plazo_meses, estado, id_socio,
                   fecha_solicitud, fecha_aprobacion
            FROM core_bancario.prestamo WHERE id = :id
        """),
        {"id": prestamo_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if user.tipo == "socio" and row["id_socio"] != user.socio_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    cuotas = await db.execute(
        text("""
            SELECT numero_cuota, monto, fecha_vencimiento, pagada
            FROM core_bancario.cuota_prestamo WHERE id_prestamo = :id ORDER BY numero_cuota
        """),
        {"id": prestamo_id},
    )
    return PrestamoDetalleResponse(
        **row,
        cuotas=[CuotaResponse(**c) for c in cuotas.mappings()],
    )


@app.get("/prestamos/socio/{socio_id}", response_model=list[PrestamoResponse])
async def listar_prestamos_socio(
    socio_id: int,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.tipo == "socio" and user.socio_id != socio_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    result = await db.execute(
        text("""
            SELECT id, monto, tasa_interes, plazo_meses, estado, id_socio,
                   fecha_solicitud, fecha_aprobacion
            FROM core_bancario.prestamo WHERE id_socio = :sid ORDER BY id DESC
        """),
        {"sid": socio_id},
    )
    return [PrestamoResponse(**r) for r in result.mappings()]


@app.post("/prestamos/{prestamo_id}/evaluar", response_model=EvaluarPrestamoResponse)
async def evaluar_prestamo(
    prestamo_id: int,
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request.headers.get("x-forwarded-for"))
    prestamo = await db.execute(
        text("""
            SELECT id, monto, plazo_meses, estado, id_socio
            FROM core_bancario.prestamo WHERE id = :id FOR UPDATE
        """),
        {"id": prestamo_id},
    )
    p = prestamo.mappings().first()
    if not p:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if p["estado"] not in ("SOLICITADO", "EN_REVISION"):
        raise HTTPException(status_code=400, detail="Préstamo ya evaluado")

    if user.tipo == "socio" and p["id_socio"] != user.socio_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    score = await calcular_score(db, p["id_socio"], p["monto"])
    aprobado = score >= SCORE_MINIMO and p["monto"] <= MONTO_MAX_AUTO

    if user.tipo == "empleado" and user.rol in ROLES_GERENTE:
        aprobado = True
        score = max(score, SCORE_MINIMO)

    if aprobado:
        await db.execute(
            text("""
                UPDATE core_bancario.prestamo
                SET estado = 'APROBADO', fecha_aprobacion = NOW(), id_usuario_aprobador = :uid
                WHERE id = :id
            """),
            {"id": prestamo_id, "uid": user.usuario_id or 3},
        )
        await generar_cuotas(db, prestamo_id, p["monto"], p["plazo_meses"])
        estado = EstadoPrestamo.APROBADO
        mensaje = f"Aprobado automáticamente. Score: {score:.1f}"
    else:
        await db.execute(
            text("UPDATE core_bancario.prestamo SET estado = 'RECHAZADO' WHERE id = :id"),
            {"id": prestamo_id},
        )
        estado = EstadoPrestamo.RECHAZADO
        mensaje = f"Rechazado. Score: {score:.1f} (mínimo {SCORE_MINIMO})"

    await registrar_evento(
        db, id_usuario=user.usuario_id, accion="EVALUACION", modulo="prestamo",
        detalle=f"Préstamo {prestamo_id}: {mensaje}", ip_origen=ip,
    )
    await db.commit()
    return EvaluarPrestamoResponse(prestamo_id=prestamo_id, score=score, estado=estado, mensaje=mensaje)


@app.get("/prestamos/pendientes/count")
async def contar_pendientes(
    _: TokenPayload = Depends(require_roles("AUDITOR", "ADMIN_CORE", "GERENTE_SUCURSAL")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT COUNT(*) AS n FROM core_bancario.prestamo WHERE estado IN ('SOLICITADO', 'EN_REVISION')")
    )
    return {"pendientes": result.mappings().first()["n"]}
