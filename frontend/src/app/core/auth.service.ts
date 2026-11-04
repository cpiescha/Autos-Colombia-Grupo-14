import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom, timeout } from 'rxjs';
import { ApiUsuario, LoginResponse, Sesion } from '../models/auth.model';

const CLAVE = 'sesion_autos_colombia';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private router = inject(Router);
  private http = inject(HttpClient);
  private _sesion = signal<Sesion | null>(null);
  private avisoLogin = '';
  private tokenPendiente = this.leerToken();
  private restauracion?: Promise<boolean>;
  private revision = 0;

  sesion = this._sesion.asReadonly();
  autenticado = computed(() => this._sesion() !== null);
  rol = computed(() => this._sesion()?.rol ?? null);

  token(): string | null {
    return this._sesion()?.token ?? this.tokenPendiente;
  }

  async restaurar(): Promise<boolean> {
    if (this.autenticado()) return true;
    if (!this.tokenPendiente) return false;
    return this.restauracion ??= this.validarSesion();
  }

  private async validarSesion(): Promise<boolean> {
    const token = this.tokenPendiente!;
    const revision = this.revision;
    try {
      const usuario = await firstValueFrom(this.http.get<ApiUsuario>('/api/auth/me').pipe(timeout(15000)));
      if (revision !== this.revision) return false;
      this.guardar(usuario, token);
      return true;
    } catch {
      if (revision === this.revision) {
        this.invalidar(false, 'La sesión no es válida o venció. Inicie sesión nuevamente.');
      }
      return false;
    }
  }

  async login(usuario: string, clave: string): Promise<boolean> {
    this.invalidar(false);
    const revision = this.revision;
    const respuesta = await firstValueFrom(this.http.post<LoginResponse>('/api/auth/login', {
      username: usuario, password: clave,
    }).pipe(timeout(15000)));
    if (revision !== this.revision) return false;
    this.guardar(respuesta.user, respuesta.access_token);
    return true;
  }

  logout(): void {
    const token = this.token();
    // Clear locally even when the server is unreachable. Logout is stateless on the API.
    this.invalidar();
    if (token) this.http.post<void>('/api/auth/logout', {}, {
      headers: { Authorization: `Bearer ${token}` },
    }).pipe(timeout(15000)).subscribe({ error: () => {} });
  }

  invalidar(redirigir = true, aviso = ''): void {
    this.revision++;
    this.avisoLogin = aviso;
    this.tokenPendiente = null;
    this.restauracion = undefined;
    this._sesion.set(null);
    try { sessionStorage.removeItem(CLAVE); } catch { /* Storage can be unavailable. */ }
    if (redirigir) void this.router.navigate(['/login']);
  }

  consumirAvisoLogin(): string {
    const aviso = this.avisoLogin;
    this.avisoLogin = '';
    return aviso;
  }

  rutaInicial(): string { return '/inicio'; }

  private guardar(usuario: ApiUsuario, token: string): void {
    if (!token || !usuario || typeof usuario.username !== 'string' || typeof usuario.name !== 'string'
      || !['ADMINISTRADOR', 'OPERADOR'].includes(usuario.role)) {
      throw new Error('Respuesta de autenticación inválida');
    }
    const sesion: Sesion = { usuario: usuario.username, nombre: usuario.name, rol: usuario.role, token };
    this.tokenPendiente = null;
    this._sesion.set(sesion);
    try { sessionStorage.setItem(CLAVE, JSON.stringify({ token })); } catch { /* In-memory session only. */ }
  }

  private leerToken(): string | null {
    try {
      const valor = JSON.parse(sessionStorage.getItem(CLAVE) ?? 'null');
      return typeof valor?.token === 'string' && valor.token ? valor.token : null;
    } catch { return null; }
  }
}
