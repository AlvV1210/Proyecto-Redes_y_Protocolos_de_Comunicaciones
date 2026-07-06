import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import {
  loginEmpleado, getLogs, getResumen, getEstadoCore,
  getEstadoProm, getPrestamosPendientes, getEventosFailover,
} from './api';
import './index.css';

function Login() {
  const [username, setUsername] = useState('auditor');
  const [password, setPassword] = useState('Coop2026!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await loginEmpleado(username, password);
      navigate('/');
    } catch {
      setError('Credenciales inválidas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Dashboard Gerencial</h1>
        <p className="sub">Monitoreo SBS N° 504-2021 · Cooperativa Financiera</p>
        <form onSubmit={submit}>
          <div className="field">
            <label>Usuario</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="field">
            <label>Contraseña</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Ingresando...' : 'Ingresar al panel'}
          </button>
        </form>
        <p className="hint">Demo: auditor / Coop2026! · admin.core para acceso total</p>
      </div>
    </div>
  );
}

function Dashboard() {
  const [logs, setLogs] = useState<any[]>([]);
  const [resumen, setResumen] = useState<any[]>([]);
  const [core, setCore] = useState<any>(null);
  const [prom, setProm] = useState<any>(null);
  const [pendientes, setPendientes] = useState(0);
  const [failover, setFailover] = useState<any[]>([]);
  const navigate = useNavigate();
  const nombre = localStorage.getItem('nombre') || 'Auditor';

  useEffect(() => {
    const load = async () => {
      try {
        setLogs(await getLogs());
        setResumen(await getResumen());
        setCore(await getEstadoCore());
        setProm(await getEstadoProm());
        const p = await getPrestamosPendientes();
        setPendientes(p.pendientes);
        const ev = await getEventosFailover();
        setFailover(ev.eventos || []);
      } catch (e) {
        console.error(e);
      }
    };
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">📊</div>
          <div>
            <div className="brand-name">CoopMonitor</div>
            <div className="brand-sub">Panel Gerencial SBS</div>
          </div>
        </div>
        <div className="nav-item active">Auditoría y cumplimiento</div>
        <div className="nav-item">Resiliencia Core</div>
        <div className="nav-item">Métricas Prometheus</div>
        <div className="user-card">
          <div style={{ fontWeight: 600 }}>{nombre}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Rol auditoría</div>
          <button className="btn-logout" onClick={() => { localStorage.clear(); navigate('/login'); }}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="main">
        <div className="page-header">
          <h1>Panel de monitoreo operativo</h1>
          <p>Estado del Core bancario, auditoría normativa y contingencia NoSQL</p>
        </div>

        <div className="metrics">
          <div className="metric">
            <div className="label">Core PostgreSQL</div>
            <div className={`value ${core?.disponible ? 'ok' : 'fail'}`}>
              {core?.disponible ? 'ONLINE' : 'OFFLINE'}
            </div>
          </div>
          <div className="metric">
            <div className="label">Prometheus pg_up</div>
            <div className={`value ${prom?.disponible ? 'ok' : 'fail'}`}>
              {prom?.pg_up ?? '—'}
            </div>
          </div>
          <div className="metric">
            <div className="label">Préstamos pendientes</div>
            <div className="value" style={{ color: 'var(--accent)' }}>{pendientes}</div>
          </div>
          <div className="metric">
            <div className="label">Eventos failover</div>
            <div className="value" style={{ color: failover.length ? 'var(--fail)' : 'var(--ok)' }}>
              {failover.length}
            </div>
          </div>
        </div>

        <div className="panel">
          <h2>Logs de auditoría — SBS N° 504-2021</h2>
          <table>
            <thead>
              <tr><th>Fecha</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>IP origen</th></tr>
            </thead>
            <tbody>
              {logs.slice(0, 25).map((l) => (
                <tr key={l.id}>
                  <td>{new Date(l.fecha_hora).toLocaleString('es-PE')}</td>
                  <td>{l.id_usuario ?? '—'}</td>
                  <td>{l.modulo}</td>
                  <td><span className="badge badge-ok">{l.accion}</span></td>
                  <td>{l.ip_origen ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <h2>Resumen de eventos (últimos 30 días)</h2>
          <table>
            <thead><tr><th>Fecha</th><th>Módulo</th><th>Total eventos</th></tr></thead>
            <tbody>
              {resumen.slice(0, 15).map((r, i) => (
                <tr key={i}><td>{r.fecha}</td><td>{r.modulo}</td><td>{r.total}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        {failover.length > 0 && (
          <div className="panel">
            <h2>Eventos de contingencia (MongoDB)</h2>
            <pre style={{ fontSize: '0.8rem', overflow: 'auto', color: 'var(--text-muted)' }}>
              {JSON.stringify(failover, null, 2)}
            </pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={localStorage.getItem('token') ? <Dashboard /> : <Navigate to="/login" />} />
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}
