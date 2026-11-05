import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export type EstadoCuenta = 'ACTIVA' | 'ANULADA';

export interface Cuenta {
  id: number;
  operador_id: number;
  nombre: string;
  usuario: string;
  rol: 'ADMINISTRADOR' | 'OPERADOR';
  estado: EstadoCuenta;
  creado_en: string;
  actualizado_en: string;
}

interface CrearOperador { nombre: string; usuario: string; clave: string; }

@Injectable({ providedIn: 'root' })
export class OperadoresService {
  private http = inject(HttpClient);
  private _lista = signal<Cuenta[]>([]);
  lista = this._lista.asReadonly();
  pendiente = signal(false);
  error = signal('');

  obtener(id: number): Cuenta | undefined {
    return this._lista().find(c => c.id === id);
  }

  async cargar(): Promise<boolean> {
    if (this.pendiente()) return false;
    this._lista.set([]);
    return (await this.ejecutar(async () => {
      this._lista.set(await firstValueFrom(this.http.get<Cuenta[]>('/api/operadores')));
      return true;
    })) === true;
  }

  crear(datos: CrearOperador): Promise<Cuenta | null> {
    return this.ejecutar(async () => {
      const cuenta = await firstValueFrom(this.http.post<Cuenta>('/api/operadores', datos));
      this._lista.update(lista => [...lista, cuenta]);
      return cuenta;
    });
  }

  cambiarEstado(id: number, estado: EstadoCuenta): Promise<Cuenta | null> {
    return this.ejecutar(async () => {
      const cuenta = await firstValueFrom(this.http.patch<Cuenta>(`/api/operadores/${id}/estado`, { estado }));
      this._lista.update(lista => lista.map(c => c.id === id ? cuenta : c));
      return cuenta;
    });
  }

  codigo(id: number): string { return 'OP-' + String(id).padStart(4, '0'); }

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
        : error instanceof HttpErrorResponse && error.status === 403 ? 'No tiene permisos para administrar operadores.'
        : 'No fue posible completar la solicitud. Intente de nuevo.');
      return null;
    } finally { this.pendiente.set(false); }
  }
}
