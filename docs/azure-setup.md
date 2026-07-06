# Guía de despliegue en Azure for Students

Esta guía describe paso a paso cómo desplegar la capa de datos PC3 en Azure for Students, minimizando el consumo de créditos.

---

## Paso 1: Crear la Virtual Machine

1. Ingresar a [https://portal.azure.com](https://portal.azure.com) con cuenta **Azure for Students**.
2. Buscar **Virtual machines** → **Create** → **Azure virtual machine**.
3. Configurar:

| Campo | Valor recomendado |
|-------|-------------------|
| Resource group | `rg-cooperativa-pc3` (crear nuevo) |
| VM name | `vm-cooperativa-pc3` |
| Region | `East US` o `Brazil South` (menor latencia desde Perú) |
| Image | Ubuntu Server 22.04 LTS - x64 Gen2 | -> funciono con 24.04
| Size | `Standard_B2s` (2 vCPU, 4 GB) o `Standard_B1s` si el crédito es limitado |
| Authentication | SSH public key (recomendado) |
| Public inbound ports | **Allow selected ports** → solo **SSH (22)** |

4. **Disks:** OS disk 30 GB Standard SSD (suficiente).
5. Crear la VM y anotar la **IP pública**.

**Evidencia 01:** Captura de la VM creada mostrando nombre, región y tamaño.

---

## Paso 2: Configurar Network Security Group (NSG)

En la VM → **Networking** → **Network settings** → **Create port rule**(Inbound port rule):

| Prioridad | Nombre | Puerto | Protocolo | Origen | Acción |
|-----------|--------|--------|-----------|--------|--------|
| 100 | Allow-SSH | 22 | TCP | Tu IP pública | Allow |
| 110 | Allow-pgAdmin | 8080 | TCP | Tu IP pública | Allow |
| 120 | Allow-Prometheus | 9090 | TCP | Tu IP pública | Allow |
| 130 | Allow-API | 80 | TCP | Tu IP pública | Allow |
| 140 | Allow-HTTPS | 443 | TCP | Tu IP pública | Allow (opcional) |

**No abrir** los puertos 5432, 8001–8004 ni 27017. La API y los frontends se acceden solo por el puerto 80 vía Traefik.

**Evidencia 02:** Captura del NSG con las reglas. Explicación: *"Equivalente académico a las ACLs del TB1: solo tráfico administrativo autorizado desde IP del operador."*

---

## Paso 3: Conectar por SSH e instalar Docker

```bash
ssh -i ~/.ssh/tu_clave azureuser@<IP_PUBLICA_VM>
```

En la VM:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

**Evidencia 03:** Salida de `docker --version` y `docker ps` (vacío).

---

## Paso 4: Subir el proyecto a la VM

### Opción A: Git (si el repo está en GitHub)

```bash
git clone <URL_DEL_REPOSITORIO> cooperativa-pc3
cd cooperativa-pc3/docker
```

### Opción B: SCP desde tu PC (Windows PowerShell) SCP (por sus siglas en inglés, Secure Copy Protocol) es un comando de red que permite transferir archivos de forma segura entre un equipo local  y un servidor remoto

```powershell
scp -i C:\Users\ALVARO\.ssh\tu_clave -r "d:\2026-01\Redes y Protocolos" azureuser@<IP_VM>:~/cooperativa-pc3
```

```powershell
scp -r "d:\2026-01\Redes y Protocolos" userCooperativa@40.76.120.55:~/cooperativa-pc3
```

En la VM:

```bash
cd ~/cooperativa-pc3/docker
```

---

## Paso 5: Desplegar el stack Docker

```bash
docker compose up -d --build
```

Esperar 2–3 minutos. La réplica tarda más en inicializarse (pg_basebackup).

Verificar:

```bash
docker compose ps
bash scripts/healthcheck.sh
```

**Evidencia 04:** Salida de `docker compose ps` mostrando 7 contenedores (4 principales + pgAdmin, exporter, sync).

**Evidencia 05:** Salida de healthcheck confirmando:
- Core OK
- Réplica en modo standby (`pg_is_in_recovery = true`)
- MongoDB con documentos sincronizados
- Prometheus activo

---

## Paso 6: Verificar segmentación de redes Docker

```bash
docker network ls | grep coop
docker network inspect coop_net_contingencia --format '{{.Internal}}'
```

Debe mostrar `true` para la red de contingencia (Zero Trust simulado).

**Evidencia 06:** Captura de redes Docker + explicación de equivalencia con microsegmentación del TB1.

---

## Paso 7: Configurar pgAdmin y generar diagrama ERD

1. Abrir en navegador: `http://<IP_VM>:8080`
2. Login: `admin@coop.pe` / `admin2026`
3. **Add New Server:**
   - General → Name: `SRV-CoreBancario`
   - Connection → Host: `core-db`, Port: `5432`, User: `coop_admin`, Password: `core_pass_2026`, Database: `core_bancario`
4. Expandir: Servers → SRV-CoreBancario → Databases → core_bancario → Schemas → core_bancario
5. **Tools → ERD Tool** (clic derecho en schema `core_bancario`)
6. Exportar como PNG/PDF

**Evidencia 07:** Diagrama ERD exportado desde pgAdmin (validación técnica).

---

## Paso 8: Verificar replicación Core → Réplica

```bash
# Insertar transacción en Core
docker exec core-db psql -U coop_admin -d core_bancario -c "
INSERT INTO core_bancario.transaccion (monto, tipo, estado, descripcion, id_cuenta_destino, id_usuario, id_sede_origen)
VALUES (500.00, 'DEPOSITO', 'COMPLETADA', 'Prueba replicacion Azure', 1, 2, 3);"

# Verificar en Réplica (solo lectura)
docker exec replica-db psql -U coop_admin -d core_bancario -c "
SELECT id, monto, descripcion FROM core_bancario.transaccion ORDER BY id DESC LIMIT 1;"

docker exec replica-db psql -U coop_admin -d core_bancario -c "
SELECT pg_is_in_recovery();"
```

**Evidencia 08:** Misma transacción visible en Core y Réplica; `pg_is_in_recovery = t`.

---

## Paso 9: Verificar contingencia MongoDB

```bash
docker exec contingencia-db mongosh contingencia_coop --quiet --eval "
db.transacciones_respaldo.countDocuments();
db.transacciones_respaldo.find().sort({transaccion_id:-1}).limit(3).pretty();"
```

**Evidencia 09:** Documentos JSON de transacciones sincronizadas desde Core.

---

## Paso 10: Verificar monitoreo Prometheus

1. Abrir: `http://<IP_VM>:9090`
2. Ir a **Status → Targets** → verificar `postgres_core` UP
3. Consultar métrica: `pg_up` (debe ser 1)
4. Ir a **Alerts** para ver reglas configuradas

**Evidencia 10:** Captura de Prometheus con target UP y métrica pg_up=1.

---

## Paso 11: Ejecutar escenarios de demostración

```bash
docker exec -i core-db psql -U coop_admin -d core_bancario < ../database/04-demo-queries.sql
```

Documentar cada escenario con captura y descripción breve (ver [`../database/04-demo-queries.sql`](../database/04-demo-queries.sql)).

---

## Paso 12: Simular failover

```bash
# Detener Core
docker stop core-db

# Esperar 2 minutos (sync-contingencia registra evento)
docker exec contingencia-db mongosh contingencia_coop --eval "
db.eventos_failover.find().sort({fecha:-1}).limit(1).pretty();"

# Ver alerta en Prometheus: http://<IP>:9090/alerts

# Restaurar Core
docker start core-db
```

**Evidencia 11:** Evento de failover en MongoDB + alerta CoreDatabaseDown en Prometheus.

---

## Paso 13: Apagar para ahorrar créditos

Cuando no uses la VM:

```bash
docker compose down
exit
```

En portal Azure:
1. VM → **Stop** (deallocate) — deja de consumir cómputo
2. Solo pagas almacenamiento del disco (~USD 1–2/mes)

---

## Checklist de evidencias para el informe

| # | Evidencia | Descripción |
|---|-----------|-------------|
| 01 | VM Azure creada | Infraestructura cloud simulada |
| 02 | NSG / reglas firewall | ACLs equivalentes |
| 03 | Docker instalado | Entorno de contenedores |
| 04 | docker compose ps | 4 contenedores principales activos |
| 05 | healthcheck.sh | Validación integral del stack |
| 06 | docker network inspect | Segmentación Zero Trust |
| 07 | ERD pgAdmin | Diagrama BD desde servidor real |
| 08 | Replicación PostgreSQL | Réplica sincronizada |
| 09 | MongoDB contingencia | Respaldo NoSQL operativo |
| 10 | Prometheus | Monitoreo y métricas |
| 11 | Failover simulado | Procedimiento de contingencia |

---

## Credenciales del stack (entorno académico)

| Servicio | Usuario | Contraseña |
|----------|---------|------------|
| PostgreSQL Core/Réplica | coop_admin | core_pass_2026 |
| Replicación | replicator | replica_pass_2026 |
| pgAdmin | admin@coop.pe | admin2026 |
| Usuarios app (seed) | ver seed.sql | Coop2026! |

> **Nota:** Cambiar contraseñas en producción. Estas credenciales son solo para demostración académica.

---

## Paso 14: Desplegar capa de aplicación y presentación

Tras completar la capa de datos, desplegar los microservicios FastAPI, Traefik y frontends:

```bash
cd ~/cooperativa-pc3/docker
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d --build
```

Si la BD ya existía antes de esta capa, aplicar migraciones:

```bash
docker exec -i core-db psql -U coop_admin -d core_bancario < ../database/05-socio-auth.sql
docker exec -i core-db psql -U coop_admin -d core_bancario < ../database/06-update-passwords.sql
```

Verificar:

```bash
bash scripts/healthcheck-app.sh
```

### URLs en la VM

| Canal | URL |
|-------|-----|
| Banca Web | `http://<IP_VM>/web/` |
| Cajas | `http://<IP_VM>/cajas/` |
| Dashboard SBS | `http://<IP_VM>/dashboard/` |
| API Login | `http://<IP_VM>/api/v1/auth/login` |

**Evidencia 12:** Captura de Banca Web con saldo visible tras depósito en Cajas.

**Evidencia 13:** Dashboard SBS con logs de auditoría y estado del Core.

### Recursos VM

La capa completa requiere **Standard_B2s (4 GB RAM)**. Con B1s, detener pgAdmin o réplica temporalmente.

Guía detallada: [app-setup.md](app-setup.md)
