import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { Rol } from '../models/auth.model';

interface ItemMenu { ruta: string; texto: string; icono: string; roles: Rol[]; }

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="barra">
      <strong class="marca">Autos Colombia</strong>
      <span class="subtitulo">{{ subtitulo() }}</span>
      <span class="espacio"></span>
      <span class="usuario">{{ auth.sesion()?.nombre }} · {{ etiquetaRol() }}</span>
      <button class="salir" (click)="auth.logout()">
        <span class="material-symbols-outlined">power_settings_new</span> Cerrar sesión
      </button>
    </header>
    <div class="cuerpo">
      <nav class="menu" aria-label="Menú principal">
        <div class="rol">{{ etiquetaRol() }}</div>
        @for (item of menu(); track item.ruta) {
          <a [routerLink]="item.ruta" routerLinkActive="activo">
            <span class="material-symbols-outlined">{{ item.icono }}</span> {{ item.texto }}
          </a>
        }
      </nav>
      <main class="contenido"><router-outlet /></main>
    </div>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; height: 100vh; }
    .barra { background: #2068bd; color: #fff; height: 54px; display: flex; align-items: center; gap: 18px; padding: 0 24px; flex: 0 0 auto; }
    .marca { font-size: 20px; }
    .subtitulo { font-size: 13px; color: #fff; margin: 0; }
    .espacio { flex: 1; }
    .usuario { font-size: 13px; font-weight: 600; }
    .salir { display: flex; align-items: center; gap: 4px; background: rgba(255,255,255,.15); color: #fff; border: 0; border-radius: 16px; padding: 6px 12px; cursor: pointer; font: inherit; font-size: 13px; }
    .salir:hover { background: rgba(255,255,255,.28); }
    .cuerpo { display: flex; flex: 1; min-height: 0; }
    .menu { width: 240px; background: #164f9e; display: flex; flex-direction: column; gap: 4px; padding: 12px; flex: 0 0 auto; box-sizing: border-box; }
    .rol { color: #fff; opacity: .85; font-size: 13px; font-weight: 600; padding: 4px 4px 10px; }
    .menu a { color: #fff; text-decoration: none; padding: 11px 16px; border-radius: 8px; display: flex; align-items: center; gap: 10px; }
    .menu a:hover { background: rgba(255,255,255,.1); }
    .menu a.activo { background: #2068bd; font-weight: 600; }
    .contenido { flex: 1; padding: 24px 32px; background: #f4f6f8; overflow: auto; }
    @media (max-width: 720px) {
      .cuerpo { flex-direction: column; }
      .menu { width: auto; flex-direction: row; flex-wrap: wrap; }
      .rol { width: 100%; }
      .subtitulo { display: none; }
    }
  `],
})
export class ShellComponent {
  auth = inject(AuthService);

  private items: ItemMenu[] = [
    { ruta: '/inicio', texto: 'Inicio', icono: 'home', roles: ['ADMINISTRADOR', 'OPERADOR'] },
    { ruta: '/operadores', texto: 'Operadores', icono: 'badge', roles: ['ADMINISTRADOR'] },
    { ruta: '/celdas', texto: 'Celdas', icono: 'local_parking', roles: ['ADMINISTRADOR'] },
    { ruta: '/entrada', texto: 'Entrada', icono: 'login', roles: ['ADMINISTRADOR', 'OPERADOR'] },
    { ruta: '/salida', texto: 'Salida', icono: 'logout', roles: ['ADMINISTRADOR', 'OPERADOR'] },
    { ruta: '/ocupacion', texto: 'Ocupación', icono: 'grid_view', roles: ['ADMINISTRADOR', 'OPERADOR'] },
    { ruta: '/presentes', texto: 'Vehículos presentes', icono: 'directions_car', roles: ['OPERADOR'] },
    { ruta: '/reportes', texto: 'Reportes', icono: 'bar_chart', roles: ['ADMINISTRADOR'] },
  ];

  menu = computed(() => this.items.filter((i) => i.roles.includes(this.auth.rol()!)));
  etiquetaRol = computed(() => (this.auth.rol() === 'ADMINISTRADOR' ? 'Administrador' : 'Operador'));
  subtitulo = computed(() =>
    this.auth.rol() === 'ADMINISTRADOR' ? 'Administración del parqueadero' : 'Registro de entradas y salidas'
  );
}