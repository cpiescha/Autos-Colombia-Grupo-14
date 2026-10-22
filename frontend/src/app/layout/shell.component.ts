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
      <span class="subtitulo">Control de acceso</span>
      <span class="relleno"></span>
      <mat-icon aria-hidden="true">badge</mat-icon>
      <span class="operario">Operario</span>
    </mat-toolbar>

    <mat-sidenav-container class="contenedor">
      <mat-sidenav mode="side" [opened]="menuAbierto()" class="menu">
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
    .barra { background: #1f2933; color: #fff; border-bottom: 4px solid #f2b705; flex: 0 0 auto; }
    .titulo { margin-left: 8px; font-weight: 500; letter-spacing: .3px; }
    .subtitulo { margin-left: 12px; opacity: .7; font-size: 14px; }
    .relleno { flex: 1; }
    .operario { margin-left: 8px; font-size: 14px; }
    .contenedor { flex: 1; }
    .menu { width: 240px; padding-top: 8px; }
    .activo { background: rgba(242, 183, 5, .22); }
    .contenido { padding: 24px; background: #f4f5f7; }
    @media (max-width: 720px) { .subtitulo, .operario { display: none; } .contenido { padding: 12px; } }
  `],
})
export class ShellComponent {
  menuAbierto = signal(true);
  items: ItemMenu[] = [
    { ruta: '/consulta', texto: 'Consulta', icono: 'search' },
    { ruta: '/ingreso', texto: 'Ingreso', icono: 'login' },
    { ruta: '/salida', texto: 'Salida', icono: 'logout' },
    { ruta: '/ocupacion', texto: 'Ocupación', icono: 'local_parking' },
  ];
}
