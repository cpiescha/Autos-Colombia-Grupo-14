import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { PagoCreate, PagoItem } from '../../models/payment.model';

@Component({
  selector: 'app-pago-registrar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Registrar Pago</h1>
        <p>Registra el pago de mensualidad y genera el comprobante correspondiente.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;">
        <form (ngSubmit)="registrar()" class="form-grid">
          <div class="form-group">
            <label>Placa del vehículo *</label>
            <input
              type="text"
              [(ngModel)]="form.placa"
              name="placa"
              placeholder="Ej. ABC123"
              style="text-transform: uppercase;"
            />
          </div>

          <div class="form-group">
            <label>Monto a pagar (COP) *</label>
            <input
              type="number"
              [(ngModel)]="form.monto"
              name="monto"
              min="1"
              required
            />
          </div>

          <div class="form-group">
            <label>Método de pago *</label>
            <select [(ngModel)]="form.metodo_pago" name="metodo_pago" required>
              <option value="EFECTIVO">Efectivo</option>
              <option value="TRANSFERENCIA">Transferencia</option>
              <option value="QR">QR</option>
            </select>
          </div>

          <div class="form-actions" style="grid-column: 1 / -1;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">
              {{ cargando ? 'Registrando...' : 'Registrar pago' }}
            </button>
          </div>
        </form>
      </div>

      <div *ngIf="error" class="alert alert-error">{{ error }}</div>

      <div class="card" *ngIf="comprobante">
        <h2>Comprobante de Pago Generado</h2>
        <p><strong>Recibo N°:</strong> {{ comprobante.numero_recibo || comprobante.id }}</p>
        <p *ngIf="comprobante.cliente_nombre"><strong>Cliente:</strong> {{ comprobante.cliente_nombre }}</p>
        <p *ngIf="comprobante.placa"><strong>Placa:</strong> {{ comprobante.placa }}</p>
        <p><strong>Monto:</strong> {{ comprobante.monto | currency:'COP':'symbol-narrow':'1.0-0' }}</p>
        <p><strong>Método:</strong> {{ comprobante.metodo_pago }}</p>
        <p><strong>Fecha de pago:</strong> {{ comprobante.fecha_pago }}</p>
        <p *ngIf="comprobante.vigencia_hasta"><strong>Vigente hasta:</strong> {{ comprobante.vigencia_hasta }}</p>
      </div>
    </section>
  `,
})
export class PagoRegistrarComponent {
  private readonly pagosService = inject(PagosService);
  private readonly cambios = inject(ChangeDetectorRef);

  cargando = false;
  error = '';
  comprobante: PagoItem | null = null;

  form: PagoCreate = {
    placa: '',
    monto: 0,
    metodo_pago: 'EFECTIVO',
  };

  registrar(): void {
    if (!this.form.placa?.trim() || !this.form.monto || this.form.monto <= 0) {
      this.error = 'Ingresa la placa y un monto mayor a 0.';
      return;
    }

    this.cargando = true;
    this.error = '';
    this.comprobante = null;

    const payload: PagoCreate = {
      ...this.form,
      placa: this.form.placa?.trim().toUpperCase(),
    };

    this.pagosService.registrarPago(payload).subscribe({
      next: (res) => {
        this.comprobante = res;
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
}
