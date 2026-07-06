# Referencia API — Cooperativa PC3

Base URL: `http://<host>/api/v1`

Autenticación: header `Authorization: Bearer <token>`

---

## Auth (gateway-auth)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/login` | No | Login empleado `{username, password}` |
| POST | `/auth/socio/login` | No | Login socio `{dni, pin}` |
| GET | `/auth/health` | No | Healthcheck |

---

## Cuentas (cuentas-svc)

Prefijo Traefik: `/cuentas`

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| GET | `/cuentas/{id}` | Empleado/Socio | Consulta cuenta |
| GET | `/cuentas/socio/{socio_id}` | Empleado/Socio | Listar cuentas |
| GET | `/cuentas/numero/{numero}` | CAJERO+ | Buscar por número |
| GET | `/socios/dni/{dni}` | CAJERO+ | Buscar socio |
| POST | `/socios` | CAJERO+ | Registrar socio |
| POST | `/transacciones/deposito` | CAJERO+ | Depósito |
| POST | `/transacciones/retiro` | CAJERO+/Socio | Retiro |
| POST | `/transacciones/transferencia` | Socio | Transferencia (comisión 0.5% inter-sede) |
| POST | `/cuentas/{id}/bloquear` | GERENTE+ | Bloquear cuenta |
| GET | `/transacciones/recientes?socio_id=` | Empleado/Socio | Historial |

---

## Préstamos (prestamos-svc)

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| POST | `/prestamos/solicitar` | Socio | Nueva solicitud |
| GET | `/prestamos/{id}` | Empleado/Socio | Detalle + cuotas |
| GET | `/prestamos/socio/{socio_id}` | Empleado/Socio | Listar préstamos |
| POST | `/prestamos/{id}/evaluar` | Socio/Gerente | Motor de scoring |
| GET | `/prestamos/pendientes/count` | AUDITOR+ | Contador pendientes |

### Scoring académico

- Score base 100, penalización por deuda y monto/saldo, bonificación por antigüedad.
- Aprobación automática si score ≥ 70 y monto ≤ S/ 50,000.
- Gerente puede aprobar manualmente.

---

## Auditoría SBS 504-2021 (auditoria-svc)

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| GET | `/logs` | AUDITOR+ | Listado paginado con filtros |
| GET | `/logs/{id}` | AUDITOR+ | Detalle de evento |
| GET | `/reportes/resumen` | AUDITOR+ | Conteo por módulo/día |

---

## Sync y resiliencia (sync-svc)

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| GET | `/estado/core` | ADMIN | Health PostgreSQL |
| GET | `/estado/prometheus` | ADMIN/AUDITOR | Métrica pg_up |
| GET | `/contingencia/transacciones` | ADMIN/AUDITOR | Respaldo MongoDB |
| GET | `/contingencia/eventos-failover` | ADMIN/AUDITOR | Eventos de failover |

---

## Swagger por servicio (desarrollo)

Con `docker-compose.dev.yml`:

- Auth: http://localhost:8000/docs
- Cuentas: http://localhost:8001/docs
- Préstamos: http://localhost:8002/docs
- Auditoría: http://localhost:8003/docs
- Sync: http://localhost:8004/docs
