import { Component, computed, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CeldasService } from '../../../services/celdas.service';

@Component({
  selector: 'app-celda-inactivar',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (svc.pendiente()) { <p role="status">Procesando celda…</p> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }
    @if (!svc.pendiente() && !celda()) { <p>Celda no disponible.</p><a routerLink="/celdas">Volver a celdas</a> }
    @if (celda(); as c) {
      @if (c.estado === 'ocupada') {
        <h1>No se puede inactivar la celda</h1>
        <div class="aviso-error" role="alert">
          <strong>Celda ocupada.</strong> {{ c.codigo }} tiene una permanencia abierta y no puede anularse ni retirarse.
          No se realizó ningún cambio.
        </div>
        <div class="panel form-tarjeta">
          <strong>Estado actual de {{ c.codigo }}</strong>
          <dl class="resumen">
            <dt>Tipo</dt><dd>{{ svc.etiquetaTipo(c.categoria) }}</dd>
            <dt>Vehículo asignado</dt><dd>{{ c.placa }}</dd>
          </dl>
          <div class="auditoria">
            Regla aplicada: una celda con permanencia abierta no puede cambiar de estado ni retirarse físicamente.
          </div>
        </div>
        <div class="acciones-fila"><a class="boton" routerLink="/celdas">Volver a celdas</a></div>
      } @else {
        <h1>Inactivar celda {{ c.codigo }}</h1>
        <p class="sub">La celda no está ocupada{{ c.tiene_historial ? ', pero conserva movimientos históricos.' : ' y no tiene movimientos.' }}</p>
        <div class="panel form-tarjeta">
          <div class="aviso-warn">
            @if (c.tiene_historial) {
              <strong>No se puede retirar físicamente.</strong> {{ c.codigo }} tiene historial asociado.
              Al inactivarla dejará de aparecer para la asignación automática, pero sus movimientos se conservarán.
            } @else {
              Puede inactivarla para reactivarla después o retirarla definitivamente si sigue sin historial.
            }
          </div>
          <strong>Confirme el cambio de estado</strong>
          <dl class="resumen">
            <dt>Código</dt><dd>{{ c.codigo }}</dd>
            <dt>Tipo</dt><dd>{{ svc.etiquetaTipo(c.categoria) }}</dd>
            <dt>Estado actual</dt><dd>{{ svc.estadoVisible(c) }}</dd>
            <dt>Historial</dt><dd>{{ c.tiene_historial ? 'Con historial' : 'Sin historial' }}</dd>
          </dl>
        </div>
        <div class="acciones-fila">
          <button class="boton peligro" (click)="confirmar()" [disabled]="svc.pendiente() || c.estado === 'inactiva'">
            <span class="material-symbols-outlined">block</span> Inactivar celda
          </button>
          @if (!c.tiene_historial) {
            <button class="boton peligro" (click)="retirar()" [disabled]="svc.pendiente()">Retirar definitivamente</button>
          }
          <a class="boton claro" routerLink="/celdas">Cancelar</a>
        </div>
      }
    }
  `,
})
export class CeldaInactivarComponent {
  svc = inject(CeldasService);
  private router = inject(Router);
  private codigo = inject(ActivatedRoute).snapshot.paramMap.get('codigo') ?? '';
  celda = computed(() => this.svc.obtener(this.codigo));

  constructor() { void this.svc.cargar(); }

  async confirmar() {
    const celda = this.celda();
    if (!celda || celda.estado !== 'disponible' || this.svc.pendiente()) return;
    if (await this.svc.cambiarEstado(celda.id, 'INACTIVA')) {
      await this.router.navigate(['/celdas'], { queryParams: { inactivada: celda.codigo } });
    }
  }

  async retirar() {
    const celda = this.celda();
    if (!celda || celda.estado === 'ocupada' || celda.tiene_historial || this.svc.pendiente()) return;
    if (await this.svc.retirar(celda.id)) {
      await this.router.navigate(['/celdas'], { queryParams: { retirada: celda.codigo } });
    }
  }
}
