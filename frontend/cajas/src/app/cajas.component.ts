import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from './api.service';

@Component({
  selector: 'app-cajas',
  standalone: true,
  imports: [FormsModule, CommonModule],
  template: `
    <div class="header">
      <span><strong>Cooperativa — Cajas</strong></span>
      <span>{{ nombre }} <button class="btn btn-outline" (click)="logout()" style="margin-left: 1rem;">Salir</button></span>
    </div>
    <div class="container">
      <div class="nav">
        <button class="btn" [class.btn-outline]="tab !== 'deposito'" (click)="tab = 'deposito'">Depósito</button>
        <button class="btn" [class.btn-outline]="tab !== 'retiro'" (click)="tab = 'retiro'">Retiro</button>
        <button class="btn" [class.btn-outline]="tab !== 'buscar'" (click)="tab = 'buscar'">Buscar socio</button>
        <button class="btn" [class.btn-outline]="tab !== 'registro'" (click)="tab = 'registro'">Nuevo socio</button>
      </div>

      <div class="card" *ngIf="tab === 'deposito' || tab === 'retiro'">
        <h2>{{ tab === 'deposito' ? 'Depósito' : 'Retiro' }}</h2>
        <label>Número de cuenta</label>
        <input [(ngModel)]="numeroCuenta" name="numeroCuenta" />
        <button class="btn" (click)="buscarCuenta()">Buscar cuenta</button>
        <div *ngIf="cuenta" style="margin: 1rem 0; padding: 1rem; background: #e3f2fd; border-radius: 6px;">
          <strong>{{ cuenta.numero_cuenta }}</strong> — Saldo: S/ {{ cuenta.saldo }}
        </div>
        <label>Monto (S/)</label>
        <input type="number" [(ngModel)]="monto" name="monto" step="0.01" />
        <label>Descripción</label>
        <input [(ngModel)]="descripcion" name="descripcion" />
        <button class="btn" (click)="operar()" [disabled]="!cuenta">Confirmar {{ tab }}</button>
        <p [class]="msgClass" *ngIf="msg">{{ msg }}</p>
      </div>

      <div class="card" *ngIf="tab === 'buscar'">
        <h2>Buscar socio por DNI</h2>
        <label>DNI</label>
        <input [(ngModel)]="dniBuscar" name="dniBuscar" maxlength="8" />
        <button class="btn" (click)="buscarSocio()">Buscar</button>
        <div *ngIf="socio" style="margin-top: 1rem;">
          <p><strong>{{ socio.nombres }} {{ socio.apellidos }}</strong></p>
          <p>Email: {{ socio.email }} | Tel: {{ socio.telefono }}</p>
          <p>Sede ID: {{ socio.id_sede }}</p>
        </div>
      </div>

      <div class="card" *ngIf="tab === 'registro'">
        <h2>Registrar nuevo socio</h2>
        <label>DNI</label>
        <input [(ngModel)]="nuevo.dni" maxlength="8" />
        <label>Nombres</label>
        <input [(ngModel)]="nuevo.nombres" />
        <label>Apellidos</label>
        <input [(ngModel)]="nuevo.apellidos" />
        <label>Email</label>
        <input [(ngModel)]="nuevo.email" />
        <label>Teléfono</label>
        <input [(ngModel)]="nuevo.telefono" />
        <label>Sede</label>
        <select [(ngModel)]="nuevo.id_sede">
          <option [value]="1">Arequipa</option>
          <option [value]="2">Chiclayo</option>
          <option [value]="3">Lima</option>
        </select>
        <button class="btn" (click)="registrar()">Registrar</button>
        <p [class]="msgClass" *ngIf="msg">{{ msg }}</p>
      </div>
    </div>
  `,
})
export class CajasComponent {
  tab: 'deposito' | 'retiro' | 'buscar' | 'registro' = 'deposito';
  nombre = localStorage.getItem('nombre') || 'Cajero';
  numeroCuenta = '001-000001';
  monto = 100;
  descripcion = '';
  cuenta: any = null;
  socio: any = null;
  dniBuscar = '45678901';
  msg = '';
  msgClass = 'success';
  nuevo = { dni: '', nombres: '', apellidos: '', email: '', telefono: '', id_sede: 3 };

  constructor(private api: ApiService, private router: Router) {
    if (!localStorage.getItem('token')) this.router.navigate(['/login']);
  }

  logout() {
    localStorage.clear();
    this.router.navigate(['/login']);
  }

  buscarCuenta() {
    this.api.buscarCuenta(this.numeroCuenta).subscribe({
      next: (c) => { this.cuenta = c; this.msg = ''; },
      error: () => { this.msg = 'Cuenta no encontrada'; this.msgClass = 'error'; },
    });
  }

  operar() {
    const obs = this.tab === 'deposito'
      ? this.api.deposito(this.cuenta.id, this.monto, this.descripcion)
      : this.api.retiro(this.cuenta.id, this.monto, this.descripcion);
    obs.subscribe({
      next: () => {
        this.msg = `${this.tab} realizado correctamente`;
        this.msgClass = 'success';
        this.buscarCuenta();
      },
      error: (e) => {
        this.msg = e.error?.detail || 'Error en operación';
        this.msgClass = 'error';
      },
    });
  }

  buscarSocio() {
    this.api.buscarSocio(this.dniBuscar).subscribe({
      next: (s) => { this.socio = s; },
      error: () => { this.socio = null; },
    });
  }

  registrar() {
    this.api.registrarSocio(this.nuevo).subscribe({
      next: (s) => {
        this.msg = `Socio registrado: ${s.nombres} ${s.apellidos}. PIN: últimos 4 del DNI`;
        this.msgClass = 'success';
      },
      error: (e) => {
        this.msg = e.error?.detail || 'Error al registrar';
        this.msgClass = 'error';
      },
    });
  }
}
