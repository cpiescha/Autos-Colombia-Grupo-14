import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Sesion } from '../models/auth.model';
import { OperadoresService } from '../services/operadores.service';

const CLAVE = 'sesion_autos_colombia';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private router = inject(Router);
  private cuentas = inject(OperadoresService);
  private _sesion = signal<Sesion | null>(this.leer());

  sesion = this._sesion.asReadonly();
  autenticado = computed(() => this._sesion() !== null);
  rol = computed(() => this._sesion()?.rol ?? null);

  // En T25 esto se reemplaza por la llamada a la API de login
  login(usuario: string, clave: string): 'OK' | 'INVALIDO' | 'ANULADA' {
    const c = this.cuentas.buscarPorUsuario(usuario);
    if (!c || c.clave !== clave) return 'INVALIDO';
    if (c.estado === 'ANULADA') return 'ANULADA';

    const s: Sesion = { usuario: c.usuario, nombre: c.nombre, rol: c.rol, token: 'token-demo-' + Date.now() };
    sessionStorage.setItem(CLAVE, JSON.stringify(s));
    this._sesion.set(s);
    this.cuentas.registrarAcceso(c.id);
    return 'OK';
  }

  logout(): void {
    sessionStorage.removeItem(CLAVE);
    this._sesion.set(null);
    this.router.navigate(['/login']);
  }

  rutaInicial(): string {
    return '/inicio';
  }

  private leer(): Sesion | null {
    try {
      const t = sessionStorage.getItem(CLAVE);
      return t ? (JSON.parse(t) as Sesion) : null;
    } catch {
      return null;
    }
  }
}