import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { PagoItem } from '../../models/payment.model';

@Component({
  selector: 'app-pago-historial',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Historial de Pagos</h1>
        <p>Consulta los pagos registrados, filtra por documento, placa, estado o fechas.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;">
        <form (ngSubmit)="buscar()" class="form-grid">
          <div class="form-group">
            <label>Cliente</label>
            <input type="text" [(ngModel)]="filtros.documento" name="documento" placeholder="Nombre del cliente" />
          </div>

          <div class="form-group">
            <label>Placa</label>
            <input
              type="text"
              [(ngModel)]="filtros.placa"
              name="placa"
              placeholder="Ej. ABC123"
              style="text-transform: uppercase;"
            />
          </div>

          <div class="form-group">
            <label>Estado</label>
            <select [(ngModel)]="filtros.estado" name="estado">
              <option value="">Todos</option>
              <option value="PAGADO">Pagado</option>
              <option value="ANULADO">Anulado</option>
            </select>
          </div>

          <div class="form-group">
            <label>Fecha inicio</label>
            <input type="date" [(ngModel)]="filtros.fecha_inicio" name="fecha_inicio" />
          </div>

          <div class="form-group">
            <label>Fecha fin</label>
            <input type="date" [(ngModel)]="filtros.fecha_fin" name="fecha_fin" />
          </div>

          <div class="form-actions" style="grid-column: 1 / -1; display: flex; gap: 0.75rem;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">
              {{ cargando ? 'Buscando...' : 'Filtrar' }}
            </button>
            <button type="button" class="btn btn-secondary" (click)="limpiar()">Limpiar</button>
          </div>
        </form>
      </div>

      <div *ngIf="error" class="alert alert-error">{{ error }}</div>

      <div class="card">
        <table class="table" *ngIf="pagos.length > 0; else sinPagos">
          <thead>
            <tr>
              <th>Recibo</th>
              <th>Fecha</th>
              <th>Cliente / Doc.</th>
              <th>Placa</th>
              <th>Método</th>
              <th>Monto</th>
              <th>Vigencia hasta</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of pagos">
              <td>{{ p.numero_recibo || p.id }}</td>
              <td>{{ p.fecha_pago }}</td>
              <td>{{ p.cliente_nombre || p.documento || '-' }}</td>
              <td>{{ p.placa || '-' }}</td>
              <td>{{ p.metodo_pago }}</td>
              <td>{{ p.monto | currency:'COP':'symbol-narrow':'1.0-0' }}</td>
              <td>{{ p.vigencia_hasta || '-' }}</td>
              <td>
                <span
                  class="badge"
                  [class.badge-success]="p.estado === 'REGISTRADO'"
                  [class.badge-danger]="p.estado === 'ANULADO'"
                >
                  {{ p.estado }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <ng-template #sinPagos>
          <p>No se encontraron pagos con los criterios seleccionados.</p>
        </ng-template>
      </div>
    </section>
  `,
})
export class PagoHistorialComponent implements OnInit {
  private readonly pagosService = inject(PagosService);

  pagos: PagoItem[] = [];
  cargando = false;
  error = '';

  filtros = {
    documento: '',
    placa: '',
    estado: '',
    fecha_inicio: '',
    fecha_fin: '',
  };

  ngOnInit(): void {
    this.buscar();
  }

  buscar(): void {
    this.cargando = true;
    this.error = '';

    this.pagosService.listarHistorialPagos(this.filtros).subscribe({
      next: (data) => {
        this.pagos = data;
        this.cargando = false;
      },
      error: (err) => {
        this.error = this.pagosService.mensaje(err);
        this.cargando = false;
      },
    });
  }

  limpiar(): void {
    this.filtros = {
      documento: '',
      placa: '',
      estado: '',
      fecha_inicio: '',
      fecha_fin: '',
    };
    this.buscar();
  }
}
