-- PC3 Cooperativa Financiera - Triggers de auditoría
SET search_path TO core_bancario, public;

-- Función genérica de auditoría
CREATE OR REPLACE FUNCTION fn_registrar_auditoria()
RETURNS TRIGGER AS $$
DECLARE
    v_accion TEXT;
    v_modulo TEXT;
    v_detalle TEXT;
    v_usuario INT;
BEGIN
    v_modulo := TG_TABLE_NAME;

    IF TG_OP = 'INSERT' THEN
        v_accion := 'INSERT';
        v_detalle := 'Registro creado: ' || row_to_json(NEW)::TEXT;
    ELSIF TG_OP = 'UPDATE' THEN
        v_accion := 'UPDATE';
        v_detalle := 'Antes: ' || row_to_json(OLD)::TEXT || ' | Después: ' || row_to_json(NEW)::TEXT;
    ELSIF TG_OP = 'DELETE' THEN
        v_accion := 'DELETE';
        v_detalle := 'Registro eliminado: ' || row_to_json(OLD)::TEXT;
    END IF;

    -- Intentar obtener id_usuario del registro si existe
    BEGIN
        IF TG_OP = 'DELETE' THEN
            v_usuario := (OLD).id_usuario;
        ELSE
            v_usuario := COALESCE((NEW).id_usuario, (NEW).id_usuario_aprobador, (NEW).id_usuario_solicita);
        END IF;
    EXCEPTION WHEN OTHERS THEN
        v_usuario := NULL;
    END;

    INSERT INTO core_bancario.log_auditoria (id_usuario, accion, modulo, detalle, ip_origen)
    VALUES (v_usuario, v_accion, v_modulo, LEFT(v_detalle, 2000), '192.168.200.10'::INET);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = core_bancario, public;

-- Triggers en tablas críticas
CREATE TRIGGER trg_auditoria_cuenta
    AFTER INSERT OR UPDATE OR DELETE ON cuenta
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_auditoria();

CREATE TRIGGER trg_auditoria_transaccion
    AFTER INSERT OR UPDATE ON transaccion
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_auditoria();

CREATE TRIGGER trg_auditoria_prestamo
    AFTER INSERT OR UPDATE ON prestamo
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_auditoria();

CREATE TRIGGER trg_auditoria_socio
    AFTER INSERT OR UPDATE ON socio
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_auditoria();

-- Función para registrar operaciones manuales desde aplicación
CREATE OR REPLACE FUNCTION fn_log_operacion(
    p_id_usuario INT,
    p_accion VARCHAR(50),
    p_modulo VARCHAR(80),
    p_detalle TEXT DEFAULT NULL,
    p_ip_origen INET DEFAULT '192.168.2.10'
)
RETURNS INT AS $$
DECLARE
    v_id INT;
BEGIN
    INSERT INTO core_bancario.log_auditoria (id_usuario, accion, modulo, detalle, ip_origen)
    VALUES (p_id_usuario, p_accion, p_modulo, p_detalle, p_ip_origen)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql SET search_path = core_bancario, public;
