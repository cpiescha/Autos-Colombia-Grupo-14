import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { RecaudoResumen } from '../../models/payment.model';

@Component({
  selector: 'app-recaudo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Reporte de Recaudo</h1>
        <p>Consulta el total recaudado por rango de fechas y desglose por medio de pago.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;">
        <form (ngSubmit)="consultar()" class="form-grid">
          <div class="form-group">
            <label>Fecha inicio *</label>
            <input type="date" [(ngModel)]="fechaInicio" name="fechaInicio" required />
          </div>

          <div class="form-group">
            <label>Fecha fin *</label>
            <input type="date" [(ngModel)]="fechaFin" name="fechaFin" required />
          </div>

          <div class="form-actions" style="grid-column: 1 / -1;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">
              {{ cargando ? 'Consultando...' : 'Consultar recaudo' }}
            </button>
          </div>
        </form>
      </div>

      <div *ngIf="error" class="alert alert-error">{{ error }}</div>

      <ng-container *ngIf="resumen">
        <div class="form-grid" style="margin-bottom: 1.5rem;">
          <div class="card">
            <h3>Total Recaudado</h3>
            <p style="font-size: 1.5rem; font-weight: 700;">
              {{ resumen.total_recaudado | currency:'COP':'symbol-narrow':'1.0-0' }}
            </p>
            <small>{{ resumen.cantidad_pagos_validos }} pagos válidos</small>
          </div>

          <div class="card">
            <h3>Total Anulado</h3>
            <p style="font-size: 1.5rem; font-weight: 700;">
              {{ resumen.total_anulado | currency:'COP':'symbol-narrow':'1.0-0' }}
            </p>
            <small>{{ resumen.cantidad_pagos_anulados }} pagos anulados</small>
          </div>
        </div>

        <div class="card">
          <h2>Desglose por Medio de Pago</h2>
          <table class="table" *ngIf="resumen.por_metodo?.length; else sinDetalle">
            <thead>
              <tr>
                <th>Medio de pago</th>
                <th>Cantidad de pagos</th>
                <th>Total recaudado</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let item of resumen.por_metodo">
                <td>{{ item.metodo_pago }}</td>
                <td>{{ item.cantidad }}</td>
                <td>{{ item.total | currency:'COP':'symbol-narrow':'1.0-0' }}</td>
              </tr>
            </tbody>
          </table>

          <ng-template #sinDetalle>
            <p>No hay movimientos registrados en el rango seleccionado.</p>
          </ng-template>
        </div>
      </ng-container>
    </section>
  `,
})
export class RecaudoComponent implements OnInit {
  private readonly pagosService = inject(PagosService);

  fechaInicio = new Date().toISOString().slice(0, 10);
  fechaFin = new Date().toISOString().slice(0, 10);
  cargando = false;
  error = '';
  resumen: RecaudoResumen | null = null;

  ngOnInit(): void {
    this.consultar();
  }

  consultar(): void {
    if (!this.fechaInicio || !this.fechaFin) {
      this.error = 'Selecciona la fecha de inicio y la fecha fin.';
      return;
    }

    this.cargando = true;
    this.error = '';

    this.pagosService.consultarRecaudo(this.fechaInicio, this.fechaFin).subscribe({
      next: (data) => {
        this.resumen = data;
        this.cargando = false;
      },
      error: (err) => {
        this.error = err?.error?.detail || 'No se pudo consultar el reporte de recaudo.';
        this.cargando = false;
      },
    });
  }
}
