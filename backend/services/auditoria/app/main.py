from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from coop_shared.database import get_db
from coop_shared.deps import ROLES_AUDITORIA, require_roles
from coop_shared.schemas import LogAuditoriaResponse, ResumenAuditoriaItem, TokenPayload

app = FastAPI(title="Auditoría SBS 504-2021", version="1.0.0", root_path="/api/v1/auditoria")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auditoria-svc"}


@app.get("/logs", response_model=list[LogAuditoriaResponse])
async def listar_logs(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    modulo: Optional[str] = None,
    accion: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: TokenPayload = Depends(require_roles(*ROLES_AUDITORIA)),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    conditions = ["1=1"]
    params: dict = {"limit": page_size, "offset": offset}
    if fecha_desde:
        conditions.append("fecha_hora::date >= :desde")
        params["desde"] = fecha_desde
    if fecha_hasta:
        conditions.append("fecha_hora::date <= :hasta")
        params["hasta"] = fecha_hasta
    if modulo:
        conditions.append("modulo ILIKE :modulo")
        params["modulo"] = f"%{modulo}%"
    if accion:
        conditions.append("accion ILIKE :accion")
        params["accion"] = f"%{accion}%"

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"""
            SELECT id, id_usuario, accion, modulo, detalle,
                   host(ip_origen) AS ip_origen, fecha_hora
            FROM core_bancario.log_auditoria
            WHERE {where}
            ORDER BY fecha_hora DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    return [LogAuditoriaResponse(**r) for r in result.mappings()]


@app.get("/logs/{log_id}", response_model=LogAuditoriaResponse)
async def obtener_log(
    log_id: int,
    _: TokenPayload = Depends(require_roles(*ROLES_AUDITORIA)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT id, id_usuario, accion, modulo, detalle,
                   host(ip_origen) AS ip_origen, fecha_hora
            FROM core_bancario.log_auditoria WHERE id = :id
        """),
        {"id": log_id},
    )
    row = result.mappings().first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log no encontrado")
    return LogAuditoriaResponse(**row)


@app.get("/reportes/resumen", response_model=list[ResumenAuditoriaItem])
async def resumen_auditoria(
    _: TokenPayload = Depends(require_roles(*ROLES_AUDITORIA)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT modulo, COUNT(*) AS total, fecha_hora::date AS fecha
            FROM core_bancario.log_auditoria
            WHERE fecha_hora >= NOW() - INTERVAL '30 days'
            GROUP BY modulo, fecha_hora::date
            ORDER BY fecha DESC, total DESC
            LIMIT 100
        """)
    )
    return [ResumenAuditoriaItem(**r) for r in result.mappings()]
