import { Injectable, signal } from '@angular/core';

export type TipoCelda = 'AUTOMOVIL' | 'MOTO';
export type EstadoCelda = 'ACTIVA' | 'INACTIVA';
export type EstadoVisible = 'OCUPADA' | 'ACTIVA · LIBRE' | 'INACTIVA';

export interface Ocupacion { placa: string; vehiculo: string; entrada: Date; responsable: string; }
export interface Movimiento { texto: string; fecha: Date; responsable: string; }

export interface Celda {
  codigo: string;
  tipo: TipoCelda;
  estado: EstadoCelda;
  ocupacion: Ocupacion | null;
  historial: number;
  ultimoMovimiento: Movimiento | null;
}

const pad = (n: number) => String(n).padStart(2, '0');
const nueva = (codigo: string, tipo: TipoCelda): Celda =>
  ({ codigo, tipo, estado: 'ACTIVA', ocupacion: null, historial: 0, ultimoMovimiento: null });

// Datos simulados. En T25 se reemplazan por llamadas HttpClient a la API.
function inicial(): Celda[] {
  const lista: Celda[] = [
    ...Array.from({ length: 70 }, (_, i) => nueva('A-' + pad(i + 1), 'AUTOMOVIL')),
    ...Array.from({ length: 10 }, (_, i) => nueva('M-' + pad(i + 1), 'MOTO')),
  ];
  const poner = (codigo: string, cambios: Partial<Celda>) => {
    const i = lista.findIndex((c) => c.codigo === codigo);
    lista[i] = { ...lista[i], ...cambios };
  };
  poner('A-01', {
    historial: 12,
    ocupacion: { placa: 'INS001', vehiculo: 'Kia Rio Azul', entrada: new Date(2026, 9, 22, 7, 41), responsable: 'Andrés Rojas · Operador' },
  });
  poner('A-12', { historial: 8 });
  poner('M-10', {
    historial: 4,
    ultimoMovimiento: { texto: 'Salida de MNO72', fecha: new Date(2026, 9, 17, 18, 43), responsable: 'Diana Pardo' },
  });
  return lista;
}

@Injectable({ providedIn: 'root' })
export class CeldasService {
  private _lista = signal<Celda[]>(inicial());
  lista = this._lista.asReadonly();

  obtener(codigo: string): Celda | undefined {
    return this._lista().find((c) => c.codigo === codigo);
  }
  existe(codigo: string): boolean {
    return !!this.obtener(codigo.toUpperCase());
  }

  // Las celdas nuevas se crean activas y libres
  crear(codigo: string, tipo: TipoCelda) {
    this._lista.update((l) => [...l, nueva(codigo.toUpperCase(), tipo)]);
  }

  // Regla: una celda con permanencia abierta no puede inactivarse
  inactivar(codigo: string): boolean {
    const c = this.obtener(codigo);
    if (!c || c.ocupacion) return false;
    this._lista.update((l) => l.map((x) => (x.codigo === codigo ? { ...x, estado: 'INACTIVA' } : x)));
    return true;
  }
  reactivar(codigo: string) {
    this._lista.update((l) => l.map((x) => (x.codigo === codigo ? { ...x, estado: 'ACTIVA' } : x)));
  }

  estadoVisible(c: Celda): EstadoVisible {
    if (c.estado === 'INACTIVA') return 'INACTIVA';
    return c.ocupacion ? 'OCUPADA' : 'ACTIVA · LIBRE';
  }
  etiquetaTipo(t: TipoCelda): string {
    return t === 'MOTO' ? 'MOTO' : 'AUTOMÓVIL';
  }
}