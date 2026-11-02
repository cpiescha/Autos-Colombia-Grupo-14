import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { OperadoresService } from '../../../services/operadores.service';

type Filtro = 'todos' | 'ACTIVA' | 'ANULADA';

@Component({
  selector: 'app-operadores',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <h1>Operadores</h1>
    <p class="sub">Cuentas internas con acceso al registro de entradas y salidas.</p>

    <div class="herramientas">
      <input class="buscador" placeholder="Buscar por nombre o usuario" aria-label="Buscar por nombre o usuario"
             (input)="texto.set($any($event.target).value)" />
      <button class="boton claro" type="button" (click)="siguienteFiltro()">
        <span class="material-symbols-outlined">filter_list</span> Filtrar: {{ etiquetaFiltro() }}
      </button>
      <span class="espacio"></span>
      <a class="boton" routerLink="/operadores/nuevo">
        <span class="material-symbols-outlined">person_add</span> Crear operador
      </a>
    </div>

    <div class="panel">
      <strong>Cuentas registradas · {{ filtradas().length }}</strong>

      @if (filtradas().length === 0) {
        <p class="vacio">No hay cuentas que coincidan con la búsqueda o el filtro.</p>
      } @else {
        <table class="tabla">
          <thead>
            <tr><th>Operador</th><th>Usuario</th><th>Perfil</th><th>Estado</th><th>Último acceso</th><th>Acción</th></tr>
          </thead>
          <tbody>
            @for (c of filtradas(); track c.id) {
              <tr>
                <td>{{ c.nombre }}</td>
                <td>{{ c.usuario }}</td>
                <td>{{ c.rol }}</td>
                <td><span class="chip" [class.ok]="c.estado === 'ACTIVA'" [class.bad]="c.estado === 'ANULADA'">{{ c.estado }}</span></td>
                <td>{{ c.ultimoAcceso ? (c.ultimoAcceso | date: 'dd/MM/yyyy HH:mm') : 'Nunca' }}</td>
                <td>
                  @if (c.rol === 'OPERADOR') {
                    <a class="enlace" [routerLink]="['/operadores', c.id]">Gestionar</a>
                  } @else { — }
                </td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
})
export class OperadoresComponent {
  private svc = inject(OperadoresService);

  texto = signal('');
  filtro = signal<Filtro>('todos');

  etiquetaFiltro = computed(() => ({ todos: 'todos', ACTIVA: 'activas', ANULADA: 'anuladas' })[this.filtro()]);

  filtradas = computed(() => {
    const t = this.texto().toLowerCase().trim();
    const f = this.filtro();
    return this.svc.lista().filter(
      (c) =>
        (f === 'todos' || c.estado === f) &&
        (!t || c.nombre.toLowerCase().includes(t) || c.usuario.toLowerCase().includes(t))
    );
  });

  siguienteFiltro() {
    const orden: Filtro[] = ['todos', 'ACTIVA', 'ANULADA'];
    this.filtro.set(orden[(orden.indexOf(this.filtro()) + 1) % orden.length]);
  }
}