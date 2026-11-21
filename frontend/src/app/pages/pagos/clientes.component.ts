import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PagosService } from '../../services/pagos.service';
import { Cliente, ClienteCreate } from '../../models/payment.model';

@Component({
  selector: 'app-clientes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrl: '../paginas.scss',
  template: `
    <section class="page-container">
      <header class="page-header">
        <h1>Gestión de Clientes</h1>
        <p>Registra, consulta y actualiza el estado de los clientes de mensualidad.</p>
      </header>

      <div class="card" style="margin-bottom: 1.5rem;">
        <h2>{{ editandoId ? 'Editar Cliente' : 'Nuevo Cliente' }}</h2>
        <form (ngSubmit)="guardarCliente()" class="form-grid">
          <div class="form-group">
            <label>Documento *</label>
            <input
              type="text"
              [(ngModel)]="form.documento"
              name="documento"
              [disabled]="!!editandoId"
              placeholder="Ej. 1065123456"
              required
            />
          </div>
          <div class="form-group">
            <label>Nombre completo *</label>
            <input
              type="text"
              [(ngModel)]="form.nombre"
              name="nombre"
              placeholder="Nombre y apellidos"
              required
            />
          </div>
          <div class="form-group">
            <label>Teléfono</label>
            <input type="text" [(ngModel)]="form.telefono" name="telefono" placeholder="3001234567" />
          </div>
          <div class="form-group">
            <label>Correo electrónico</label>
            <input type="email" [(ngModel)]="form.correo" name="correo" placeholder="cliente@correo.com" />
          </div>

          <div class="form-actions" style="grid-column: 1 / -1; display: flex; gap: 0.75rem;">
            <button type="submit" class="btn btn-primary" [disabled]="cargando">
              {{ editandoId ? 'Actualizar cliente' : 'Registrar cliente' }}
            </button>
            <button *ngIf="editandoId" type="button" class="btn btn-secondary" (click)="cancelarEdicion()">
              Cancelar
            </button>
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
              placeholder="Buscar por documento o nombre..."
              (keyup.enter)="cargarClientes()"
            />
            <button type="button" class="btn btn-secondary" (click)="cargarClientes()">Buscar</button>
          </div>
        </div>

        <table class="table" *ngIf="clientes.length > 0; else sinDatos">
          <thead>
            <tr>
              <th>Documento</th>
              <th>Nombre</th>
              <th>Teléfono</th>
              <th>Correo</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let c of clientes">
              <td>{{ c.documento }}</td>
              <td>{{ c.nombre }}</td>
              <td>{{ c.telefono || '-' }}</td>
              <td>{{ c.correo || '-' }}</td>
              <td>
                <span class="badge" [class.badge-success]="c.activo" [class.badge-danger]="!c.activo">
                  {{ c.activo ? 'ACTIVO' : 'INACTIVO' }}
                </span>
              </td>
              <td style="display: flex; gap: 0.5rem;">
                <button type="button" class="btn btn-sm btn-secondary" (click)="editar(c)">Editar</button>
                <button type="button" class="btn btn-sm" (click)="toggleEstado(c)">
                  {{ c.activo ? 'Inactivar' : 'Activar' }}
                </button>
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

  clientes: Cliente[] = [];
  filtro = '';
  cargando = false;
  editandoId: number | null = null;
  mensaje = '';
  error = '';

  form: ClienteCreate = {
    documento: '',
    nombre: '',
    telefono: '',
    correo: '',
  };

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
      },
      error: (err) => {
        this.error = err?.error?.detail || 'No se pudo cargar la lista de clientes.';
        this.cargando = false;
      },
    });
  }

  guardarCliente(): void {
    if (!this.form.documento.trim() || !this.form.nombre.trim()) {
      this.error = 'Documento y nombre son obligatorios.';
      return;
    }

    this.cargando = true;
    this.mensaje = '';
    this.error = '';

    if (this.editandoId) {
      this.pagosService
        .actualizarCliente(this.editandoId, {
          nombre: this.form.nombre,
          telefono: this.form.telefono,
          correo: this.form.correo,
        })
        .subscribe({
          next: () => {
            this.mensaje = 'Cliente actualizado correctamente.';
            this.cancelarEdicion();
            this.cargarClientes();
          },
          error: (err) => {
            this.error = err?.error?.detail || 'Error al actualizar el cliente.';
            this.cargando = false;
          },
        });
    } else {
      this.pagosService.crearCliente(this.form).subscribe({
        next: () => {
          this.mensaje = 'Cliente registrado correctamente.';
          this.form = { documento: '', nombre: '', telefono: '', correo: '' };
          this.cargarClientes();
        },
        error: (err) => {
          this.error = err?.error?.detail || 'Error al registrar el cliente.';
          this.cargando = false;
        },
      });
    }
  }

  editar(cliente: Cliente): void {
    this.editandoId = cliente.id;
    this.form = {
      documento: cliente.documento,
      nombre: cliente.nombre,
      telefono: cliente.telefono || '',
      correo: cliente.correo || '',
    };
    this.mensaje = '';
    this.error = '';
  }

  cancelarEdicion(): void {
    this.editandoId = null;
    this.form = { documento: '', nombre: '', telefono: '', correo: '' };
    this.cargando = false;
  }

  toggleEstado(cliente: Cliente): void {
    this.pagosService.actualizarCliente(cliente.id, { activo: !cliente.activo }).subscribe({
      next: () => {
        this.mensaje = `Cliente ${!cliente.activo ? 'activado' : 'inactivado'} correctamente.`;
        this.cargarClientes();
      },
      error: (err) => {
        this.error = err?.error?.detail || 'No se pudo cambiar el estado del cliente.';
      },
    });
  }
}