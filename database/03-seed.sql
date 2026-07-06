-- PC3 Cooperativa Financiera - Datos de prueba
SET search_path TO core_bancario, public;

-- ============================================================
-- SEDES (subnets del Packet Tracer)
-- ============================================================
INSERT INTO sede (id, nombre, ciudad, subnet_ipv4, es_principal) VALUES
    (1, 'Sede Arequipa',  'Arequipa', '192.168.0.0/24',  FALSE),
    (2, 'Sede Chiclayo',  'Chiclayo', '192.168.1.0/24',  FALSE),
    (3, 'Sede Lima',      'Lima',    '192.168.2.0/24',  TRUE)
ON CONFLICT (id) DO NOTHING;

SELECT setval('sede_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sede));

-- ============================================================
-- ROLES
-- ============================================================
INSERT INTO rol (id, nombre_rol, descripcion) VALUES
    (1, 'CAJERO',            'Operaciones de caja: depósitos, retiros, consultas'),
    (2, 'GERENTE_SUCURSAL',  'Aprobación de préstamos y supervisión de sede'),
    (3, 'ADMIN_CORE',        'Administración total del Core Bancario'),
    (4, 'AUDITOR',           'Solo lectura y consulta de logs de auditoría')
ON CONFLICT (id) DO NOTHING;

SELECT setval('rol_id_seq', (SELECT COALESCE(MAX(id), 1) FROM rol));

-- ============================================================
-- USUARIOS (password de todos: "Coop2026!")
-- Hash bcrypt generado para demostración académica
-- ============================================================
INSERT INTO usuario (id, username, email, password_hash, id_rol, id_sede) VALUES
    (1, 'admin.core',    'admin.core@coop.pe',    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 3, NULL),
    (2, 'cajero.lima',   'cajero.lima@coop.pe',   '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 1, 3),
    (3, 'gerente.chi',   'gerente.chi@coop.pe',   '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 2, 2),
    (4, 'cajero.aqp',    'cajero.aqp@coop.pe',    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 1, 1),
    (5, 'auditor',       'auditor@coop.pe',       '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 4, 3)
ON CONFLICT (id) DO NOTHING;

SELECT setval('usuario_id_seq', (SELECT COALESCE(MAX(id), 1) FROM usuario));

-- ============================================================
-- SOCIOS
-- ============================================================
INSERT INTO socio (id, dni, nombres, apellidos, email, telefono, id_sede) VALUES
    (1, '45678901', 'María',    'Quispe',     'maria.quispe@email.com',   '987654321', 3),
    (2, '12345678', 'Carlos',   'Ramírez',    'carlos.ramirez@email.com', '976543210', 3),
    (3, '87654321', 'Ana',      'Torres',     'ana.torres@email.com',     '965432109', 2),
    (4, '23456789', 'Luis',     'Vargas',     'luis.vargas@email.com',    '954321098', 2),
    (5, '34567890', 'Rosa',     'Huamán',     'rosa.huaman@email.com',    '943210987', 1),
    (6, '56789012', 'Pedro',    'Flores',     'pedro.flores@email.com',   '932109876', 1),
    (7, '67890123', 'Lucía',    'Mendoza',    'lucia.mendoza@email.com',  '921098765', 3),
    (8, '78901234', 'Jorge',    'Castillo',   'jorge.castillo@email.com', '910987654', 2)
ON CONFLICT (id) DO NOTHING;

SELECT setval('socio_id_seq', (SELECT COALESCE(MAX(id), 1) FROM socio));

-- ============================================================
-- CUENTAS
-- ============================================================
INSERT INTO cuenta (id, numero_cuenta, tipo, saldo, estado, id_socio) VALUES
    (1,  '001-000001', 'AHORRO',    15000.00, 'ACTIVA', 1),
    (2,  '001-000002', 'CORRIENTE',  8500.50, 'ACTIVA', 1),
    (3,  '001-000003', 'AHORRO',     3200.00, 'ACTIVA', 2),
    (4,  '002-000001', 'AHORRO',    22000.00, 'ACTIVA', 3),
    (5,  '002-000002', 'CORRIENTE',  5600.75, 'ACTIVA', 3),
    (6,  '002-000003', 'AHORRO',     9800.00, 'ACTIVA', 4),
    (7,  '003-000001', 'AHORRO',    11500.00, 'ACTIVA', 5),
    (8,  '003-000002', 'AHORRO',     4300.00, 'ACTIVA', 6),
    (9,  '001-000004', 'AHORRO',    18750.00, 'ACTIVA', 7),
    (10, '002-000004', 'CORRIENTE',  7200.00, 'ACTIVA', 8)
ON CONFLICT (id) DO NOTHING;

SELECT setval('cuenta_id_seq', (SELECT COALESCE(MAX(id), 1) FROM cuenta));

-- ============================================================
-- EQUIPOS DE RED (Packet Tracer)
-- ============================================================
INSERT INTO equipo_red (id, nombre, tipo, ip, vlan, id_sede) VALUES
    (1, 'R-AQP',           'Router',  '192.168.0.1',   10, 1),
    (2, 'R-CHI',           'Router',  '192.168.1.1',   20, 2),
    (3, 'R-LIMA',          'Router',  '192.168.2.1',   30, 3),
    (4, 'R-CORE',          'Router',  '192.168.200.1', 200, NULL),
    (5, 'R-SERVER',        'Router',  '192.168.100.1', 100, NULL),
    (6, 'SRV-CoreBancario','Servidor','192.168.200.10',200, NULL),
    (7, 'SRV-Backup',      'Servidor','192.168.100.20',100, NULL),
    (8, 'SRV-Contingencia','Servidor','192.168.100.30',100, NULL),
    (9, 'SRV-Monitoreo',   'Servidor','192.168.100.40',100, NULL)
ON CONFLICT (id) DO NOTHING;

SELECT setval('equipo_red_id_seq', (SELECT COALESCE(MAX(id), 1) FROM equipo_red));

-- ============================================================
-- TRANSACCIONES INICIALES
-- ============================================================
INSERT INTO transaccion (id, monto, tipo, estado, descripcion, id_cuenta_destino, id_usuario, id_sede_origen) VALUES
    (1, 5000.00,  'DEPOSITO',     'COMPLETADA', 'Depósito inicial apertura cuenta', 1, 2, 3),
    (2, 1500.00,  'DEPOSITO',     'COMPLETADA', 'Depósito en efectivo',             3, 2, 3),
    (3, 3000.00,  'TRANSFERENCIA','COMPLETADA', 'Transferencia entre socios Lima',  2, 2, 3),
    (4, 8000.00,  'DEPOSITO',     'COMPLETADA', 'Depósito sede Chiclayo',           4, 3, 2),
    (5, 2500.00,  'RETIRO',       'COMPLETADA', 'Retiro cajero automático',         7, 4, 1)
ON CONFLICT (id) DO NOTHING;

UPDATE transaccion SET id_cuenta_origen = 1 WHERE id = 3;
UPDATE transaccion SET id_cuenta_origen = 7 WHERE id = 5;

SELECT setval('transaccion_id_seq', (SELECT COALESCE(MAX(id), 1) FROM transaccion));

-- ============================================================
-- PRÉSTAMOS (3 estados distintos)
-- ============================================================
INSERT INTO prestamo (id, monto, tasa_interes, plazo_meses, estado, id_socio, id_usuario_solicita, id_usuario_aprobador, fecha_aprobacion) VALUES
    (1, 10000.00, 12.50, 12, 'SOLICITADO',  2, 2, NULL, NULL),
    (2, 25000.00, 11.00, 24, 'APROBADO',    3, 3, 3, NOW() - INTERVAL '2 days'),
    (3, 15000.00, 10.50, 18, 'DESEMBOLSADO',5, 4, 3, NOW() - INTERVAL '30 days')
ON CONFLICT (id) DO NOTHING;

SELECT setval('prestamo_id_seq', (SELECT COALESCE(MAX(id), 1) FROM prestamo));

-- ============================================================
-- CUOTAS DE PRÉSTAMO DESEMBOLSADO (id=3)
-- ============================================================
INSERT INTO cuota_prestamo (id_prestamo, numero_cuota, monto, fecha_vencimiento, pagada, fecha_pago) VALUES
    (3, 1, 916.67, CURRENT_DATE - INTERVAL '30 days', TRUE,  NOW() - INTERVAL '30 days'),
    (3, 2, 916.67, CURRENT_DATE - INTERVAL '0 days',  FALSE, NULL),
    (3, 3, 916.67, CURRENT_DATE + INTERVAL '30 days', FALSE, NULL),
    (3, 4, 916.67, CURRENT_DATE + INTERVAL '60 days', FALSE, NULL),
    (3, 5, 916.67, CURRENT_DATE + INTERVAL '90 days', FALSE, NULL)
ON CONFLICT (id_prestamo, numero_cuota) DO NOTHING;

-- Cuotas del préstamo aprobado (id=2) - pendientes de desembolso
INSERT INTO cuota_prestamo (id_prestamo, numero_cuota, monto, fecha_vencimiento, pagada) VALUES
    (2, 1, 1166.67, CURRENT_DATE + INTERVAL '30 days', FALSE),
    (2, 2, 1166.67, CURRENT_DATE + INTERVAL '60 days', FALSE),
    (2, 3, 1166.67, CURRENT_DATE + INTERVAL '90 days', FALSE)
ON CONFLICT (id_prestamo, numero_cuota) DO NOTHING;

-- ============================================================
-- LOG INICIAL DE AUDITORÍA
-- ============================================================
INSERT INTO log_auditoria (id_usuario, accion, modulo, detalle, ip_origen) VALUES
    (1, 'INIT', 'SISTEMA', 'Carga inicial de datos de prueba PC3', '192.168.200.10'),
    (2, 'LOGIN', 'AUTENTICACION', 'Inicio de sesión cajero Lima', '192.168.2.10'),
    (3, 'LOGIN', 'AUTENTICACION', 'Inicio de sesión gerente Chiclayo', '192.168.1.10');

SELECT setval('log_auditoria_id_seq', (SELECT COALESCE(MAX(id), 1) FROM log_auditoria));
