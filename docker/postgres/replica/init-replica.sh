#!/bin/bash
# Script de inicializacion de la replica PostgreSQL
set -e

PRIMARY_HOST="${PRIMARY_HOST:-core-db}"
PRIMARY_PORT="${PRIMARY_PORT:-5432}"
REPLICATION_USER="${REPLICATION_USER:-replicator}"
REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-replica_pass_2026}"
POSTGRES_USER="${POSTGRES_USER:-coop_admin}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-core_pass_2026}"
POSTGRES_DB="${POSTGRES_DB:-core_bancario}"
PGDATA="/var/lib/postgresql/data"
export PGPASSWORD="$POSTGRES_PASSWORD"

echo "Esperando que el primario ($PRIMARY_HOST) este disponible..."
until pg_isready -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Primario no disponible, reintentando en 3s..."
    sleep 3
done

echo "Esperando schema en primario..."
until psql -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT 1 FROM core_bancario.sede LIMIT 1;" 2>/dev/null | grep -q 1; do
    echo "Schema aun no listo, reintentando en 5s..."
    sleep 5
done

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "Inicializando replica con pg_basebackup desde $PRIMARY_HOST..."
    rm -rf "$PGDATA"/*
    PGPASSWORD="$REPLICATION_PASSWORD" pg_basebackup \
        -h "$PRIMARY_HOST" \
        -p "$PRIMARY_PORT" \
        -U "$REPLICATION_USER" \
        -D "$PGDATA" \
        -Fp -Xs -P -R
    echo "Replica inicializada correctamente."
else
    echo "Datos de replica ya existen, iniciando..."
fi

exec /usr/local/bin/docker-entrypoint.sh postgres
