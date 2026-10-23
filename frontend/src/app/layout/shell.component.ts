import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

interface ItemMenu { ruta: string; texto: string; }

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="barra">Autos Colombia</header>
    <div class="cuerpo">
      <nav class="menu" aria-label="Menú principal">
        <div class="operario">Operario Diurno 1</div>
        @for (item of items; track item.ruta) {
          <a [routerLink]="item.ruta" routerLinkActive="activo">{{ item.texto }}</a>
        }
      </nav>
      <main class="contenido"><router-outlet /></main>
    </div>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; height: 100vh; }
    .barra { background: #1565c0; color: #fff; height: 56px; display: flex; align-items: center; justify-content: center; font-weight: 500; font-size: 18px; flex: 0 0 auto; }
    .cuerpo { display: flex; flex: 1; min-height: 0; }
    .menu { width: 240px; background: #0d47a1; display: flex; flex-direction: column; padding: 8px 0; flex: 0 0 auto; }
    .operario { color: #fff; opacity: .8; font-size: 13px; padding: 8px 16px 12px; }
    .menu a { color: #fff; text-decoration: none; padding: 12px 16px; }
    .menu a:hover { background: rgba(255, 255, 255, .1); }
    .menu a.activo { background: #1565c0; font-weight: 500; }
    .contenido { flex: 1; padding: 24px; background: #fff; overflow: auto; }
    @media (max-width: 720px) {
      .cuerpo { flex-direction: column; }
      .menu { width: auto; flex-direction: row; flex-wrap: wrap; }
      .operario { width: 100%; }
    }
  `],
})
export class ShellComponent {
  items: ItemMenu[] = [
    { ruta: '/inicio', texto: 'Inicio' },
    { ruta: '/entrada', texto: 'Entrada' },
    { ruta: '/salida', texto: 'Salida' },
    { ruta: '/ocupacion', texto: 'Ocupación' },
    { ruta: '/presentes', texto: 'Vehículos presentes' },
    { ruta: '/reportes', texto: 'Reportes' },
  ];
}