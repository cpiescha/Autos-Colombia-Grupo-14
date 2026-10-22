import { Routes } from '@angular/router';
import { ConsultaComponent } from './pages/consulta/consulta.component';
import { IngresoComponent } from './pages/ingreso/ingreso.component';
import { SalidaComponent } from './pages/salida/salida.component';
import { OcupacionComponent } from './pages/ocupacion/ocupacion.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'consulta' },
  { path: 'consulta', component: ConsultaComponent, title: 'Consulta de vehículo' },
  { path: 'ingreso', component: IngresoComponent, title: 'Registro de ingreso' },
  { path: 'salida', component: SalidaComponent, title: 'Registro de salida' },
  { path: 'ocupacion', component: OcupacionComponent, title: 'Ocupación de celdas' },
  { path: '**', redirectTo: 'consulta' },
];