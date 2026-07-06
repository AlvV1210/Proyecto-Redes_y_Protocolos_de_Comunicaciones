-- Actualizar hashes bcrypt compatibles con capa de aplicación
SET search_path TO core_bancario, public;

UPDATE usuario SET password_hash = '$2b$12$BO2GoOM1Om1RdrwVPoq3W.Gf3vb7u78LbvGWFApu2lSzabvFM8XDa';
