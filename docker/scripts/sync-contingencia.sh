#!/bin/bash
# Sincroniza transacciones recientes del Core PostgreSQL hacia MongoDB Contingencia
# Simula el respaldo NoSQL para failover (SRV-Contingencia)
set -e

CORE_HOST="${CORE_HOST:-core-db}"
CORE_PORT="${CORE_PORT:-5432}"
CORE_USER="${CORE_USER:-coop_admin}"
CORE_PASSWORD="${CORE_PASSWORD:-core_pass_2026}"
CORE_DB="${CORE_DB:-core_bancario}"
MONGO_HOST="${MONGO_HOST:-contingencia-db}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_DB="${MONGO_DB:-contingencia_coop}"
SYNC_INTERVAL="${SYNC_INTERVAL:-300}"

export PGPASSWORD="$CORE_PASSWORD"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

sync_transacciones() {
    log "Iniciando sincronización Core → MongoDB contingencia..."

    # Exportar transacciones como JSON
    RESULT=$(psql -h "$CORE_HOST" -p "$CORE_PORT" -U "$CORE_USER" -d "$CORE_DB" -t -A -c "
        SELECT json_agg(row_to_json(t))
        FROM (
            SELECT
                tr.id AS transaccion_id,
                tr.monto,
                tr.tipo::TEXT,
                tr.estado::TEXT,
                tr.descripcion,
                tr.fecha_operacion,
                co.numero_cuenta AS cuenta_origen,
                cd.numero_cuenta AS cuenta_destino,
                u.username AS usuario,
                s.nombre AS sede_origen,
                NOW() AS fecha_sync
            FROM core_bancario.transaccion tr
            LEFT JOIN core_bancario.cuenta co ON co.id = tr.id_cuenta_origen
            LEFT JOIN core_bancario.cuenta cd ON cd.id = tr.id_cuenta_destino
            LEFT JOIN core_bancario.usuario u ON u.id = tr.id_usuario
            LEFT JOIN core_bancario.sede s ON s.id = tr.id_sede_origen
            ORDER BY tr.id DESC
            LIMIT 100
        ) t;
    " 2>/dev/null || echo "null")

    if [ "$RESULT" = "null" ] || [ -z "$RESULT" ]; then
        log "No hay transacciones para sincronizar o Core no disponible."
        return 1
    fi

    # Insertar/actualizar en MongoDB via mongosh
    mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" --quiet --eval "
        const docs = $RESULT;
        if (docs && docs.length > 0) {
            docs.forEach(doc => {
                db.getSiblingDB('$MONGO_DB').transacciones_respaldo.updateOne(
                    { transaccion_id: doc.transaccion_id },
                    { \$set: doc },
                    { upsert: true }
                );
            });
            db.getSiblingDB('$MONGO_DB').metadata_sync.updateOne(
                { descripcion: 'Contingencia Cooperativa Financiera PC3' },
                { \$set: { ultima_sync: new Date(), registros_sync: docs.length } }
            );
            print('Sync OK: ' + docs.length + ' transacciones');
        }
    " 2>/dev/null

    log "Sincronización completada."
    return 0
}

check_core_health() {
    pg_isready -h "$CORE_HOST" -p "$CORE_PORT" -U "$CORE_USER" -d "$CORE_DB" -q 2>/dev/null
}

# Modo daemon: sincronización periódica
if [ "$1" = "daemon" ]; then
    log "Iniciando servicio de sincronización (intervalo: ${SYNC_INTERVAL}s)..."
    while true; do
        if check_core_health; then
            sync_transacciones || true
        else
            log "ALERTA: Core no disponible. Registrando evento de failover en MongoDB..."
            mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" --quiet --eval "
                db.getSiblingDB('$MONGO_DB').eventos_failover.insertOne({
                    evento: 'CORE_NO_DISPONIBLE',
                    fecha: new Date(),
                    accion: 'Modo contingencia activo - consultar transacciones_respaldo',
                    origen: 'sync-contingencia'
                });
            " 2>/dev/null || true
        fi
        sleep "$SYNC_INTERVAL"
    done
else
    sync_transacciones
fi
