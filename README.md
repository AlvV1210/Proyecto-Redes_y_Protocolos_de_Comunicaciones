# PC3 — Cooperativa Financiera

Implementación académica de arquitectura bancaria híbrida sobre **Azure for Students** usando **1 VM + Docker**.

## Capas implementadas

| Capa | Componentes | Estado |
|------|-------------|--------|
| **Datos** | PostgreSQL Core/Réplica, MongoDB contingencia, Prometheus, sync worker | Completo |
| **Aplicación** | FastAPI microservicios (cuentas, préstamos, auditoría, sync) + Traefik + Redis | Completo |
| **Presentación** | Banca Web (React), Cajas (Angular), Dashboard SBS (React) | Completo |

## Inicio rápido

### Solo capa de datos

```bash
cd docker
docker compose up -d
```

### Stack completo (datos + app + frontends)

```bash
cd docker
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d --build
bash scripts/healthcheck-app.sh
```

### Accesos locales

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Banca Web | http://localhost/web/ | DNI 45678901 / PIN 8901 |
| Cajas | http://localhost/cajas/ | cajero.lima / Coop2026! |
| Dashboard SBS | http://localhost/dashboard/ | auditor / Coop2026! |
| pgAdmin | http://localhost:8080 | admin@coop.pe / admin2026 |
| Prometheus | http://localhost:9090 | — |

## Estructura del proyecto

```
Redes y Protocolos/
├── backend/           # Microservicios FastAPI + shared
├── frontend/          # banca-web, cajas, dashboard-sbs
├── docker/            # Compose, Traefik, scripts
├── database/          # SQL schema, seed, migraciones
├── docs/              # Guías Azure, app, API
└── diagrams/          # DER Mermaid
```

## Documentación

- [Guía Azure (capa datos)](docs/azure-setup.md)
- [Guía aplicación y presentación](docs/app-setup.md)
- [Referencia API](docs/api-reference.md)
- [DER y explicación normativa](docs/DER-explicacion.md)

## Apagar para ahorrar créditos Azure

```bash
docker compose -f docker-compose.yml -f docker-compose.app.yml down
# En portal Azure: Stop (deallocate) la VM
```
