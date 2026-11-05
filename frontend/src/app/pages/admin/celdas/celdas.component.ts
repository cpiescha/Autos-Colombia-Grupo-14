import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CeldasService } from '../../../services/celdas.service';

type Filtro = 'todas' | 'libres' | 'ocupadas' | 'inactivas';

@Component({
  selector: 'app-celdas',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1>Celdas</h1>
    <p class="sub">Capacidad configurada: {{ resumen().total }} celdas · {{ resumen().motos }} motos y {{ resumen().autos }} automóviles.</p>

    @if (creada) { <div class="aviso-ok" role="status">Celda {{ creada }} creada correctamente. Quedó activa y libre.</div> }
    @if (inactivada) { <div class="aviso-ok" role="status">Celda {{ inactivada }} inactivada. Su historial se conserva.</div> }

    @if (svc.pendiente()) { <p role="status">Procesando celdas…</p> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }} <button class="enlace" (click)="svc.cargar()" [disabled]="svc.pendiente()">Reintentar</button></div> }
    @if (retirada) { <div class="aviso-ok" role="status">Solicitud de retiro de {{ retirada }} completada. Si tenía historial, se conservó inactiva.</div> }

    <div class="herramientas">
      <input class="buscador" placeholder="Buscar por código" aria-label="Buscar por código"
             (input)="texto.set($any($event.target).value)" />
      <button class="boton claro" type="button" (click)="siguienteFiltro()">
        <span class="material-symbols-outlined">filter_list</span> Filtrar: {{ filtro() }}
      </button>
      <span class="espacio"></span>
      <a class="boton" routerLink="/celdas/nueva">
        <span class="material-symbols-outlined">add</span> Crear celda
      </a>
    </div>

    <div class="panel">
      <strong>Celdas administradas · {{ filtradas().length }}</strong>

      @if (!svc.pendiente() && !svc.error() && filtradas().length === 0) {
        <p class="vacio">No hay celdas que coincidan con la búsqueda o el filtro.</p>
      } @else {
        <table class="tabla">
          <thead>
            <tr><th>Código</th><th>Tipo</th><th>Estado</th><th>Ocupación actual</th><th>Historial</th><th>Acción</th></tr>
          </thead>
          <tbody>
            @for (c of filtradas(); track c.id) {
              <tr>
                <td><strong>{{ c.codigo }}</strong></td>
                <td>
                  <span class="material-symbols-outlined">{{ c.categoria === 'MOTO' ? 'two_wheeler' : 'directions_car' }}</span>
                  {{ svc.etiquetaTipo(c.categoria) }}
                </td>
                <td>
                  <span class="chip" [class.warn]="svc.estadoVisible(c) === 'OCUPADA'"
                        [class.ok]="svc.estadoVisible(c) === 'ACTIVA · LIBRE'"
                        [class.bad]="svc.estadoVisible(c) === 'INACTIVA'">{{ svc.estadoVisible(c) }}</span>
                </td>
                <td>
                  @if (c.estado === 'inactiva') { No asignable }
                  @else if (c.estado === 'ocupada') { {{ c.placa }} }
                  @else { Disponible }
                </td>
                <td>{{ c.tiene_historial ? 'Con historial' : 'Sin historial' }}</td>
                <td>
                  @if (c.estado !== 'inactiva') {
                    <a class="enlace" [routerLink]="['/celdas', c.codigo, 'inactivar']">Inactivar</a>
                  } @else {
                    <button class="enlace" type="button" (click)="reactivar(c.id)" [disabled]="svc.pendiente()">Reactivar</button>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
})
export class CeldasComponent {
  svc = inject(CeldasService);
  private q = inject(ActivatedRoute).snapshot.queryParamMap;
  creada = this.q.get('creada');
  inactivada = this.q.get('inactivada');
  retirada = this.q.get('retirada');

  constructor() { void this.svc.cargar(); }

  texto = signal('');
  filtro = signal<Filtro>('todas');

  resumen = computed(() => {
    const l = this.svc.lista();
    return { total: l.length, motos: l.filter((c) => c.categoria === 'MOTO').length, autos: l.filter((c) => c.categoria === 'AUTOMOVIL').length };
  });

  filtradas = computed(() => {
    const t = this.texto().toUpperCase().trim();
    const f = this.filtro();
    return this.svc.lista().filter((c) => {
      const v = this.svc.estadoVisible(c);
      const okFiltro =
        f === 'todas' ||
        (f === 'libres' && v === 'ACTIVA · LIBRE') ||
        (f === 'ocupadas' && v === 'OCUPADA') ||
        (f === 'inactivas' && v === 'INACTIVA');
      return okFiltro && (!t || c.codigo.includes(t));
    });
  });

  siguienteFiltro() {
    const orden: Filtro[] = ['todas', 'libres', 'ocupadas', 'inactivas'];
    this.filtro.set(orden[(orden.indexOf(this.filtro()) + 1) % orden.length]);
  }
  reactivar(id: number) { void this.svc.cambiarEstado(id, 'ACTIVA'); }
}