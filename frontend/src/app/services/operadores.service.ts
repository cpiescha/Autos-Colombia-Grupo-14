import { Injectable, signal } from '@angular/core';
import { Rol } from '../models/auth.model';

export type Turno = 'DIURNO' | 'NOCTURNO';
export type EstadoCuenta = 'ACTIVA' | 'ANULADA';

export interface Cuenta {
  id: number;
  nombre: string;
  usuario: string;
  clave: string;
  rol: Rol;
  turno: Turno;
  estado: EstadoCuenta;
  ultimoAcceso: Date | null;
  creadoPor: string;
  creadoEn: Date;
}

// Datos simulados. En T25 se reemplazan por llamadas HttpClient a la API.
@Injectable({ providedIn: 'root' })
export class OperadoresService {
  private _lista = signal<Cuenta[]>([
    { id: 44, nombre: 'Laura Moreno', usuario: 'laura.moreno', clave: 'Admin2026', rol: 'ADMINISTRADOR', turno: 'DIURNO', estado: 'ACTIVA', ultimoAcceso: new Date(2026, 9, 22, 8, 2), creadoPor: 'Sistema', creadoEn: new Date(2026, 0, 5, 9, 0) },
    { id: 45, nombre: 'Andrés Rojas', usuario: 'andres.rojas', clave: 'Operador2026', rol: 'OPERADOR', turno: 'DIURNO', estado: 'ACTIVA', ultimoAcceso: new Date(2026, 9, 22, 7, 48), creadoPor: 'Laura Moreno', creadoEn: new Date(2026, 0, 10, 9, 0) },
    { id: 46, nombre: 'Diana Pardo', usuario: 'diana.pardo', clave: 'Operador2026', rol: 'OPERADOR', turno: 'NOCTURNO', estado: 'ACTIVA', ultimoAcceso: new Date(2026, 9, 21, 14, 10), creadoPor: 'Laura Moreno', creadoEn: new Date(2026, 0, 10, 9, 5) },
    { id: 47, nombre: 'Mateo Gil', usuario: 'mateo.gil', clave: 'Operador2026', rol: 'OPERADOR', turno: 'DIURNO', estado: 'ANULADA', ultimoAcceso: new Date(2026, 9, 18, 10, 31), creadoPor: 'Laura Moreno', creadoEn: new Date(2026, 1, 3, 9, 0) },
  ]);
  lista = this._lista.asReadonly();

  obtener(id: number): Cuenta | undefined {
    return this._lista().find((c) => c.id === id);
  }

  buscarPorUsuario(usuario: string): Cuenta | undefined {
    return this._lista().find((c) => c.usuario.toLowerCase() === usuario.trim().toLowerCase());
  }

  existeUsuario(usuario: string): boolean {
    return !!this.buscarPorUsuario(usuario);
  }

  // Toda cuenta nueva se crea con perfil OPERADOR y estado ACTIVA
  crear(datos: { nombre: string; usuario: string; clave: string; turno: Turno }, creadoPor: string): Cuenta {
    const id = Math.max(0, ...this._lista().map((c) => c.id)) + 1;
    const nueva: Cuenta = {
      ...datos,
      nombre: datos.nombre.trim(),
      usuario: datos.usuario.trim().toLowerCase(),
      id,
      rol: 'OPERADOR',
      estado: 'ACTIVA',
      ultimoAcceso: null,
      creadoPor,
      creadoEn: new Date(),
    };
    this._lista.update((l) => [...l, nueva]);
    return nueva;
  }

  // Una cuenta no se elimina: se anula (y se puede reactivar)
  cambiarEstado(id: number, estado: EstadoCuenta) {
    this._lista.update((l) => l.map((c) => (c.id === id ? { ...c, estado } : c)));
  }

  registrarAcceso(id: number) {
    this._lista.update((l) => l.map((c) => (c.id === id ? { ...c, ultimoAcceso: new Date() } : c)));
  }

  codigo(id: number): string {
    return 'OP-' + String(id).padStart(4, '0');
  }
}