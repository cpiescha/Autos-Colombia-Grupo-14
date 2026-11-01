import { Routes } from '@angular/router';
import { ShellComponent } from './layout/shell.component';
import { LoginComponent } from './pages/login/login.component';
import { AccesoDenegadoComponent } from './pages/acceso-denegado/acceso-denegado.component';
import { InicioComponent } from './pages/inicio/inicio.component';
import { EntradaComponent } from './pages/entrada/entrada.component';
import { SalidaComponent } from './pages/salida/salida.component';
import { OcupacionComponent } from './pages/ocupacion/ocupacion.component';
import { PresentesComponent } from './pages/presentes/presentes.component';
import { ReportesComponent } from './pages/reportes/reportes.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'inicio' },
  { path: 'inicio', component: InicioComponent, title: 'Inicio' },
  { path: 'entrada', component: EntradaComponent, title: 'Registrar entrada' },
  { path: 'salida', component: SalidaComponent, title: 'Registrar salida' },
  { path: 'ocupacion', component: OcupacionComponent, title: 'Ocupación y disponibilidad' },
  { path: 'presentes', component: PresentesComponent, title: 'Vehículos presentes' },
  { path: 'reportes', component: ReportesComponent, title: 'Reporte de ocupación' },
  { path: '**', redirectTo: 'inicio' },
];
