import axios from 'axios';

const api = axios.create({ baseURL: '/api/v1' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function loginEmpleado(username: string, password: string) {
  const { data } = await api.post('/auth/login', { username, password });
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('rol', data.rol);
  localStorage.setItem('nombre', data.nombre);
  return data;
}

export async function getLogs() {
  const { data } = await api.get('/auditoria/logs?page_size=100');
  return data;
}

export async function getResumen() {
  const { data } = await api.get('/auditoria/reportes/resumen');
  return data;
}

export async function getEstadoCore() {
  const { data } = await api.get('/sync/estado/core');
  return data;
}

export async function getEstadoProm() {
  const { data } = await api.get('/sync/estado/prometheus');
  return data;
}

export async function getPrestamosPendientes() {
  const { data } = await api.get('/prestamos/prestamos/pendientes/count');
  return data;
}

export async function getEventosFailover() {
  const { data } = await api.get('/sync/contingencia/eventos-failover?limit=5');
  return data;
}
