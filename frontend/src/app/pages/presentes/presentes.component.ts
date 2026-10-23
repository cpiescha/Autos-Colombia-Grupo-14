import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AccesoService } from '../../services/acceso.service';

@Component({
  selector: 'app-presentes',
  standalone: true,
  imports: [DatePipe, RouterLink],
  template: `
    <h1>Vehículos dentro del parqueadero</h1>
    <div class="panel">
      <strong>Tabla operativa</strong>
      @if (acceso.activos().length === 0) {
        <p class="vacio">Lista vacía: no hay permanencias abiertas.</p>
      } @else {
        <div class="scroll">
          <table>
            <thead><tr><th>Placa</th><th>Tipo</th><th>Celda</th><th>Entrada</th><th>Comprobante</th><th>Acción</th></tr></thead>
            <tbody>
              @for (r of acceso.activos(); track r.id) {
                <tr>
                  <td>{{ r.placa }}</td>
                  <td>{{ r.celda.startsWith('M') ? 'MOTO' : 'CARRO' }}</td>
                  <td>{{ r.celda }}</td>
                  <td>{{ r.entrada | date: 'dd/MM/yyyy HH:mm' }}</td>
                  <td>{{ r.comprobanteEntrada.numero }}</td>
                  <td><a class="accion" [routerLink]="['/correccion', r.id]">Corregir celda</a></td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
  styles: [`
    h1 { margin: 0 0 16px; font-size: 24px; font-weight: 500; color: #0d2a4d; }
    .panel { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 16px; }
    .vacio { color: #5f6b7a; margin: 12px 0 0; }
    .scroll { overflow-x: auto; margin-top: 8px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th { text-align: left; color: #5f6b7a; font-weight: 500; }
    th, td { padding: 8px 12px 8px 0; border-bottom: 1px solid #eef1f4; }
    .accion { color: #1565c0; text-decoration: none; font-weight: 500; }
    .accion:hover { text-decoration: underline; }
    .accion:focus-visible { outline: 2px solid #1565c0; outline-offset: 2px; border-radius: 2px; }
  `],
})
export class PresentesComponent {
  acceso = inject(AccesoService);
}
