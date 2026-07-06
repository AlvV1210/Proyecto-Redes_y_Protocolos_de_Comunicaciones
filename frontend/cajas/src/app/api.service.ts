import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = '/api/v1';

  constructor(private http: HttpClient) {}

  private headers(): HttpHeaders {
    const token = localStorage.getItem('token');
    return new HttpHeaders(token ? { Authorization: `Bearer ${token}` } : {});
  }

  login(username: string, password: string): Observable<any> {
    return this.http.post(`${this.base}/auth/login`, { username, password });
  }

  buscarCuenta(numero: string): Observable<any> {
    return this.http.get(`${this.base}/cuentas/cuentas/numero/${numero}`, { headers: this.headers() });
  }

  buscarSocio(dni: string): Observable<any> {
    return this.http.get(`${this.base}/cuentas/socios/dni/${dni}`, { headers: this.headers() });
  }

  deposito(idCuenta: number, monto: number, descripcion?: string): Observable<any> {
    return this.http.post(`${this.base}/cuentas/transacciones/deposito`,
      { id_cuenta: idCuenta, monto, descripcion }, { headers: this.headers() });
  }

  retiro(idCuenta: number, monto: number, descripcion?: string): Observable<any> {
    return this.http.post(`${this.base}/cuentas/transacciones/retiro`,
      { id_cuenta: idCuenta, monto, descripcion }, { headers: this.headers() });
  }

  registrarSocio(data: any): Observable<any> {
    return this.http.post(`${this.base}/cuentas/socios`, data, { headers: this.headers() });
  }
}
