#!/usr/bin/env python3
"""Sincroniza transacciones del Core PostgreSQL hacia MongoDB Contingencia."""
import os
import sys
import time
import json
from datetime import datetime, timezone

try:
    import psycopg2
    import psycopg2.extras
    from pymongo import MongoClient
except ImportError:
    print("Instalar: pip install psycopg2-binary pymongo")
    sys.exit(1)

CORE_HOST = os.getenv("CORE_HOST", "core-db")
CORE_PORT = int(os.getenv("CORE_PORT", "5432"))
CORE_USER = os.getenv("CORE_USER", "coop_admin")
CORE_PASSWORD = os.getenv("CORE_PASSWORD", "core_pass_2026")
CORE_DB = os.getenv("CORE_DB", "core_bancario")
MONGO_HOST = os.getenv("MONGO_HOST", "contingencia-db")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "contingencia_coop")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "120"))


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def get_pg_connection():
    return psycopg2.connect(
        host=CORE_HOST, port=CORE_PORT,
        user=CORE_USER, password=CORE_PASSWORD, dbname=CORE_DB
    )


def get_mongo_db():
    client = MongoClient(MONGO_HOST, MONGO_PORT, serverSelectionTimeoutMS=5000)
    return client[MONGO_DB]


def check_core_health():
    try:
        conn = get_pg_connection()
        conn.close()
        return True
    except Exception:
        return False


def sync_transacciones():
    log("Iniciando sincronización Core → MongoDB contingencia...")
    conn = get_pg_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            tr.id AS transaccion_id,
            tr.monto::float AS monto,
            tr.tipo::text AS tipo,
            tr.estado::text AS estado,
            tr.descripcion,
            tr.fecha_operacion,
            co.numero_cuenta AS cuenta_origen,
            cd.numero_cuenta AS cuenta_destino,
            u.username AS usuario,
            s.nombre AS sede_origen
        FROM core_bancario.transaccion tr
        LEFT JOIN core_bancario.cuenta co ON co.id = tr.id_cuenta_origen
        LEFT JOIN core_bancario.cuenta cd ON cd.id = tr.id_cuenta_destino
        LEFT JOIN core_bancario.usuario u ON u.id = tr.id_usuario
        LEFT JOIN core_bancario.sede s ON s.id = tr.id_sede_origen
        ORDER BY tr.id DESC
        LIMIT 100
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        log("No hay transacciones para sincronizar.")
        return 0

    db = get_mongo_db()
    count = 0
    for row in rows:
        doc = dict(row)
        if doc.get("fecha_operacion"):
            doc["fecha_operacion"] = doc["fecha_operacion"].isoformat()
        doc["fecha_sync"] = datetime.now(timezone.utc).isoformat()
        db.transacciones_respaldo.update_one(
            {"transaccion_id": doc["transaccion_id"]},
            {"$set": doc},
            upsert=True
        )
        count += 1

    db.metadata_sync.update_one(
        {"descripcion": "Contingencia Cooperativa Financiera PC3"},
        {"$set": {"ultima_sync": datetime.now(timezone.utc), "registros_sync": count}},
        upsert=True
    )
    log(f"Sincronización completada: {count} transacciones.")
    return count


def register_failover_event():
    db = get_mongo_db()
    db.eventos_failover.insert_one({
        "evento": "CORE_NO_DISPONIBLE",
        "fecha": datetime.now(timezone.utc),
        "accion": "Modo contingencia activo - consultar transacciones_respaldo",
        "origen": "sync-contingencia"
    })
    log("ALERTA: Core no disponible. Evento de failover registrado en MongoDB.")


def main():
    daemon = len(sys.argv) > 1 and sys.argv[1] == "daemon"
    if not daemon:
        try:
            sync_transacciones()
        except Exception as e:
            log(f"Error: {e}")
            sys.exit(1)
        return

    log(f"Iniciando servicio de sincronización (intervalo: {SYNC_INTERVAL}s)...")
    # Esperar a que Core esté listo tras el arranque del stack
    for attempt in range(30):
        if check_core_health():
            break
        log(f"Esperando Core... intento {attempt + 1}/30")
        time.sleep(5)

    while True:
        try:
            if check_core_health():
                sync_transacciones()
            else:
                register_failover_event()
        except Exception as e:
            log(f"Error en ciclo de sync: {e}")
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
