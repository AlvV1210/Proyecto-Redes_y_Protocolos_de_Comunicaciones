-- PC3 Cooperativa Financiera - Schema Core Bancario
-- PostgreSQL 16

CREATE SCHEMA IF NOT EXISTS core_bancario;
SET search_path TO core_bancario, public;

-- ============================================================
-- Tipos enumerados
-- ============================================================
CREATE TYPE tipo_cuenta AS ENUM ('AHORRO', 'CORRIENTE');
CREATE TYPE estado_cuenta AS ENUM ('ACTIVA', 'BLOQUEADA', 'CERRADA');
CREATE TYPE tipo_transaccion AS ENUM ('DEPOSITO', 'RETIRO', 'TRANSFERENCIA', 'DESEMBOLSO_PRESTAMO', 'PAGO_CUOTA');
CREATE TYPE estado_transaccion AS ENUM ('PENDIENTE', 'COMPLETADA', 'RECHAZADA', 'ANULADA');
CREATE TYPE estado_prestamo AS ENUM ('SOLICITADO', 'EN_REVISION', 'APROBADO', 'DESEMBOLSADO', 'RECHAZADO', 'CANCELADO');

-- ============================================================
-- SEDE - Mapea sedes del Packet Tracer
-- ============================================================
CREATE TABLE sede (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    ciudad          VARCHAR(80)  NOT NULL,
    subnet_ipv4     VARCHAR(18)  NOT NULL UNIQUE,
    es_principal    BOOLEAN      NOT NULL DEFAULT FALSE,
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ
);

-- ============================================================
-- ROL - Control de acceso por perfil
-- ============================================================
CREATE TABLE rol (
    id              SERIAL PRIMARY KEY,
    nombre_rol      VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255),
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ
);

-- ============================================================
-- USUARIO - Empleados del sistema (cajeros, gerentes, admin)
-- ============================================================
CREATE TABLE usuario (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    id_rol          INT          NOT NULL REFERENCES rol(id),
    id_sede         INT          REFERENCES sede(id),
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ
);

-- ============================================================
-- SOCIO - Socios de la cooperativa (~50,000 en producción)
-- ============================================================
CREATE TABLE socio (
    id              SERIAL PRIMARY KEY,
    dni             CHAR(8)      NOT NULL UNIQUE,
    nombres         VARCHAR(100) NOT NULL,
    apellidos       VARCHAR(100) NOT NULL,
    email           VARCHAR(120),
    telefono        VARCHAR(20),
    id_sede         INT          NOT NULL REFERENCES sede(id),
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ,
    CONSTRAINT chk_dni_numerico CHECK (dni ~ '^[0-9]{8}$')
);

-- ============================================================
-- CUENTA - Cuentas de ahorro/corriente
-- ============================================================
CREATE TABLE cuenta (
    id              SERIAL PRIMARY KEY,
    numero_cuenta   VARCHAR(20)  NOT NULL UNIQUE,
    tipo            tipo_cuenta  NOT NULL,
    saldo           NUMERIC(14,2) NOT NULL DEFAULT 0.00,
    estado          estado_cuenta NOT NULL DEFAULT 'ACTIVA',
    id_socio        INT          NOT NULL REFERENCES socio(id),
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ,
    CONSTRAINT chk_saldo_no_negativo CHECK (saldo >= 0)
);

-- ============================================================
-- TRANSACCION - Operaciones financieras
-- ============================================================
CREATE TABLE transaccion (
    id                  SERIAL PRIMARY KEY,
    monto               NUMERIC(14,2) NOT NULL,
    tipo                tipo_transaccion NOT NULL,
    estado              estado_transaccion NOT NULL DEFAULT 'PENDIENTE',
    descripcion         VARCHAR(255),
    id_cuenta_origen    INT REFERENCES cuenta(id),
    id_cuenta_destino   INT REFERENCES cuenta(id),
    id_usuario          INT NOT NULL REFERENCES usuario(id),
    id_sede_origen      INT REFERENCES sede(id),
    fecha_operacion     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ,
    CONSTRAINT chk_monto_positivo CHECK (monto > 0),
    CONSTRAINT chk_cuenta_operacion CHECK (
        id_cuenta_origen IS NOT NULL OR id_cuenta_destino IS NOT NULL
    )
);

-- ============================================================
-- PRESTAMO - Préstamos solicitados y aprobados
-- ============================================================
CREATE TABLE prestamo (
    id                  SERIAL PRIMARY KEY,
    monto               NUMERIC(14,2) NOT NULL,
    tasa_interes        NUMERIC(5,2)  NOT NULL,
    plazo_meses         INT           NOT NULL,
    estado              estado_prestamo NOT NULL DEFAULT 'SOLICITADO',
    id_socio            INT           NOT NULL REFERENCES socio(id),
    id_usuario_solicita INT           REFERENCES usuario(id),
    id_usuario_aprobador INT          REFERENCES usuario(id),
    fecha_solicitud     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    fecha_aprobacion    TIMESTAMPTZ,
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ,
    CONSTRAINT chk_monto_prestamo CHECK (monto > 0),
    CONSTRAINT chk_plazo CHECK (plazo_meses BETWEEN 1 AND 360)
);

-- ============================================================
-- CUOTA_PRESTAMO - Cronograma de pagos
-- ============================================================
CREATE TABLE cuota_prestamo (
    id                  SERIAL PRIMARY KEY,
    id_prestamo         INT           NOT NULL REFERENCES prestamo(id),
    numero_cuota        INT           NOT NULL,
    monto               NUMERIC(14,2) NOT NULL,
    fecha_vencimiento   DATE          NOT NULL,
    pagada              BOOLEAN       NOT NULL DEFAULT FALSE,
    fecha_pago          TIMESTAMPTZ,
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ,
    UNIQUE (id_prestamo, numero_cuota)
);

-- ============================================================
-- EQUIPO_RED - Dispositivos de la topología Packet Tracer
-- ============================================================
CREATE TABLE equipo_red (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(80)  NOT NULL UNIQUE,
    tipo            VARCHAR(40)  NOT NULL,
    ip              INET         NOT NULL,
    vlan            INT,
    id_sede         INT          REFERENCES sede(id),
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    usuario_creacion     VARCHAR(80) NOT NULL DEFAULT 'SYSTEM',
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_modificacion VARCHAR(80),
    fecha_modificacion   TIMESTAMPTZ
);

-- ============================================================
-- LOG_AUDITORIA - Trazabilidad normativa
-- ============================================================
CREATE TABLE log_auditoria (
    id              SERIAL PRIMARY KEY,
    id_usuario      INT          REFERENCES usuario(id),
    accion          VARCHAR(50)  NOT NULL,
    modulo          VARCHAR(80)  NOT NULL,
    detalle         TEXT,
    ip_origen       INET,
    fecha_hora      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Índices
-- ============================================================
CREATE INDEX idx_socio_dni ON socio(dni);
CREATE INDEX idx_socio_sede ON socio(id_sede);
CREATE INDEX idx_cuenta_socio ON cuenta(id_socio);
CREATE INDEX idx_cuenta_numero ON cuenta(numero_cuenta);
CREATE INDEX idx_transaccion_fecha ON transaccion(fecha_operacion);
CREATE INDEX idx_transaccion_cuenta_origen ON transaccion(id_cuenta_origen);
CREATE INDEX idx_transaccion_cuenta_destino ON transaccion(id_cuenta_destino);
CREATE INDEX idx_prestamo_socio ON prestamo(id_socio);
CREATE INDEX idx_prestamo_estado ON prestamo(estado);
CREATE INDEX idx_cuota_prestamo ON cuota_prestamo(id_prestamo);
CREATE INDEX idx_log_auditoria_fecha ON log_auditoria(fecha_hora);
CREATE INDEX idx_log_auditoria_usuario ON log_auditoria(id_usuario);
CREATE INDEX idx_equipo_red_sede ON equipo_red(id_sede);
