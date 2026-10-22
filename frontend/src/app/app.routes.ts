import { Routes } from '@angular/router';
import { EntradaComponent } from './pages/entrada/entrada.component';
import { SalidaComponent } from './pages/salida/salida.component';
import { OcupacionComponent } from './pages/ocupacion/ocupacion.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'entrada' },
  { path: 'entrada', component: EntradaComponent, title: 'Registrar entrada' },
  { path: 'salida', component: SalidaComponent, title: 'Registro de salida' },
  { path: 'ocupacion', component: OcupacionComponent, title: 'Ocupación de celdas' },
  { path: '**', redirectTo: 'entrada' },
];