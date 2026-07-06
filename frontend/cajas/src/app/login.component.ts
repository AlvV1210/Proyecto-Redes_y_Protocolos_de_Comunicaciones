import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from './api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  template: `
    <div class="container" style="padding-top: 3rem;">
      <div class="card" style="max-width: 400px; margin: 0 auto;">
        <h1>Terminal de Cajas</h1>
        <p style="color: #666; margin-bottom: 1rem;">Ventanilla — Cooperativa Financiera</p>
        <label>Usuario</label>
        <input [(ngModel)]="username" name="username" />
        <label>Contraseña</label>
        <input [(ngModel)]="password" name="password" type="password" />
        <p class="error" *ngIf="error">{{ error }}</p>
        <button class="btn" (click)="login()" style="width: 100%; margin-top: 0.5rem;">Ingresar</button>
        <p style="font-size: 0.85rem; color: #888; margin-top: 1rem;">Demo: cajero.lima / Coop2026!</p>
      </div>
    </div>
  `,
})
export class LoginComponent {
  username = 'cajero.lima';
  password = 'Coop2026!';
  error = '';

  constructor(private api: ApiService, private router: Router) {}

  login() {
    this.api.login(this.username, this.password).subscribe({
      next: (data) => {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('nombre', data.nombre);
        this.router.navigate(['/']);
      },
      error: () => (this.error = 'Credenciales inválidas'),
    });
  }
}
