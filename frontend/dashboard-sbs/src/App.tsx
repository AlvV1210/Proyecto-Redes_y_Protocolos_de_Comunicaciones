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
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await loginEmpleado(username, password);
      navigate('/');
    } catch {
      setError('Credenciales inválidas');
    }
  };

  return (
    <div className="container" style={{ paddingTop: '4rem' }}>
      <div className="card" style={{ maxWidth: 400, margin: '0 auto' }}>
        <h1>Dashboard SBS</h1>
        <p style={{ color: '#666', marginBottom: '1rem' }}>Monitoreo y cumplimiento normativo</p>
        <form onSubmit={submit}>
          <label>Usuario</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
          <label>Contraseña</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn" style={{ width: '100%' }}>Ingresar</button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#888' }}>Demo: auditor / Coop2026!</p>
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
  const nombre = localStorage.getItem('nombre');

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
    <>
      <div className="header-bar">
        <span className="logo">Dashboard SBS 504-2021</span>
        <span>{nombre} <button className="btn btn-outline" style={{ marginLeft: '1rem' }} onClick={() => { localStorage.clear(); navigate('/login'); }}>Salir</button></span>
      </div>
      <div className="container">
        <div className="widget">
          <div className="widget-item">
            <div>Core PostgreSQL</div>
            <h3 className={core?.disponible ? 'status-ok' : 'status-fail'}>
              {core?.disponible ? 'ONLINE' : 'OFFLINE'}
            </h3>
          </div>
          <div className="widget-item">
            <div>Prometheus pg_up</div>
            <h3 className={prom?.disponible ? 'status-ok' : 'status-fail'}>
              {prom?.pg_up ?? 'N/A'}
            </h3>
          </div>
          <div className="widget-item">
            <div>Préstamos pendientes</div>
            <h3>{pendientes}</h3>
          </div>
          <div className="widget-item">
            <div>Eventos failover</div>
            <h3>{failover.length}</h3>
          </div>
        </div>

        <div className="card">
          <h2>Logs de auditoría (SBS N° 504-2021)</h2>
          <table>
            <thead><tr><th>Fecha</th><th>Usuario</th><th>Módulo</th><th>Acción</th><th>IP</th></tr></thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{new Date(l.fecha_hora).toLocaleString()}</td>
                  <td>{l.id_usuario ?? '-'}</td>
                  <td>{l.modulo}</td>
                  <td>{l.accion}</td>
                  <td>{l.ip_origen ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>Resumen por módulo (30 días)</h2>
          <table>
            <thead><tr><th>Fecha</th><th>Módulo</th><th>Total</th></tr></thead>
            <tbody>
              {resumen.map((r, i) => (
                <tr key={i}><td>{r.fecha}</td><td>{r.modulo}</td><td>{r.total}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        {failover.length > 0 && (
          <div className="card">
            <h2>Últimos eventos de contingencia</h2>
            <pre>{JSON.stringify(failover, null, 2)}</pre>
          </div>
        )}
      </div>
    </>
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
