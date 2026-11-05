import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ClienteOpcion, VehiculoDetalle, VehiculoEscritura, VehiculoGuardado } from '../models/vehicle-admin.model';

@Injectable({ providedIn: 'root' })
export class VehiculosService {
  private readonly http = inject(HttpClient);
  readonly clientes = signal<ClienteOpcion[]>([]);
  readonly pendiente = signal(false);
  readonly error = signal('');
  readonly errorClientes = signal('');

  async cargarClientes(): Promise<boolean> {
    if (this.pendiente()) return false;
    this.pendiente.set(true);
    this.errorClientes.set('');
    try {
      this.clientes.set(await firstValueFrom(this.http.get<ClienteOpcion[]>('/api/clientes')));
      return true;
    } catch {
      this.errorClientes.set('No fue posible cargar los clientes existentes.');
      return false;
    } finally { this.pendiente.set(false); }
  }

  buscar(placa: string): Promise<VehiculoDetalle | null> {
    return this.ejecutar(() => firstValueFrom(this.http.get<VehiculoDetalle>(`/api/vehiculos/${this.placa(placa)}`)));
  }

  crear(datos: VehiculoEscritura): Promise<VehiculoGuardado | null> {
    return this.ejecutar(() => firstValueFrom(this.http.post<VehiculoGuardado>('/api/vehiculos', this.normalizar(datos))));
  }

  actualizar(placaActual: string, datos: VehiculoEscritura): Promise<VehiculoGuardado | null> {
    return this.ejecutar(() => firstValueFrom(this.http.put<VehiculoGuardado>(`/api/vehiculos/${this.placa(placaActual)}`, this.normalizar(datos))));
  }

  retirar(placa: string): Promise<VehiculoGuardado | null> {
    return this.ejecutar(() => firstValueFrom(this.http.delete<VehiculoGuardado>(`/api/vehiculos/${this.placa(placa)}`)));
  }

  private normalizar(datos: VehiculoEscritura): VehiculoEscritura {
    return { ...datos, placa: this.placa(datos.placa), marca: datos.marca.trim(), modelo: datos.modelo.trim(), color: datos.color.trim() };
  }

  private placa(valor: string): string { return valor.trim().toUpperCase().replace(/\s+/g, ''); }

  private async ejecutar<T>(accion: () => Promise<T>): Promise<T | null> {
    if (this.pendiente()) return null;
    this.pendiente.set(true);
    this.error.set('');
    try { return await accion(); }
    catch (error) {
      const detalle = error instanceof HttpErrorResponse ? error.error?.message ?? error.error?.detail : null;
      this.error.set(typeof detalle === 'string' ? detalle
        : error instanceof HttpErrorResponse && error.status === 403 ? 'Solo el administrador puede modificar vehículos guardados.'
        : 'No fue posible completar la solicitud. Intente nuevamente.');
      return null;
    } finally { this.pendiente.set(false); }
  }
}
