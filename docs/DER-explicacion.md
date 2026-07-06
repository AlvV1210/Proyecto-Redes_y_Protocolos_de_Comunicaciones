# Diagrama Entidad-Relación — Core Bancario Cooperativa Financiera

## Figura DER

El diagrama fuente está en [`../diagrams/DER-cooperativa.mmd`](../diagrams/DER-cooperativa.mmd). Puede renderizarse con Mermaid Live Editor o exportarse como PNG para el informe.

---

## Explicación del modelo de datos

En la figura anterior se muestra el diagrama entidad-relación (DER) de la base de datos del **Core Bancario** de la cooperativa financiera peruana. Este modelo organiza la información crítica de socios, cuentas, transacciones, préstamos, usuarios del sistema y equipos de red, y cumple con las exigencias técnicas y normativas planteadas en el proyecto PC3.

### Entidad central: SOCIO

La entidad **Socio** representa a los aproximadamente 50,000 miembros de la cooperativa distribuidos entre las sedes de Lima, Chiclayo y Arequipa. Cada socio se identifica por su `dni` (8 dígitos, validado con constraint), y almacena datos personales mínimos (`nombres`, `apellidos`, `email`, `telefono`) vinculados a una `id_sede` que permite rastrear en qué sucursal fue registrado. Esta trazabilidad es esencial para cumplir con la **Ley N° 29733** (Protección de Datos Personales), que exige tratar solo los datos necesarios y asociarlos a un responsable de tratamiento por sede.

La relación **1:N** entre Sede y Socio permite que cada sucursal regional gestione el alta de socios sin saturar el servidor central, mientras el Core consolida la información.

### Cuentas y operaciones financieras

Las **Cuenta** almacenan los productos financieros (ahorro o corriente) de cada socio. El campo `numero_cuenta` es único a nivel institucional, `saldo` mantiene el estado financiero en tiempo real, y `estado` controla si la cuenta está activa, bloqueada o cerrada. Existe una relación **1:N** entre Socio y Cuenta, permitiendo que un socio tenga múltiples productos.

Las operaciones se registran en **Transaccion**, que documenta cada movimiento (`DEPOSITO`, `RETIRO`, `TRANSFERENCIA`, etc.) con su `monto`, `estado` y las cuentas origen/destino involucradas. Cada transacción queda asociada al `id_usuario` que la autorizó (cajero o gerente) y a la `id_sede_origen` desde donde se originó la operación. Esto cumple con la **Ley N° 26702** (Sistema Financiero) y la **Resolución SBS 2660-2015** sobre cooperativas de ahorro y crédito, que exigen registro íntegro e inalterable de operaciones.

Ambas tablas incluyen las cuatro columnas críticas de trazabilidad: `usuario_creacion`, `fecha_creacion`, `usuario_modificacion` y `fecha_modificacion`.

### Préstamos y cuotas

La entidad **Prestamo** responde al objetivo principal del proyecto: reducir tiempos de aprobación de créditos. Registra `monto`, `tasa_interes`, `plazo_meses` y un `estado` que transita por SOLICITADO → EN_REVISION → APROBADO → DESEMBOLSADO. Se vincula al socio solicitante y al usuario aprobador (`id_usuario_aprobador`), lo que permite auditar quién autorizó cada crédito.

El cronograma de pagos se modela en **CuotaPrestamo** con relación **1:N** desde Prestamo. Cada cuota tiene `numero_cuota`, `monto`, `fecha_vencimiento` y flag `pagada`, facilitando el seguimiento de morosidad y el cumplimiento de reportes regulatorios a la SBS.

### Control de acceso: Usuario y Rol

El acceso al sistema se administra mediante **Usuario**, que contiene credenciales (`username`, `email`, `password_hash`) y se vincula con `id_rol` hacia la entidad **Rol**. Los roles definidos son:

| Rol | Descripción |
|-----|-------------|
| CAJERO | Operaciones de caja en sede |
| GERENTE_SUCURSAL | Aprobación de préstamos en sede regional |
| ADMIN_CORE | Administración total del Core Bancario |
| AUDITOR | Solo lectura y consulta de logs |

Cada usuario pertenece opcionalmente a una **Sede**, restringiendo operaciones al ámbito geográfico correspondiente. Esto implementa el principio de **mínimo privilegio** exigido por la Directiva SBS sobre ciberseguridad y gestión de riesgos tecnológicos.

### Infraestructura de red: EquipoRed

La entidad **EquipoRed** documenta los dispositivos de la topología Packet Tracer (routers R-LIMA, R-CHI, R-AQP; switches; servidores SRV-CoreBancario, SRV-Backup). Contiene campos `nombre`, `tipo`, `ip`, `vlan` e `id_sede`, permitiendo al personal de infraestructura correlacionar la capa de datos con la capa de red diseñada en TB1. Aunque no se relaciona directamente con entidades funcionales transaccionales, es clave para garantizar continuidad operativa y diagnóstico de latencia (<50 ms objetivo del SRV-Monitoreo).

### Auditoría normativa: LogAuditoria

**LogAuditoria** registra toda acción relevante ejecutada por los usuarios o disparada por triggers del sistema. Cada fila guarda `id_usuario`, `accion`, `modulo`, `detalle` y `fecha_hora` exacta, junto con `ip_origen` para rastrear la sede de origen.

Esta entidad cumple un rol esencial en el cumplimiento normativo:

- **Ley N° 29733, Art. 18**: derecho del titular a conocer quién accedió a sus datos.
- **Resolución SBS 2660-2015**: controles internos y registros de operaciones en entidades cooperativas.
- **Directiva SBS sobre ciberseguridad**: trazabilidad de eventos del sistema en tiempo real para verificación por auditores.

Los triggers automáticos en tablas `cuenta`, `transaccion`, `prestamo` y `socio` garantizan que ninguna modificación crítica quede sin registro, incluso si la aplicación no invoca explícitamente la función `fn_log_operacion()`.

---

## Mapeo con la arquitectura de servidores

| Capa | Servidor | Tablas principales |
|------|----------|-------------------|
| Primaria (Core) | SRV-CoreBancario / `core-db` | Todas — lectura/escritura |
| Secundaria (Réplica) | SRV-Backup / `replica-db` | Consultas de saldo, estados de cuenta |
| Contingencia | SRV-Contingencia / `contingencia-db` | Respaldo NoSQL de transacciones recientes |
| Supervisión | SRV-Monitoreo / `monitoreo` | Métricas de latencia y disponibilidad del Core |

---

## Referencias normativas

1. **Ley N° 29733** — Ley de Protección de Datos Personales (2011).
2. **Ley N° 26702** — Ley General del Sistema Financiero.
3. **Resolución SBS 2660-2015** — Disposiciones para cooperativas de ahorro y crédito.
4. **Directiva SBS** — Gestión de riesgos tecnológicos y ciberseguridad en entidades supervisadas.
