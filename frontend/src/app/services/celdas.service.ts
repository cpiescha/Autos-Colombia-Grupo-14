import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export type TipoCelda = 'AUTOMOVIL' | 'MOTO';
export type EstadoCelda = 'ACTIVA' | 'INACTIVA';
export type EstadoVisible = 'OCUPADA' | 'ACTIVA · LIBRE' | 'INACTIVA';

export interface Celda {
  id: number;
  codigo: string;
  categoria: TipoCelda;
  estado: 'disponible' | 'ocupada' | 'inactiva';
  placa: string | null;
  tiene_historial: boolean;
}

@Injectable({ providedIn: 'root' })
export class CeldasService {
  private http = inject(HttpClient);
  private _lista = signal<Celda[]>([]);
  lista = this._lista.asReadonly();
  pendiente = signal(false);
  error = signal('');

  obtener(codigo: string): Celda | undefined {
    return this._lista().find(c => c.codigo === codigo);
  }

  async cargar(): Promise<boolean> {
    if (this.pendiente()) return false;
    this._lista.set([]);
    return (await this.ejecutar(async () => {
      this._lista.set(await firstValueFrom(this.http.get<Celda[]>('/api/celdas')));
      return true;
    })) === true;
  }

  crear(codigo: string, categoria: TipoCelda): Promise<Celda | null> {
    return this.ejecutar(async () => {
      const celda = await firstValueFrom(this.http.post<Celda>('/api/celdas', { codigo, categoria }));
      this._lista.update(lista => [...lista, celda]);
      return celda;
    });
  }

  cambiarEstado(id: number, estado: EstadoCelda): Promise<Celda | null> {
    return this.ejecutar(async () => {
      const celda = await firstValueFrom(this.http.patch<Celda>(`/api/celdas/${id}`, { estado }));
      this.actualizar(celda);
      return celda;
    });
  }

  // DELETE returns the inactive cell when history exists, otherwise 204 with no body.
  async retirar(id: number): Promise<boolean> {
    return (await this.ejecutar(async () => {
      const respuesta = await firstValueFrom(this.http.delete<Celda>(`/api/celdas/${id}`, { observe: 'response' }));
      if (respuesta.status === 204) this._lista.update(lista => lista.filter(c => c.id !== id));
      else if (respuesta.body) this.actualizar(respuesta.body);
      else throw new Error('Respuesta de retiro vacía');
      return true;
    })) === true;
  }

  estadoVisible(c: Celda): EstadoVisible {
    return c.estado === 'inactiva' ? 'INACTIVA' : c.estado === 'ocupada' ? 'OCUPADA' : 'ACTIVA · LIBRE';
  }
  etiquetaTipo(t: TipoCelda): string { return t === 'MOTO' ? 'MOTO' : 'AUTOMÓVIL'; }

  private actualizar(celda: Celda) {
    this._lista.update(lista => lista.map(c => c.id === celda.id ? celda : c));
  }

  private async ejecutar<T>(accion: () => Promise<T>): Promise<T | null> {
    if (this.pendiente()) return null;
    this.pendiente.set(true);
    this.error.set('');
    try { return await accion(); }
    catch (error) {
      const detalle = error instanceof HttpErrorResponse ? error.error?.message ?? error.error?.detail : null;
      this.error.set(typeof detalle === 'string' ? detalle : Array.isArray(detalle)
        ? detalle.map(d => `${d.loc?.slice(1).join('.') ?? ''}: ${d.msg}`).join(' · ')
        : error instanceof HttpErrorResponse && error.status === 401 ? 'La sesión no es válida. Inicie sesión de nuevo.'
        : error instanceof HttpErrorResponse && error.status === 403 ? 'No tiene permisos para administrar celdas.'
        : 'No fue posible completar la solicitud. Intente de nuevo.');
      return null;
    } finally { this.pendiente.set(false); }
  }
}
