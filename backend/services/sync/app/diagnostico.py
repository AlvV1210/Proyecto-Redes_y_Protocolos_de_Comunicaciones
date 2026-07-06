"""Pruebas de conectividad y transferencia de datos — capa de simulación técnica."""

import time
from datetime import datetime, timezone

import httpx
import redis
from pymongo import MongoClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from coop_shared.config import settings

SERVICIOS_APP = [
    ("gateway-auth", "http://gateway-auth:8000/health", "API Gateway / Auth"),
    ("cuentas-svc", "http://cuentas-svc:8001/health", "Cuentas y Transacciones"),
    ("prestamos-svc", "http://prestamos-svc:8002/health", "Scoring Préstamos"),
    ("auditoria-svc", "http://auditoria-svc:8003/health", "Auditoría SBS"),
    ("sync-svc", "http://sync-svc:8004/health", "Sync y Resiliencia"),
]

CANALES_WEB = [
    ("banca-web", "http://banca-web:80/web/", "Banca Web (React)"),
    ("dashboard-sbs", "http://dashboard-sbs:80/dashboard/", "Dashboard Gerencial"),
]


async def _probe_http(url: str, timeout: float = 5.0) -> dict:
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            ok = resp.status_code < 400
            return {
                "estado": "OK" if ok else "FALLO",
                "codigo_http": resp.status_code,
                "latencia_ms": ms,
                "detalle": resp.text[:120] if not ok else "Respuesta HTTP válida",
            }
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {"estado": "FALLO", "codigo_http": None, "latencia_ms": ms, "detalle": str(exc)}


async def _probe_postgres(host: str, label: str) -> dict:
    t0 = time.perf_counter()
    url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{host}:{settings.postgres_port}/{settings.postgres_db}"
    )
    try:
        eng = create_async_engine(url, pool_pre_ping=True)
        factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            r = await session.execute(text("SELECT 1 AS ping"))
            row = r.scalar()
            recovery = await session.execute(text("SELECT pg_is_in_recovery()"))
            in_recovery = recovery.scalar()
            count = await session.execute(text("SELECT COUNT(*) FROM core_bancario.transaccion"))
            tx_count = count.scalar()
        await eng.dispose()
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": label,
            "host": host,
            "estado": "OK",
            "latencia_ms": ms,
            "modo_replica": bool(in_recovery),
            "transacciones": tx_count,
            "detalle": f"ping={row}, recovery={in_recovery}",
        }
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": label,
            "host": host,
            "estado": "FALLO",
            "latencia_ms": ms,
            "detalle": str(exc),
        }


def _probe_mongo() -> dict:
    t0 = time.perf_counter()
    try:
        client = MongoClient(settings.mongo_host, settings.mongo_port, serverSelectionTimeoutMS=5000)
        db = client[settings.mongo_db]
        client.admin.command("ping")
        tx_docs = db.transacciones_respaldo.count_documents({})
        failover_docs = db.eventos_failover.count_documents({})
        client.close()
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": "contingencia-db",
            "host": f"{settings.mongo_host}:{settings.mongo_port}",
            "estado": "OK",
            "latencia_ms": ms,
            "transacciones_respaldo": tx_docs,
            "eventos_failover": failover_docs,
        }
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": "contingencia-db",
            "host": f"{settings.mongo_host}:{settings.mongo_port}",
            "estado": "FALLO",
            "latencia_ms": ms,
            "detalle": str(exc),
        }


def _probe_redis() -> dict:
    t0 = time.perf_counter()
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=5)
        pong = r.ping()
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": "redis",
            "host": settings.redis_url,
            "estado": "OK" if pong else "FALLO",
            "latencia_ms": ms,
            "detalle": "PING→PONG",
        }
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": "redis",
            "host": settings.redis_url,
            "estado": "FALLO",
            "latencia_ms": ms,
            "detalle": str(exc),
        }


async def _probe_prometheus() -> dict:
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health = await client.get(f"{settings.prometheus_url}/-/healthy")
            query = await client.get(
                f"{settings.prometheus_url}/api/v1/query",
                params={"query": "pg_up"},
            )
            data = query.json()
            pg_up = None
            if data.get("data", {}).get("result"):
                pg_up = float(data["data"]["result"][0]["value"][1])
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": "prometheus",
            "host": settings.prometheus_url,
            "estado": "OK" if health.status_code == 200 else "FALLO",
            "latencia_ms": ms,
            "pg_up": pg_up,
            "detalle": f"pg_up={pg_up}",
        }
    except Exception as exc:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "nodo": "prometheus",
            "host": settings.prometheus_url,
            "estado": "FALLO",
            "latencia_ms": ms,
            "detalle": str(exc),
        }


async def ejecutar_conectividad() -> dict:
    presentacion = []
    for nombre, url, desc in CANALES_WEB:
        r = await _probe_http(url)
        presentacion.append({"nodo": nombre, "descripcion": desc, "url": url, **r})

    aplicacion = []
    for nombre, url, desc in SERVICIOS_APP:
        r = await _probe_http(url)
        aplicacion.append({"nodo": nombre, "descripcion": desc, "url": url, **r})

    datos = [
        await _probe_postgres(settings.postgres_host, "core-db"),
        await _probe_postgres(settings.postgres_replica_host, "replica-db"),
        _probe_mongo(),
        _probe_redis(),
        await _probe_prometheus(),
    ]

    todos = presentacion + aplicacion + datos
    ok = sum(1 for n in todos if n.get("estado") == "OK")
    fallo = len(todos) - ok

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": "prueba_conectividad",
        "capas": {
            "presentacion": {
                "descripcion": "Servidor web nginx y canales React (sin afectar UI de usuario)",
                "nodos": presentacion,
            },
            "aplicacion": {
                "descripcion": "Microservicios FastAPI / ASGI",
                "nodos": aplicacion,
            },
            "datos": {
                "descripcion": "PostgreSQL Core/Réplica, MongoDB contingencia, Redis, Prometheus",
                "nodos": datos,
            },
        },
        "resumen": {"total": len(todos), "ok": ok, "fallo": fallo, "porcentaje_ok": round(ok / len(todos) * 100, 1)},
    }


async def ejecutar_transferencia(via_gateway: bool = True) -> dict:
    """Simula flujo de transferencia de datos a través de la arquitectura."""
    pasos = []
    total_bytes = 0

    gateway_urls = [
        ("GET", "http://nginx-gateway/api/v1/auth/health", "Cliente → Nginx → Gateway Auth"),
        ("GET", "http://nginx-gateway/api/v1/cuentas/health", "Cliente → Nginx → Cuentas SVC"),
        ("GET", "http://nginx-gateway/api/v1/sync/health", "Cliente → Nginx → Sync SVC"),
    ] if via_gateway else [
        ("GET", "http://gateway-auth:8000/api/v1/auth/health", "Sync → Gateway Auth (red interna)"),
        ("GET", "http://cuentas-svc:8001/health", "Sync → Cuentas SVC (red interna)"),
    ]

    for metodo, url, desc in gateway_urls:
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.request(metodo, url)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            nbytes = len(resp.content)
            total_bytes += nbytes
            pasos.append({
                "paso": len(pasos) + 1,
                "flujo": desc,
                "metodo": metodo,
                "url": url.replace("http://nginx-gateway", "http://localhost"),
                "estado": "OK" if resp.status_code < 400 else "FALLO",
                "codigo_http": resp.status_code,
                "bytes_transferidos": nbytes,
                "latencia_ms": ms,
            })
        except Exception as exc:
            ms = round((time.perf_counter() - t0) * 1000, 1)
            pasos.append({
                "paso": len(pasos) + 1,
                "flujo": desc,
                "metodo": metodo,
                "url": url.replace("http://nginx-gateway", "http://localhost"),
                "estado": "FALLO",
                "latencia_ms": ms,
                "detalle": str(exc),
            })

    core = await _probe_postgres(settings.postgres_host, "core-db")
    replica = await _probe_postgres(settings.postgres_replica_host, "replica-db")
    mongo = _probe_mongo()

    sync_ok = (
        core.get("estado") == "OK"
        and replica.get("estado") == "OK"
        and core.get("transacciones") == replica.get("transacciones")
    )
    pasos.append({
        "paso": len(pasos) + 1,
        "flujo": "Core PostgreSQL → lectura transacciones",
        "estado": core.get("estado", "FALLO"),
        "registros": core.get("transacciones"),
        "latencia_ms": core.get("latencia_ms"),
    })
    pasos.append({
        "paso": len(pasos) + 1,
        "flujo": "Réplica PostgreSQL → replicación streaming",
        "estado": "OK" if sync_ok else "ADVERTENCIA",
        "registros_core": core.get("transacciones"),
        "registros_replica": replica.get("transacciones"),
        "replica_en_standby": replica.get("modo_replica"),
        "latencia_ms": replica.get("latencia_ms"),
        "detalle": "Réplica sincronizada" if sync_ok else "Conteos difieren o réplica no disponible",
    })
    pasos.append({
        "paso": len(pasos) + 1,
        "flujo": "Core → MongoDB contingencia (respaldo NoSQL)",
        "estado": mongo.get("estado", "FALLO"),
        "documentos_respaldo": mongo.get("transacciones_respaldo"),
        "latencia_ms": mongo.get("latencia_ms"),
    })

    ok = sum(1 for p in pasos if p.get("estado") == "OK")
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": "prueba_transferencia_datos",
        "via_servidor_web": via_gateway,
        "pasos": pasos,
        "resumen": {
            "pasos_total": len(pasos),
            "pasos_ok": ok,
            "bytes_http_acumulados": total_bytes,
            "latencia_total_ms": round(sum(p.get("latencia_ms", 0) for p in pasos), 1),
        },
    }
