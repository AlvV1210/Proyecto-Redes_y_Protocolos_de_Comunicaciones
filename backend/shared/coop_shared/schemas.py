from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TipoCuenta(str, Enum):
    AHORRO = "AHORRO"
    CORRIENTE = "CORRIENTE"


class EstadoCuenta(str, Enum):
    ACTIVA = "ACTIVA"
    BLOQUEADA = "BLOQUEADA"
    CERRADA = "CERRADA"


class TipoTransaccion(str, Enum):
    DEPOSITO = "DEPOSITO"
    RETIRO = "RETIRO"
    TRANSFERENCIA = "TRANSFERENCIA"
    DESEMBOLSO_PRESTAMO = "DESEMBOLSO_PRESTAMO"
    PAGO_CUOTA = "PAGO_CUOTA"


class EstadoTransaccion(str, Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    RECHAZADA = "RECHAZADA"
    ANULADA = "ANULADA"


class EstadoPrestamo(str, Enum):
    SOLICITADO = "SOLICITADO"
    EN_REVISION = "EN_REVISION"
    APROBADO = "APROBADO"
    DESEMBOLSADO = "DESEMBOLSADO"
    RECHAZADO = "RECHAZADO"
    CANCELADO = "CANCELADO"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    rol: Optional[str] = None
    socio_id: Optional[int] = None
    usuario_id: Optional[int] = None
    nombre: Optional[str] = None


class LoginEmpleadoRequest(BaseModel):
    username: str
    password: str


class LoginSocioRequest(BaseModel):
    dni: str = Field(min_length=8, max_length=8)
    pin: str = Field(min_length=4, max_length=4)


class CuentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_cuenta: str
    tipo: TipoCuenta
    saldo: Decimal
    estado: EstadoCuenta
    id_socio: int


class TransaccionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monto: Decimal
    tipo: TipoTransaccion
    estado: EstadoTransaccion
    descripcion: Optional[str] = None
    id_cuenta_origen: Optional[int] = None
    id_cuenta_destino: Optional[int] = None
    fecha_operacion: datetime


class DepositoRequest(BaseModel):
    id_cuenta: int
    monto: Decimal = Field(gt=0)
    descripcion: Optional[str] = None


class RetiroRequest(BaseModel):
    id_cuenta: int
    monto: Decimal = Field(gt=0)
    descripcion: Optional[str] = None


class TransferenciaRequest(BaseModel):
    id_cuenta_origen: int
    id_cuenta_destino: int
    monto: Decimal = Field(gt=0)
    descripcion: Optional[str] = None


class BloquearCuentaRequest(BaseModel):
    motivo: str


class PrestamoRequest(BaseModel):
    monto: Decimal = Field(gt=0)
    plazo_meses: int = Field(ge=1, le=360)
    tasa_interes: Decimal = Field(default=Decimal("12.50"), ge=0)


class PrestamoResponse(BaseModel):
    id: int
    monto: Decimal
    tasa_interes: Decimal
    plazo_meses: int
    estado: EstadoPrestamo
    id_socio: int
    fecha_solicitud: datetime
    fecha_aprobacion: Optional[datetime] = None


class CuotaResponse(BaseModel):
    numero_cuota: int
    monto: Decimal
    fecha_vencimiento: date
    pagada: bool


class PrestamoDetalleResponse(PrestamoResponse):
    cuotas: list[CuotaResponse] = []
    score: Optional[float] = None
    motivo_rechazo: Optional[str] = None


class EvaluarPrestamoResponse(BaseModel):
    prestamo_id: int
    score: float
    estado: EstadoPrestamo
    mensaje: str


class LogAuditoriaResponse(BaseModel):
    id: int
    id_usuario: Optional[int]
    accion: str
    modulo: str
    detalle: Optional[str]
    ip_origen: Optional[str]
    fecha_hora: datetime


class ResumenAuditoriaItem(BaseModel):
    modulo: str
    total: int
    fecha: date


class SocioResponse(BaseModel):
    id: int
    dni: str
    nombres: str
    apellidos: str
    email: Optional[str]
    telefono: Optional[str]
    id_sede: int
    activo: bool


class SocioCreateRequest(BaseModel):
    dni: str = Field(min_length=8, max_length=8)
    nombres: str
    apellidos: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    id_sede: int


class EstadoCoreResponse(BaseModel):
    disponible: bool
    mensaje: str


class EstadoPrometheusResponse(BaseModel):
    pg_up: Optional[float]
    disponible: bool


class TokenPayload(BaseModel):
    sub: str
    tipo: str  # empleado | socio
    rol: Optional[str] = None
    usuario_id: Optional[int] = None
    socio_id: Optional[int] = None
    sede_id: Optional[int] = None
    nombre: Optional[str] = None
