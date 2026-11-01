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
import { OperadoresComponent } from './pages/admin/operadores/operadores.component';
import { OperadorCrearComponent } from './pages/admin/operadores/operador-crear.component';
import { OperadorCreadoComponent } from './pages/admin/operadores/operador-creado.component';
import { OperadorGestionarComponent } from './pages/admin/operadores/operador-gestionar.component';
import { CeldasComponent } from './pages/admin/celdas/celdas.component';
import { CeldaCrearComponent } from './pages/admin/celdas/celda-crear.component';
import { CeldaInactivarComponent } from './pages/admin/celdas/celda-inactivar.component';
import { authGuard, loginGuard, rolGuard } from './core/guards';

const ADMIN = { roles: ['ADMINISTRADOR'] };
const AMBOS = { roles: ['ADMINISTRADOR', 'OPERADOR'] };

export const routes: Routes = [
  { path: 'login', component: LoginComponent, canActivate: [loginGuard], title: 'Iniciar sesión' },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      { path: 'inicio', component: InicioComponent, title: 'Inicio' },

      { path: 'entrada', component: EntradaComponent, title: 'Registrar entrada', canActivate: [rolGuard], data: AMBOS },
      { path: 'salida', component: SalidaComponent, title: 'Registrar salida', canActivate: [rolGuard], data: AMBOS },
      { path: 'ocupacion', component: OcupacionComponent, title: 'Ocupación y disponibilidad', canActivate: [rolGuard], data: AMBOS },
      { path: 'presentes', component: PresentesComponent, title: 'Vehículos presentes', canActivate: [rolGuard], data: { roles: ['OPERADOR'] } },
      { path: 'reportes', component: ReportesComponent, title: 'Reporte de ocupación', canActivate: [rolGuard], data: ADMIN },

      { path: 'operadores', component: OperadoresComponent, title: 'Operadores', canActivate: [rolGuard], data: ADMIN },
      { path: 'operadores/nuevo', component: OperadorCrearComponent, title: 'Crear operador', canActivate: [rolGuard], data: ADMIN },
      { path: 'operadores/creado/:id', component: OperadorCreadoComponent, title: 'Operador creado', canActivate: [rolGuard], data: ADMIN },
      { path: 'operadores/:id', component: OperadorGestionarComponent, title: 'Gestionar cuenta', canActivate: [rolGuard], data: ADMIN },

      { path: 'celdas', component: CeldasComponent, title: 'Celdas', canActivate: [rolGuard], data: ADMIN },
      { path: 'celdas/nueva', component: CeldaCrearComponent, title: 'Crear celda', canActivate: [rolGuard], data: ADMIN },
      { path: 'celdas/:codigo/inactivar', component: CeldaInactivarComponent, title: 'Inactivar celda', canActivate: [rolGuard], data: ADMIN },

      { path: 'acceso-denegado', component: AccesoDenegadoComponent, title: 'Acceso denegado' },
    ],
  },
  { path: '**', redirectTo: '' },
];