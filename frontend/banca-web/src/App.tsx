import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import {
  loginSocio, getCuentas, getTransacciones, transferir,
  solicitarPrestamo, evaluarPrestamo, Cuenta, Transaccion,
} from './api';
import './index.css';

function Login() {
  const [dni, setDni] = useState('45678901');
  const [pin, setPin] = useState('8901');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await loginSocio(dni, pin);
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'DNI o PIN incorrectos. Verifique sus datos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-hero">
        <h1>CoopBanca</h1>
        <p className="tagline">
          Banca por Internet de la Cooperativa Financiera.
          Consulte saldos, transfiera fondos y solicite créditos desde cualquier lugar.
        </p>
        <div className="features">
          <div className="feature-item"><span className="feature-dot" /> Consulta de saldos en tiempo real</div>
          <div className="feature-item"><span className="feature-dot" /> Transferencias seguras entre cuentas</div>
          <div className="feature-item"><span className="feature-dot" /> Solicitud de préstamos con scoring automático</div>
        </div>
      </div>
      <div className="login-form-side">
        <div className="login-card">
          <h2>Bienvenido</h2>
          <p className="subtitle">Ingrese con su DNI y PIN de socio</p>
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label>DNI</label>
              <input value={dni} onChange={(e) => setDni(e.target.value)} maxLength={8} placeholder="8 dígitos" required />
            </div>
            <div className="field">
              <label>PIN</label>
              <input value={pin} onChange={(e) => setPin(e.target.value)} maxLength={4} type="password" placeholder="4 dígitos" required />
            </div>
            {error && <div className="error-msg">{error}</div>}
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Ingresando...' : 'Ingresar a Banca Web'}
            </button>
          </form>
          <p className="hint">Demo: DNI 45678901 · PIN 8901</p>
        </div>
      </div>
    </div>
  );
}

function Dashboard() {
  const socioId = Number(localStorage.getItem('socio_id'));
  const nombre = localStorage.getItem('nombre') || 'Socio';
  const [cuentas, setCuentas] = useState<Cuenta[]>([]);
  const [txs, setTxs] = useState<Transaccion[]>([]);
  const [tab, setTab] = useState<'cuentas' | 'transferir' | 'prestamo'>('cuentas');
  const navigate = useNavigate();

  const load = async () => {
    try {
      setCuentas(await getCuentas(socioId));
      setTxs(await getTransacciones(socioId));
    } catch { /* silent */ }
  };

  useEffect(() => { load(); }, [socioId]);

  const logout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const saldoTotal = cuentas.reduce((s, c) => s + Number(c.saldo), 0);

  const titles: Record<string, string> = {
    cuentas: 'Mis Cuentas',
    transferir: 'Transferencias',
    prestamo: 'Solicitar Préstamo',
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">🏦</div>
          <div>
            <div className="brand-name">CoopBanca</div>
            <div className="brand-sub">Banca por Internet</div>
          </div>
        </div>
        <nav className="nav-menu">
          <button className={`nav-item ${tab === 'cuentas' ? 'active' : ''}`} onClick={() => setTab('cuentas')}>
            💳 Mis Cuentas
          </button>
          <button className={`nav-item ${tab === 'transferir' ? 'active' : ''}`} onClick={() => setTab('transferir')}>
            ↔️ Transferir
          </button>
          <button className={`nav-item ${tab === 'prestamo' ? 'active' : ''}`} onClick={() => setTab('prestamo')}>
            📋 Préstamos
          </button>
        </nav>
        <div className="user-card">
          <div className="name">{nombre}</div>
          <div className="role">Socio · ID {socioId}</div>
          <button className="btn-logout" onClick={logout}>Cerrar sesión</button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-header">
          <h1>{titles[tab]}</h1>
          <p>Gestione sus operaciones financieras de forma segura</p>
        </div>

        {tab === 'cuentas' && (
          <>
            <div className="stats-row">
              <div className="stat-card">
                <div className="label">Saldo total</div>
                <div className="value">S/ {saldoTotal.toFixed(2)}</div>
              </div>
              <div className="stat-card">
                <div className="label">Cuentas activas</div>
                <div className="value">{cuentas.filter((c) => c.estado === 'ACTIVA').length}</div>
              </div>
              <div className="stat-card">
                <div className="label">Transacciones recientes</div>
                <div className="value">{txs.length}</div>
              </div>
            </div>

            <div className="panel">
              <h2>Mis cuentas</h2>
              <div className="account-grid">
                {cuentas.map((c) => (
                  <div key={c.id} className="account-card">
                    <div className="num">{c.numero_cuenta}</div>
                    <span className="type">{c.tipo}</span>
                    <div className="balance">S/ {Number(c.saldo).toFixed(2)}</div>
                    <div className="status">Estado: {c.estado}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <h2>Últimas transacciones</h2>
              <table>
                <thead>
                  <tr><th>Fecha</th><th>Tipo</th><th>Monto</th><th>Estado</th></tr>
                </thead>
                <tbody>
                  {txs.map((t) => (
                    <tr key={t.id}>
                      <td>{new Date(t.fecha_operacion).toLocaleString('es-PE')}</td>
                      <td>{t.tipo}</td>
                      <td>S/ {Number(t.monto).toFixed(2)}</td>
                      <td><span className={`badge ${t.estado === 'COMPLETADA' ? 'badge-ok' : 'badge-warn'}`}>{t.estado}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {tab === 'transferir' && <Transferir cuentas={cuentas} onDone={load} />}
        {tab === 'prestamo' && <Prestamo />}
      </main>
    </div>
  );
}

function Transferir({ cuentas, onDone }: { cuentas: Cuenta[]; onDone: () => void }) {
  const [origen, setOrigen] = useState(0);
  const [destino, setDestino] = useState(0);
  const [monto, setMonto] = useState('');
  const [msg, setMsg] = useState('');
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    if (cuentas.length >= 2) { setOrigen(cuentas[0].id); setDestino(cuentas[1].id); }
    else if (cuentas.length === 1) setOrigen(cuentas[0].id);
  }, [cuentas]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await transferir(origen, destino, Number(monto));
      setMsg('✓ Transferencia realizada correctamente');
      setIsError(false);
      onDone();
    } catch {
      setMsg('Error en la transferencia. Verifique saldo y cuentas.');
      setIsError(true);
    }
  };

  return (
    <div className="panel">
      <h2>Transferencia entre cuentas propias</h2>
      <form onSubmit={submit}>
        <div className="field">
          <label>Cuenta origen</label>
          <select value={origen} onChange={(e) => setOrigen(Number(e.target.value))}>
            {cuentas.map((c) => <option key={c.id} value={c.id}>{c.numero_cuenta} — S/ {Number(c.saldo).toFixed(2)}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Cuenta destino</label>
          <select value={destino} onChange={(e) => setDestino(Number(e.target.value))}>
            {cuentas.map((c) => <option key={c.id} value={c.id}>{c.numero_cuenta}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Monto (S/)</label>
          <input type="number" step="0.01" min="0.01" value={monto} onChange={(e) => setMonto(e.target.value)} required />
        </div>
        <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.75rem 2rem' }}>Confirmar transferencia</button>
        {msg && <p className={isError ? 'error-msg' : 'success-msg'}>{msg}</p>}
      </form>
    </div>
  );
}

function Prestamo() {
  const [monto, setMonto] = useState('5000');
  const [plazo, setPlazo] = useState('12');
  const [result, setResult] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const p = await solicitarPrestamo(Number(monto), Number(plazo));
      const ev = await evaluarPrestamo(p.id);
      setResult(`${ev.mensaje} — Estado: ${ev.estado}`);
    } catch {
      setResult('Error al solicitar préstamo');
    }
  };

  return (
    <div className="panel">
      <h2>Solicitud de crédito</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.25rem', fontSize: '0.9rem' }}>
        El sistema evaluará automáticamente su perfil crediticio (scoring académico).
      </p>
      <form onSubmit={submit}>
        <div className="field">
          <label>Monto solicitado (S/)</label>
          <input type="number" value={monto} onChange={(e) => setMonto(e.target.value)} required />
        </div>
        <div className="field">
          <label>Plazo (meses)</label>
          <input type="number" value={plazo} onChange={(e) => setPlazo(e.target.value)} min="1" max="360" required />
        </div>
        <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.75rem 2rem' }}>Solicitar y evaluar</button>
        {result && <p className="success-msg" style={{ marginTop: '1rem' }}>{result}</p>}
      </form>
    </div>
  );
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
  return localStorage.getItem('token') ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
}
