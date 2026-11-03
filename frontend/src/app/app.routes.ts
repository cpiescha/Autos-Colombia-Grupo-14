import { Routes } from '@angular/router';
import { authGuard, loginGuard, rolGuard } from './core/guards';
import { ShellComponent } from './layout/shell.component';
import { AccesoDenegadoComponent } from './pages/acceso-denegado/acceso-denegado.component';
import { CeldaCrearComponent } from './pages/admin/celdas/celda-crear.component';
import { CeldaInactivarComponent } from './pages/admin/celdas/celda-inactivar.component';
import { CeldasComponent } from './pages/admin/celdas/celdas.component';
import { OperadorCreadoComponent } from './pages/admin/operadores/operador-creado.component';
import { OperadorCrearComponent } from './pages/admin/operadores/operador-crear.component';
import { OperadorGestionarComponent } from './pages/admin/operadores/operador-gestionar.component';
import { OperadoresComponent } from './pages/admin/operadores/operadores.component';
import { EntradaComponent } from './pages/entrada/entrada.component';
import { InicioComponent } from './pages/inicio/inicio.component';
import { LoginComponent } from './pages/login/login.component';
import { OcupacionComponent } from './pages/ocupacion/ocupacion.component';
import { PresentesComponent } from './pages/presentes/presentes.component';
import { ReportesComponent } from './pages/reportes/reportes.component';
import { SalidaComponent } from './pages/salida/salida.component';

const ADMIN = { roles: ['ADMINISTRADOR'] };
const AMBOS = { roles: ['ADMINISTRADOR', 'OPERADOR'] };

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
    canActivate: [loginGuard],
    title: 'Iniciar sesión',
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      { path: 'inicio', component: InicioComponent, title: 'Inicio' },
      {
        path: 'entrada',
        component: EntradaComponent,
        canActivate: [rolGuard],
        data: AMBOS,
        title: 'Registrar entrada',
      },
      {
        path: 'salida',
        component: SalidaComponent,
        canActivate: [rolGuard],
        data: AMBOS,
        title: 'Registrar salida',
      },
      {
        path: 'ocupacion',
        component: OcupacionComponent,
        canActivate: [rolGuard],
        data: AMBOS,
        title: 'Ocupación y disponibilidad',
      },
      {
        path: 'presentes',
        component: PresentesComponent,
        canActivate: [rolGuard],
        data: AMBOS,
        title: 'Vehículos presentes',
      },
      {
        path: 'reportes',
        component: ReportesComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Reporte de ocupación',
      },
      {
        path: 'operadores',
        component: OperadoresComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Operadores',
      },
      {
        path: 'operadores/nuevo',
        component: OperadorCrearComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Crear operador',
      },
      {
        path: 'operadores/creado/:id',
        component: OperadorCreadoComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Operador creado',
      },
      {
        path: 'operadores/:id',
        component: OperadorGestionarComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Gestionar cuenta',
      },
      {
        path: 'celdas',
        component: CeldasComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Celdas',
      },
      {
        path: 'celdas/nueva',
        component: CeldaCrearComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Crear celda',
      },
      {
        path: 'celdas/:codigo/inactivar',
        component: CeldaInactivarComponent,
        canActivate: [rolGuard],
        data: ADMIN,
        title: 'Inactivar celda',
      },
      {
        path: 'acceso-denegado',
        component: AccesoDenegadoComponent,
        title: 'Acceso denegado',
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
