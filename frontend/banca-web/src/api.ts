import axios from 'axios';

const API = import.meta.env.DEV ? '/api/v1' : '/api/v1';

export const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface Cuenta {
  id: number;
  numero_cuenta: string;
  tipo: string;
  saldo: number;
  estado: string;
  id_socio: number;
}

export interface Transaccion {
  id: number;
  monto: number;
  tipo: string;
  estado: string;
  descripcion?: string;
  fecha_operacion: string;
}

export async function loginSocio(dni: string, pin: string) {
  const { data } = await api.post('/auth/socio/login', { dni, pin });
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('socio_id', String(data.socio_id));
  localStorage.setItem('nombre', data.nombre);
  return data;
}

export async function getCuentas(socioId: number) {
  const { data } = await api.get<Cuenta[]>(`/cuentas/cuentas/socio/${socioId}`);
  return data;
}

export async function getTransacciones(socioId: number) {
  const { data } = await api.get<Transaccion[]>(`/cuentas/transacciones/recientes?socio_id=${socioId}`);
  return data;
}

export async function transferir(origen: number, destino: number, monto: number) {
  const { data } = await api.post('/cuentas/transacciones/transferencia', {
    id_cuenta_origen: origen,
    id_cuenta_destino: destino,
    monto,
  });
  return data;
}

export async function solicitarPrestamo(monto: number, plazo: number) {
  const { data } = await api.post('/prestamos/prestamos/solicitar', {
    monto,
    plazo_meses: plazo,
    tasa_interes: 12.5,
  });
  return data;
}

export async function evaluarPrestamo(id: number) {
  const { data } = await api.post(`/prestamos/prestamos/${id}/evaluar`);
  return data;
}
