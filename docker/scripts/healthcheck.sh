#!/bin/bash
# Healthcheck del stack PC3
set -e

echo "=== PC3 Cooperativa - Health Check ==="
echo ""

echo "[1/5] Contenedores activos:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "[2/5] Core PostgreSQL:"
docker exec core-db pg_isready -U coop_admin -d core_bancario && echo "  OK - Core respondiendo" || echo "  FALLO"
echo ""

echo "[3/5] Réplica PostgreSQL:"
RECOVERY=$(docker exec replica-db psql -U coop_admin -d core_bancario -t -A -c "SELECT pg_is_in_recovery();" 2>/dev/null || echo "error")
if [ "$RECOVERY" = "t" ]; then
    echo "  OK - Réplica en modo standby (solo lectura)"
    REPLICA_COUNT=$(docker exec replica-db psql -U coop_admin -d core_bancario -t -A -c "SELECT COUNT(*) FROM core_bancario.transaccion;" 2>/dev/null)
    echo "  Transacciones replicadas: $REPLICA_COUNT"
else
    echo "  ADVERTENCIA - Réplica no en modo recovery: $RECOVERY"
fi
echo ""

echo "[4/5] MongoDB Contingencia:"
MONGO_COUNT=$(docker exec contingencia-db mongosh --quiet --eval "db.getSiblingDB('contingencia_coop').transacciones_respaldo.countDocuments()" 2>/dev/null || echo "0")
echo "  Documentos en contingencia: $MONGO_COUNT"
echo ""

echo "[5/5] Prometheus:"
curl -sf http://localhost:9090/-/healthy >/dev/null && echo "  OK - Prometheus activo" || echo "  FALLO"
PG_UP=$(curl -sf "http://localhost:9090/api/v1/query?query=pg_up" 2>/dev/null | grep -o '"value":\[[^]]*\]' | head -1 || echo "N/A")
echo "  Métrica pg_up: $PG_UP"
echo ""

echo "=== Redes Docker (segmentación) ==="
docker network ls --filter "name=coop" --format "table {{.Name}}\t{{.Driver}}"
echo ""

echo "=== Fin Health Check ==="
