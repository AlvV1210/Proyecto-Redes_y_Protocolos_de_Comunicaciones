import { Routes } from '@angular/router';
import { LoginComponent } from './login.component';
import { CajasComponent } from './cajas.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: '', component: CajasComponent },
  { path: '**', redirectTo: '' },
];
