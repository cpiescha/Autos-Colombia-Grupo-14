import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { PagoItem } from '../../models/payment.model';

@Component({
  selector: 'app-pago-anular',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Anular Pago</h1>
        <p>Selecciona un pago vigente y registra el motivo de anulación.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;" *ngIf="pagoSeleccionado">
        <h2>Confirmar Anulación — Recibo {{ pagoSeleccionado.numero_recibo || pagoSeleccionado.id }}</h2>
        <p>
          <strong>Cliente:</strong> {{ pagoSeleccionado.cliente_nombre || pagoSeleccionado.documento || '-' }} |
          <strong>Monto:</strong> {{ pagoSeleccionado.monto | currency:'COP':'symbol-narrow':'1.0-0' }}
        </p>

        <form (ngSubmit)="confirmarAnulacion()" class="form-grid" style="margin-top: 1rem;">
          <div class="form-group" style="grid-column: 1 / -1;">
            <label>Motivo de anulación *</label>
            <input
              type="text"
              [(ngModel)]="motivo"
              name="motivo"
              placeholder="Describe la razón de la anulación"
              required
            />
          </div>

          <div class="form-actions" style="grid-column: 1 / -1; display: flex; gap: 0.75rem;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">
              {{ cargando ? 'Anulando...' : 'Confirmar anulación' }}
            </button>
            <button type="button" class="btn btn-secondary" (click)="cancelarSeleccion()">Cancelar</button>
          </div>
        </form>
      </div>

      <div *ngIf="mensaje" class="alert alert-success">{{ mensaje }}</div>
      <div *ngIf="error" class="alert alert-error">{{ error }}</div>

      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1rem;">
          <h2>Pagos disponibles para anular</h2>
          <div style="display: flex; gap: 0.5rem;">
            <input
              type="text"
              [(ngModel)]="filtroDocumento"
              placeholder="Filtrar por cliente..."
              (keyup.enter)="cargarPagos()"
            />
            <button type="button" class="btn btn-secondary" (click)="cargarPagos()">Buscar</button>
          </div>
        </div>

        <table class="table" *ngIf="pagos.length > 0; else sinPagos">
          <thead>
            <tr>
              <th>Recibo</th>
              <th>Fecha</th>
              <th>Cliente / Doc.</th>
              <th>Placa</th>
              <th>Monto</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of pagos">
              <td>{{ p.numero_recibo || p.id }}</td>
              <td>{{ p.fecha_pago }}</td>
              <td>{{ p.cliente_nombre || p.documento || '-' }}</td>
              <td>{{ p.placa || '-' }}</td>
              <td>{{ p.monto | currency:'COP':'symbol-narrow':'1.0-0' }}</td>
              <td>
                <button type="button" class="btn btn-sm btn-secondary" (click)="seleccionar(p)">
                  Seleccionar
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <ng-template #sinPagos>
          <p>No hay pagos activos para anular.</p>
        </ng-template>
      </div>
    </section>
  `,
})
export class PagoAnularComponent implements OnInit {
  private readonly pagosService = inject(PagosService);
  private readonly cambios = inject(ChangeDetectorRef);

  pagos: PagoItem[] = [];
  pagoSeleccionado: PagoItem | null = null;
  filtroDocumento = '';
  motivo = '';
  cargando = false;
  mensaje = '';
  error = '';

  ngOnInit(): void {
    this.cargarPagos();
  }

  cargarPagos(): void {
    this.cargando = true;
    this.error = '';

    this.pagosService
      .listarHistorialPagos({
        documento: this.filtroDocumento,
        estado: 'PAGADO',
      })
      .subscribe({
        next: (data) => {
          this.pagos = data;
          this.cargando = false;
          this.cambios.markForCheck();
        },
        error: (err) => {
          this.error = this.pagosService.mensaje(err);
          this.cargando = false;
          this.cambios.markForCheck();
        },
      });
  }

  seleccionar(pago: PagoItem): void {
    this.pagoSeleccionado = pago;
    this.motivo = '';
    this.mensaje = '';
    this.error = '';
  }

  cancelarSeleccion(): void {
    this.pagoSeleccionado = null;
    this.motivo = '';
  }

  confirmarAnulacion(): void {
    if (!this.pagoSeleccionado || !this.motivo.trim()) {
      this.error = 'Debes ingresar el motivo de la anulación.';
      return;
    }

    this.cargando = true;
    this.error = '';
    this.mensaje = '';

    this.pagosService
      .anularPago(this.pagoSeleccionado.id, { motivo: this.motivo.trim() })
      .subscribe({
        next: () => {
          this.mensaje = 'Pago anulado correctamente.';
          this.pagoSeleccionado = null;
          this.motivo = '';
          this.cambios.markForCheck();
          this.cargarPagos();
        },
        error: (err) => {
          this.error = this.pagosService.mensaje(err);
          this.cargando = false;
          this.cambios.markForCheck();
        },
      });
  }
}
