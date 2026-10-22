import { Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

interface ItemMenu { ruta: string; texto: string; icono: string; }

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatToolbarModule, MatSidenavModule,
    MatListModule, MatIconModule, MatButtonModule],
  template: `
    <mat-toolbar class="barra">
      <button mat-icon-button aria-label="Abrir o cerrar menú" (click)="menuAbierto.set(!menuAbierto())">
        <mat-icon>menu</mat-icon>
      </button>
      <span class="titulo">Autos Colombia</span>
      <span class="relleno"></span>
    </mat-toolbar>

    <mat-sidenav-container class="contenedor">
      <mat-sidenav mode="side" [opened]="menuAbierto()" class="menu">
        <div class="operario">Operario Diurno 1</div>
        <mat-nav-list>
          @for (item of items; track item.ruta) {
            <a mat-list-item [routerLink]="item.ruta" routerLinkActive="activo">
              <mat-icon matListItemIcon>{{ item.icono }}</mat-icon>
              <span matListItemTitle>{{ item.texto }}</span>
            </a>
          }
        </mat-nav-list>
      </mat-sidenav>
      <mat-sidenav-content class="contenido">
        <router-outlet />
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; height: 100vh; }
    .barra { background: #1565c0; color: #fff; flex: 0 0 auto; }
    .titulo { margin-left: 8px; font-weight: 500; letter-spacing: .3px; }
    .relleno { flex: 1; }
    .contenedor { flex: 1; }
    .menu {
      width: 240px; padding-top: 8px; background: #0d47a1; color: #fff; border-radius: 0;
      --mat-list-list-item-label-text-color: #fff;
      --mat-list-list-item-leading-icon-color: #fff;
      --mat-list-list-item-hover-label-text-color: #fff;
      --mat-list-list-item-focus-label-text-color: #fff;
    }
    .operario { padding: 8px 16px 12px; font-size: 13px; opacity: .8; }
    .activo { background: rgba(255, 255, 255, .18); }
    .contenido { padding: 24px; background: #e8edf3; }
    @media (max-width: 720px) { .contenido { padding: 12px; } }
  `],
})
export class ShellComponent {
  menuAbierto = signal(true);
  items: ItemMenu[] = [
    { ruta: '/entrada', texto: 'Entrada', icono: 'login' },
    { ruta: '/salida', texto: 'Salida', icono: 'logout' },
    { ruta: '/ocupacion', texto: 'Ocupación', icono: 'local_parking' },
  ];
}
