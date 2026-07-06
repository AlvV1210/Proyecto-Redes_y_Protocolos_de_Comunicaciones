# Guía — Capa de Aplicación y Presentación

Esta guía complementa la [capa de datos](azure-setup.md) con los microservicios FastAPI, API Gateway Traefik y los canales web.

---

## Requisitos locales (Windows)

| Herramienta | Versión mínima |
|-------------|----------------|
| Docker Desktop | 24+ |
| Python | 3.11+ (`py -3`) |
| Node.js | 20 LTS |

---

## Despliegue completo con Docker (recomendado)

```powershell
cd "d:\2026-01\Redes y Protocolos\docker"

# Detener contenedores de prueba manuales si los creó antes
docker rm -f banca-test cajas-test dash-test traefik 2>$null

docker compose -f docker-compose.yml -f docker-compose.app.yml -f docker-compose.dev.yml up -d --build

# Aplicar migraciones (PIN socios + passwords empleados)
.\scripts\apply-migrations.ps1

# Verificar
.\scripts\healthcheck-app.ps1
```

Esperar 3–5 minutos en el primer build.

### URLs locales

| Canal | URL principal | URL directa (dev) |
|-------|---------------|-------------------|
| **Banca Web** | http://localhost/web/ | http://localhost:8888/web/ |
| **Cajas** | http://localhost/cajas/ | http://localhost:8889/cajas/ |
| **Dashboard SBS** | http://localhost/dashboard/ | http://localhost:8890/dashboard/ |
| API Health | http://localhost/api/v1/auth/health | — |

> **Gateway:** Se usa **nginx-gateway** en puerto 80 (más fiable que Traefik en Docker Desktop Windows).

---

## Migración en BD existente

Si ya tenías el stack de datos corriendo **antes** de agregar la capa app, ejecuta manualmente:

```powershell
docker exec -i core-db psql -U coop_admin -d core_bancario < ..\database\05-socio-auth.sql
docker exec -i core-db psql -U coop_admin -d core_bancario < ..\database\06-update-passwords.sql
```

O recrea volúmenes: `docker compose down -v` (borra datos).

---

## Credenciales de prueba

### Empleados (Cajas / Dashboard)

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| cajero.lima | Coop2026! | CAJERO |
| gerente.chi | Coop2026! | GERENTE_SUCURSAL |
| auditor | Coop2026! | AUDITOR |
| admin.core | Coop2026! | ADMIN_CORE |

### Socios (Banca Web)

| DNI | PIN | Notas |
|-----|-----|-------|
| 45678901 | 8901 | María Quispe — últimos 4 del DNI |
| 12345678 | 5678 | Carlos Ramírez |

---

## Desarrollo local (hot reload)

### Terminal 1 — Datos + App con puertos expuestos

```powershell
cd docker
docker compose -f docker-compose.yml -f docker-compose.app.yml -f docker-compose.dev.yml up -d
```

### Terminal 2 — Frontends

```powershell
cd frontend/banca-web && npm install && npm run dev
cd frontend/cajas && npm install && npm start
cd frontend/dashboard-sbs && npm install && npm run dev
```

Los frontends en dev usan proxy a `http://localhost:80` para la API.

---

## Arquitectura de microservicios

```
Traefik :80
├── /api/v1/auth/*     → gateway-auth:8000
├── /api/v1/cuentas/*  → cuentas-svc:8001
├── /api/v1/prestamos/*→ prestamos-svc:8002
├── /api/v1/auditoria/*→ auditoria-svc:8003
├── /api/v1/sync/*     → sync-svc:8004
├── /web/*             → banca-web (nginx)
├── /cajas/*           → cajas-web (nginx)
└── /dashboard/*       → dashboard-sbs (nginx)
```

---

## Despliegue en Azure VM

1. Subir proyecto actualizado (SCP o git pull).
2. Abrir puerto **80** en NSG (ver [azure-setup.md](azure-setup.md)).
3. En la VM:

```bash
cd ~/cooperativa-pc3/docker
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d --build
bash scripts/healthcheck-app.sh
```

4. Acceder: `http://<IP_VM>/web/`

---

## Prueba integral

1. **Cajas**: login `cajero.lima` → depósito S/ 100 en cuenta `001-000001`.
2. **Banca Web**: login DNI `45678901` / PIN `8901` → ver saldo actualizado.
3. **Banca Web**: transferencia entre cuentas propias.
4. **Banca Web**: solicitar préstamo → evaluación automática por scoring.
5. **Dashboard**: login `auditor` → ver logs SBS y estado del Core.
6. **Failover**: `docker stop core-db` → dashboard muestra Core OFFLINE + evento en MongoDB.

---

## Referencia API

Ver [api-reference.md](api-reference.md).
