import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AccesoService } from '../../services/acceso.service';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1>Autos Colombia</h1>
    <p class="sub">Control de entradas y salidas del parqueadero por mensualidad.</p>

    <div class="tarjetas">
      <div class="tarjeta"><span>Libres</span><strong>{{ acceso.libres() }}</strong></div>
      <div class="tarjeta"><span>Ocupadas</span><strong>{{ acceso.ocupadas() }}</strong></div>
      <div class="tarjeta"><span>Presentes ahora</span><strong>{{ acceso.activos().length }}</strong></div>
    </div>

    <div class="acciones">
      <a routerLink="/entrada" class="boton">Registrar entrada</a>
      <a routerLink="/salida" class="boton">Registrar salida</a>
      <a routerLink="/ocupacion" class="boton claro">Ver ocupación</a>
    </div>
  `,
  styles: [`
    h1 { margin: 0 0 4px; font-size: 24px; font-weight: 500; color: #0d2a4d; }
    .sub { margin: 0 0 20px; color: #5f6b7a; }
    .tarjetas { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
    .tarjeta { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 12px 20px; min-width: 150px; display: grid; gap: 4px; }
    .tarjeta span { font-size: 13px; color: #5f6b7a; }
    .tarjeta strong { font-size: 28px; color: #0d47a1; font-weight: 500; }
    .acciones { display: flex; gap: 12px; flex-wrap: wrap; }
    .boton { background: #1565c0; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 20px; }
    .boton.claro { background: #e3f2fd; color: #0d47a1; }
  `],
})
export class InicioComponent {
  acceso = inject(AccesoService);
}