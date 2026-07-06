#!/bin/bash
# Agrega reglas pg_hba para replicacion en redes Docker
set -e
cat >> "$PGDATA/pg_hba.conf" <<EOF
host all all 172.28.0.0/16 scram-sha-256
host replication replicator 172.28.0.0/16 scram-sha-256
EOF
echo "pg_hba.conf actualizado para redes Docker."
