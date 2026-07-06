-- PC3 Cooperativa Financiera - Consultas de demostración
-- Ejecutar contra core-db (escritura) o replica-db (solo lectura)
SET search_path TO core_bancario, public;

-- ============================================================
-- ESCENARIO 1: Apertura de cuenta (Cajero Lima)
-- Usuario: cajero.lima@coop.pe (id=2), Sede Lima (id=3)
-- ============================================================
-- Paso 1: Registrar log de operación
SELECT fn_log_operacion(2, 'APERTURA_CUENTA', 'CUENTA',
    'Inicio apertura cuenta para socio id=7 (Lucía Mendoza)', '192.168.2.10');

-- Paso 2: Crear nueva cuenta de ahorro
INSERT INTO cuenta (numero_cuenta, tipo, saldo, estado, id_socio, usuario_creacion)
VALUES ('001-000005', 'AHORRO', 0.00, 'ACTIVA', 7, 'cajero.lima')
RETURNING id, numero_cuenta, tipo, saldo, estado;

-- Paso 3: Verificar log de auditoría generado por trigger
SELECT id, accion, modulo, LEFT(detalle, 80) AS detalle, fecha_hora
FROM log_auditoria
WHERE modulo = 'cuenta'
ORDER BY fecha_hora DESC
LIMIT 3;

-- ============================================================
-- ESCENARIO 2: Depósito en cuenta
-- ============================================================
BEGIN;

-- Depósito de S/ 2,000.00 a cuenta 001-000005
UPDATE cuenta
SET saldo = saldo + 2000.00,
    usuario_modificacion = 'cajero.lima',
    fecha_modificacion = NOW()
WHERE numero_cuenta = '001-000005';

INSERT INTO transaccion (monto, tipo, estado, descripcion, id_cuenta_destino, id_usuario, id_sede_origen, usuario_creacion)
VALUES (2000.00, 'DEPOSITO', 'COMPLETADA', 'Depósito en efectivo - apertura',
        (SELECT id FROM cuenta WHERE numero_cuenta = '001-000005'),
        2, 3, 'cajero.lima')
RETURNING id, monto, tipo, estado;

COMMIT;

-- Verificar saldo actualizado
SELECT c.numero_cuenta, c.saldo, s.nombres || ' ' || s.apellidos AS socio
FROM cuenta c
JOIN socio s ON s.id = c.id_socio
WHERE c.numero_cuenta = '001-000005';

-- ============================================================
-- ESCENARIO 3: Consulta de saldo desde sede regional (RÉPLICA)
-- Ejecutar este bloque conectado a replica-db (solo lectura)
-- Demuestra descarga del Core hacia SRV-Backup
-- ============================================================
-- SELECT pg_is_in_recovery();  -- debe retornar TRUE en réplica

SELECT
    s.nombres || ' ' || s.apellidos AS socio,
    sed.nombre AS sede,
    c.numero_cuenta,
    c.tipo,
    c.saldo,
    c.estado
FROM cuenta c
JOIN socio s ON s.id = c.id_socio
JOIN sede sed ON sed.id = s.id_sede
WHERE sed.ciudad = 'Chiclayo'
ORDER BY c.numero_cuenta;

-- Resumen de saldos por sede (consulta típica de estado de cuenta regional)
SELECT
    sed.ciudad,
    COUNT(c.id) AS total_cuentas,
    SUM(c.saldo) AS saldo_total
FROM cuenta c
JOIN socio s ON s.id = c.id_socio
JOIN sede sed ON sed.id = s.id_sede
GROUP BY sed.ciudad
ORDER BY saldo_total DESC;

-- ============================================================
-- ESCENARIO 4: Solicitud y aprobación de préstamo (Gerente Chiclayo)
-- ============================================================
BEGIN;

-- Solicitud de préstamo
INSERT INTO prestamo (monto, tasa_interes, plazo_meses, estado, id_socio, id_usuario_solicita, usuario_creacion)
VALUES (8000.00, 11.50, 12, 'SOLICITADO', 4, 3, 'gerente.chi')
RETURNING id, monto, estado;

-- Aprobación (en la misma transacción para demo)
UPDATE prestamo
SET estado = 'APROBADO',
    id_usuario_aprobador = 3,
    fecha_aprobacion = NOW(),
    usuario_modificacion = 'gerente.chi',
    fecha_modificacion = NOW()
WHERE id_socio = 4 AND estado = 'SOLICITADO'
RETURNING id, monto, estado, fecha_aprobacion;

-- Generar cuotas del préstamo aprobado
INSERT INTO cuota_prestamo (id_prestamo, numero_cuota, monto, fecha_vencimiento, usuario_creacion)
SELECT
    p.id,
    gs.n,
    ROUND(p.monto / p.plazo_meses, 2),
    CURRENT_DATE + (gs.n * INTERVAL '30 days'),
    'gerente.chi'
FROM prestamo p
CROSS JOIN generate_series(1, p.plazo_meses) AS gs(n)
WHERE p.id_socio = 4 AND p.estado = 'APROBADO'
  AND NOT EXISTS (SELECT 1 FROM cuota_prestamo cp WHERE cp.id_prestamo = p.id);

COMMIT;

-- Verificar préstamo y cuotas
SELECT p.id, p.monto, p.estado, s.nombres, s.apellidos,
       COUNT(cp.id) AS total_cuotas
FROM prestamo p
JOIN socio s ON s.id = p.id_socio
LEFT JOIN cuota_prestamo cp ON cp.id_prestamo = p.id
WHERE p.id_socio = 4
GROUP BY p.id, p.monto, p.estado, s.nombres, s.apellidos;

-- ============================================================
-- ESCENARIO 5: Transferencia entre cuentas (transacción atómica)
-- ============================================================
BEGIN;

-- Transferir S/ 1,500 de cuenta 001-000001 a 001-000003
DO $$
DECLARE
    v_origen INT;
    v_destino INT;
    v_monto NUMERIC := 1500.00;
    v_saldo_origen NUMERIC;
BEGIN
    SELECT id, saldo INTO v_origen, v_saldo_origen FROM cuenta WHERE numero_cuenta = '001-000001';
    SELECT id INTO v_destino FROM cuenta WHERE numero_cuenta = '001-000003';

    IF v_saldo_origen < v_monto THEN
        RAISE EXCEPTION 'Saldo insuficiente: % < %', v_saldo_origen, v_monto;
    END IF;

    UPDATE cuenta SET saldo = saldo - v_monto, usuario_modificacion = 'cajero.lima', fecha_modificacion = NOW()
    WHERE id = v_origen;

    UPDATE cuenta SET saldo = saldo + v_monto, usuario_modificacion = 'cajero.lima', fecha_modificacion = NOW()
    WHERE id = v_destino;

    INSERT INTO transaccion (monto, tipo, estado, descripcion, id_cuenta_origen, id_cuenta_destino, id_usuario, id_sede_origen, usuario_creacion)
    VALUES (v_monto, 'TRANSFERENCIA', 'COMPLETADA', 'Transferencia entre cuentas Lima',
            v_origen, v_destino, 2, 3, 'cajero.lima');
END $$;

COMMIT;

-- Verificar saldos post-transferencia
SELECT numero_cuenta, saldo FROM cuenta WHERE numero_cuenta IN ('001-000001', '001-000003');

-- Verificar log de auditoría de la transferencia
SELECT accion, modulo, LEFT(detalle, 100) AS detalle, fecha_hora
FROM log_auditoria
WHERE modulo IN ('cuenta', 'transaccion')
ORDER BY fecha_hora DESC
LIMIT 5;

-- ============================================================
-- ESCENARIO 6: Reporte para auditor (solo lectura)
-- ============================================================
SELECT
    la.fecha_hora,
    u.username,
    r.nombre_rol,
    la.accion,
    la.modulo,
    la.ip_origen
FROM log_auditoria la
LEFT JOIN usuario u ON u.id = la.id_usuario
LEFT JOIN rol r ON r.id = u.id_rol
ORDER BY la.fecha_hora DESC
LIMIT 20;

-- ============================================================
-- ESCENARIO 7: Verificación de replicación
-- Ejecutar INSERT en Core, luego SELECT en Réplica
-- ============================================================
-- En CORE:
-- INSERT INTO transaccion (monto, tipo, estado, descripcion, id_cuenta_destino, id_usuario, id_sede_origen)
-- VALUES (100.00, 'DEPOSITO', 'COMPLETADA', 'Prueba replicación', 1, 2, 3);

-- En RÉPLICA:
-- SELECT id, monto, descripcion, fecha_operacion FROM transaccion ORDER BY id DESC LIMIT 1;
-- SELECT pg_is_in_recovery();  -- TRUE = réplica activa

-- ============================================================
-- ESCENARIO 8: Simulación failover (documentación)
-- 1. docker stop core-db
-- 2. Verificar alerta en Prometheus: http://<VM-IP>:9090/alerts
-- 3. Consultar MongoDB contingencia:
--    docker exec contingencia-db mongosh --eval "db.transacciones_respaldo.find().limit(5)"
-- 4. docker start core-db
-- ============================================================
