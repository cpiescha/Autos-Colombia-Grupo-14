import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { Cliente } from '../../models/payment.model';

@Component({
  selector: 'app-clientes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Gestión de Clientes</h1>
        <p>Consulta los clientes y deja inactivo a quien ya no usa el parqueadero.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;" *ngIf="clienteSeleccionado">
        <h2>Inactivar a {{ clienteSeleccionado.nombre }}</h2>
        <form (ngSubmit)="inactivar()" class="form-grid">
          <div class="form-group" style="grid-column: 1 / -1;">
            <label>Motivo *</label>
            <input type="text" [(ngModel)]="motivo" name="motivo" required />
          </div>
          <div class="form-actions" style="grid-column: 1 / -1; display: flex; gap: 0.75rem;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">Inactivar</button>
            <button type="button" class="btn btn-secondary" (click)="clienteSeleccionado = null">Cancelar</button>
          </div>
        </form>
      </div>

      <div *ngIf="mensaje" class="alert alert-success">{{ mensaje }}</div>
      <div *ngIf="error" class="alert alert-error">{{ error }}</div>

      <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1rem;">
          <h2>Clientes registrados</h2>
          <div style="display: flex; gap: 0.5rem;">
            <input
              type="text"
              [(ngModel)]="filtro"
              placeholder="Buscar por nombre..."
              (keyup.enter)="cargarClientes()"
            />
            <button type="button" class="btn btn-secondary" (click)="cargarClientes()">Buscar</button>
          </div>
        </div>

        <table class="table" *ngIf="clientes.length > 0; else sinDatos">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let c of clientes">
              <td>{{ c.nombre }}</td>
              <td>
                <button type="button" class="btn btn-sm" (click)="seleccionar(c)">Inactivar</button>
              </td>
            </tr>
          </tbody>
        </table>

        <ng-template #sinDatos>
          <p>No hay clientes registrados para mostrar.</p>
        </ng-template>
      </div>
    </section>
  `,
})
export class ClientesComponent implements OnInit {
  private readonly pagosService = inject(PagosService);
  private readonly cambios = inject(ChangeDetectorRef);

  clientes: Cliente[] = [];
  filtro = '';
  cargando = false;
  clienteSeleccionado: Cliente | null = null;
  motivo = '';
  mensaje = '';
  error = '';

  ngOnInit(): void {
    this.cargarClientes();
  }

  cargarClientes(): void {
    this.cargando = true;
    this.error = '';
    this.pagosService.listarClientes(this.filtro).subscribe({
      next: (data) => {
        this.clientes = data;
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

  seleccionar(cliente: Cliente): void {
    this.clienteSeleccionado = cliente;
    this.motivo = '';
    this.mensaje = '';
    this.error = '';
  }

  inactivar(): void {
    if (!this.clienteSeleccionado || !this.motivo.trim()) {
      this.error = 'Escribe el motivo para inactivar al cliente.';
      return;
    }
    this.cargando = true;
    this.pagosService.inactivarCliente(this.clienteSeleccionado.id, this.motivo.trim()).subscribe({
      next: () => {
        this.mensaje = 'Cliente inactivado.';
        this.clienteSeleccionado = null;
        this.motivo = '';
        this.cambios.markForCheck();
        this.cargarClientes();
      },
      error: (err) => {
        this.error = this.pagosService.mensaje(err);
        this.cargando = false;
        this.cambios.markForCheck();
      },
    });
  }
}