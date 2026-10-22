import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
 
interface ItemMenu { ruta: string; texto: string; }
 
@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="barra">
      <span class="titulo">Autos Colombia</span>
    </header>
 
    <div class="cuerpo">
      <nav class="menu" aria-label="Menú principal">
        <div class="operario">Operario Diurno 1</div>
        @for (item of items; track item.ruta) {
          <a class="opcion" [routerLink]="item.ruta" routerLinkActive="activo" ariaCurrentWhenActive="page">
            {{ item.texto }}
          </a>
        }
      </nav>
 
      <main class="contenido">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; height: 100vh; }
 
    .barra {
      flex: 0 0 54px; display: flex; align-items: center; justify-content: center;
      background: #1565c0; color: #fff;
    }
    .titulo { font-size: 18px; font-weight: 700; }
 
    .cuerpo { flex: 1; display: flex; min-height: 0; }
 
    .menu { flex: 0 0 240px; background: #0d47a1; color: #fff; padding: 16px 8px; overflow-y: auto; }
    .operario { padding: 0 12px 14px; font-size: 12px; opacity: .85; }
    .opcion {
      display: block; padding: 9px 12px; margin-bottom: 4px; border-radius: 4px;
      color: #fff; font-size: 14px; text-decoration: none;
    }
    .opcion:hover { background: rgba(255, 255, 255, .12); }
    .opcion:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
    .opcion.activo { background: #1565c0; font-weight: 700; }
 
    .contenido { flex: 1; padding: 24px 32px; background: #f5f7fa; overflow-y: auto; }
 
    @media (max-width: 720px) {
      .cuerpo { flex-direction: column; }
      .menu { flex: 0 0 auto; display: flex; flex-wrap: wrap; gap: 4px; padding: 8px; }
      .operario { width: 100%; padding: 0 8px 4px; }
      .opcion { margin-bottom: 0; }
      .contenido { padding: 16px; }
    }
  `],
})
export class ShellComponent {
  items: ItemMenu[] = [
    { ruta: '/entrada', texto: 'Entrada' },
    { ruta: '/salida', texto: 'Salida' },
    { ruta: '/ocupacion', texto: 'Ocupación' },
  ];
}
