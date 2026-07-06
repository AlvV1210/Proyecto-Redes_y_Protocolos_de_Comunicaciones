import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from coop_shared.config import settings
from coop_shared.database import get_db
from coop_shared.deps import ROLES_ADMIN, require_roles
from coop_shared.schemas import EstadoCoreResponse, EstadoPrometheusResponse, TokenPayload

from app.diagnostico import ejecutar_conectividad, ejecutar_transferencia

app = FastAPI(title="Sync y Resiliencia", version="1.0.0", root_path="/api/v1/sync")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_mongo():
    client = MongoClient(settings.mongo_host, settings.mongo_port, serverSelectionTimeoutMS=5000)
    return client[settings.mongo_db]


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sync-svc"}


@app.get("/diagnostico/conectividad")
async def diagnostico_conectividad():
    """Simulación: prueba de conectividad de toda la arquitectura (sin autenticación)."""
    return await ejecutar_conectividad()


@app.post("/diagnostico/transferencia")
async def diagnostico_transferencia(via_gateway: bool = True):
    """Simulación: prueba de transferencia de datos por el servidor web y capas internas."""
    return await ejecutar_transferencia(via_gateway=via_gateway)


@app.get("/estado/core", response_model=EstadoCoreResponse)
async def estado_core(
    _: TokenPayload = Depends(require_roles(*ROLES_ADMIN, "AUDITOR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        await db.execute(text("SELECT 1"))
        return EstadoCoreResponse(disponible=True, mensaje="PostgreSQL Core operativo")
    except Exception as exc:
        return EstadoCoreResponse(disponible=False, mensaje=str(exc))


@app.get("/estado/prometheus", response_model=EstadoPrometheusResponse)
async def estado_prometheus(
    _: TokenPayload = Depends(require_roles(*ROLES_ADMIN, "AUDITOR")),
):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.prometheus_url}/api/v1/query",
                params={"query": "pg_up"},
            )
            data = resp.json()
            value = None
            if data.get("data", {}).get("result"):
                value = float(data["data"]["result"][0]["value"][1])
            return EstadoPrometheusResponse(pg_up=value, disponible=value == 1.0 if value is not None else False)
    except Exception:
        return EstadoPrometheusResponse(pg_up=None, disponible=False)


@app.get("/contingencia/transacciones")
async def contingencia_transacciones(
    limit: int = 20,
    _: TokenPayload = Depends(require_roles(*ROLES_ADMIN, "AUDITOR")),
):
    try:
        db = get_mongo()
        docs = list(db.transacciones_respaldo.find().sort("transaccion_id", -1).limit(limit))
        for d in docs:
            d["_id"] = str(d["_id"])
        return {"total": len(docs), "transacciones": docs}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB no disponible: {exc}")


@app.get("/contingencia/eventos-failover")
async def eventos_failover(
    limit: int = 10,
    _: TokenPayload = Depends(require_roles(*ROLES_ADMIN, "AUDITOR")),
):
    try:
        db = get_mongo()
        docs = list(db.eventos_failover.find().sort("fecha", -1).limit(limit))
        for d in docs:
            d["_id"] = str(d["_id"])
        return {"eventos": docs}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB no disponible: {exc}")
