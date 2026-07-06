# Demo en Chrome — Capa de aplicación y presentación

## Iniciar el demo (un comando)

```powershell
cd "D:\2026-01\Redes y Protocolos\docker"
.\scripts\start-demo.ps1
```

Esto levanta Docker, aplica migraciones, verifica salud y abre Chrome en el portal de demo.

---

## URLs del demo

| Recurso | URL |
|---------|-----|
| **Portal demo** | http://localhost/ |
| **Banca Web** | http://localhost/web/ |
| **Dashboard Gerencial** | http://localhost/dashboard/ |
| **Lab simulación** | http://localhost/lab/ |
| Prometheus | http://localhost:9090 |
| pgAdmin | http://localhost:8080 |

---

## Credenciales

| Canal | Usuario | Contraseña/PIN |
|-------|---------|----------------|
| Banca Web | DNI `45678901` | PIN `8901` |
| Dashboard | `auditor` | `Coop2026!` |

---

## Demostración con pestaña Network (Chrome F12)

### 1. Preparar DevTools

1. Abrir http://localhost/
2. `F12` → pestaña **Network**
3. Marcar **Preserve log**
4. Filtrar por **Fetch/XHR**

### 2. Banca Web — flujo socio

1. Ir a http://localhost/web/
2. Login DNI + PIN → ver en Network:
   - `POST /api/v1/auth/socio/login` → respuesta JWT
3. Tras ingresar → ver:
   - `GET /api/v1/cuentas/cuentas/socio/1`
   - `GET /api/v1/cuentas/transacciones/recientes?socio_id=1`
4. Pestaña **Transferir** → `POST .../transacciones/transferencia`
5. Pestaña **Préstamo** → `POST .../prestamos/solicitar` y `POST .../prestamos/{id}/evaluar`

### 3. Dashboard Gerencial — flujo auditoría

1. Ir a http://localhost/dashboard/
2. Login auditor → `POST /api/v1/auth/login`
3. Tras ingresar → ver llamadas paralelas:
   - `GET /api/v1/auditoria/logs`
   - `GET /api/v1/auditoria/reportes/resumen`
   - `GET /api/v1/sync/estado/core`
   - `GET /api/v1/sync/estado/prometheus`
   - `GET /api/v1/prestamos/prestamos/pendientes/count`

### 4. Lab de simulación — conectividad y transferencia (sin tocar UI)

1. Ir a http://localhost/lab/
2. F12 → Network → Fetch/XHR
3. **Ejecutar prueba de conectividad** → `GET /api/v1/sync/diagnostico/conectividad`
4. **Ejecutar transferencia de datos** → `POST /api/v1/sync/diagnostico/transferencia`

Script CLI equivalente: `.\scripts\test-arquitectura.ps1`

### 5. Demo de resiliencia (opcional)

```powershell
docker stop core-db
```

Refrescar Dashboard → Core OFFLINE, pg_up = 0.

```powershell
docker start core-db
```

---

## Arquitectura expuesta en Network

```
Chrome → nginx-gateway :80
         ├── /api/v1/auth/*      → gateway-auth (JWT)
         ├── /api/v1/cuentas/*   → cuentas-svc
         ├── /api/v1/prestamos/* → prestamos-svc
         ├── /api/v1/auditoria/* → auditoria-svc
         ├── /api/v1/sync/*      → sync-svc
         ├── /web/*              → Banca Web (React)
         ├── /dashboard/*        → Dashboard (React)
         └── /lab/*              → Lab simulación (técnico)
```

---

## Detener el demo

```powershell
cd docker
docker compose -f docker-compose.yml -f docker-compose.app.yml -f docker-compose.dev.yml down
```
