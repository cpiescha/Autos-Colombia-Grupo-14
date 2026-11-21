import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { VigenciaMembresia } from '../../models/payment.model';

@Component({
  selector: 'app-vigencia',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Consulta de Vigencia</h1>
        <p>Verifica el estado de la mensualidad por documento del cliente o placa del vehículo.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;">
        <form (ngSubmit)="consultar()" class="form-grid">
          <div class="form-group">
            <label>Nombre del cliente</label>
            <input
              type="text"
              [(ngModel)]="documento"
              name="documento"
              placeholder="Si no tienes la placa"
            />
          </div>
          <div class="form-group">
            <label>Placa del vehículo</label>
            <input
              type="text"
              [(ngModel)]="placa"
              name="placa"
              placeholder="Ej. ABC123"
              style="text-transform: uppercase;"
            />
          </div>
          <div class="form-actions" style="grid-column: 1 / -1;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">
              {{ cargando ? 'Consultando...' : 'Consultar vigencia' }}
            </button>
          </div>
        </form>
      </div>

      <div *ngIf="error" class="alert alert-error">{{ error }}</div>

      <div class="card" *ngIf="vigencia">
        <h2>Estado de la Membresía</h2>
        <div style="display: grid; gap: 0.75rem; margin-top: 1rem;">
          <div>
            <strong>Estado: </strong>
            <span
              class="badge"
              [class.badge-success]="vigencia.estado === 'ACTIVA'"
              [class.badge-warning]="vigencia.estado === 'POR_VENCER'"
              [class.badge-danger]="vigencia.estado === 'VENCIDA' || vigencia.estado === 'SIN_MEMBRESIA'"
            >
              {{ vigencia.estado }}
            </span>
          </div>
          <p *ngIf="vigencia.cliente_nombre"><strong>Cliente:</strong> {{ vigencia.cliente_nombre }}</p>
          <p *ngIf="vigencia.documento"><strong>Documento:</strong> {{ vigencia.documento }}</p>
          <p *ngIf="vigencia.placa"><strong>Placa:</strong> {{ vigencia.placa }}</p>
          <p *ngIf="vigencia.fecha_inicio"><strong>Fecha inicio:</strong> {{ vigencia.fecha_inicio }}</p>
          <p *ngIf="vigencia.fecha_fin"><strong>Fecha vencimiento:</strong> {{ vigencia.fecha_fin }}</p>
          <p *ngIf="vigencia.dias_restantes !== undefined && vigencia.dias_restantes !== null">
            <strong>Días restantes:</strong> {{ vigencia.dias_restantes }}
          </p>
          <p *ngIf="vigencia.mensaje">{{ vigencia.mensaje }}</p>
        </div>
      </div>
    </section>
  `,
})
export class VigenciaComponent {
  private readonly pagosService = inject(PagosService);

  documento = '';
  placa = '';
  cargando = false;
  error = '';
  vigencia: VigenciaMembresia | null = null;

  consultar(): void {
    if (!this.documento.trim() && !this.placa.trim()) {
      this.error = 'Ingresa un documento o una placa para consultar.';
      return;
    }

    this.cargando = true;
    this.error = '';
    this.vigencia = null;

    this.pagosService
      .consultarVigencia({
        documento: this.documento,
        placa: this.placa,
      })
      .subscribe({
        next: (res) => {
          this.vigencia = res;
          this.cargando = false;
        },
        error: (err) => {
          this.error = this.pagosService.mensaje(err);
          this.cargando = false;
        },
      });
  }
}