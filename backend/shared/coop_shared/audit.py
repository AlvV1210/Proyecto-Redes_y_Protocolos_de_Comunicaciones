from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_evento(
    db: AsyncSession,
    *,
    id_usuario: Optional[int],
    accion: str,
    modulo: str,
    detalle: str,
    ip_origen: Optional[str] = None,
) -> None:
    await db.execute(
        text("""
            INSERT INTO core_bancario.log_auditoria
                (id_usuario, accion, modulo, detalle, ip_origen)
            VALUES (:id_usuario, :accion, :modulo, :detalle, CAST(:ip AS inet))
        """),
        {
            "id_usuario": id_usuario,
            "accion": accion,
            "modulo": modulo,
            "detalle": detalle[:2000],
            "ip": ip_origen or "127.0.0.1",
        },
    )
