import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CeldasService } from '../../../services/celdas.service';

@Component({
  selector: 'app-celda-inactivar',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (celda(); as c) {
      @if (c.ocupacion; as o) {
        <h1>No se puede inactivar la celda</h1>
        <div class="aviso-error" role="alert">
          <strong>Celda ocupada.</strong> {{ c.codigo }} tiene una permanencia abierta y no puede anularse ni retirarse.
          No se realizó ningún cambio.
        </div>

        <div class="panel form-tarjeta">
          <strong>Estado actual de {{ c.codigo }}</strong>
          <dl class="resumen">
            <dt>Tipo</dt><dd>{{ svc.etiquetaTipo(c.tipo) }}</dd>
            <dt>Vehículo asignado</dt><dd>{{ o.placa }} · {{ o.vehiculo }}</dd>
            <dt>Entrada registrada</dt><dd>{{ o.entrada | date: 'dd/MM/yyyy HH:mm' }}</dd>
            <dt>Responsable de entrada</dt><dd>{{ o.responsable }}</dd>
          </dl>
          <div class="auditoria">
            Regla aplicada: una celda con permanencia abierta no puede cambiar de estado ni retirarse físicamente.
          </div>
        </div>
        <div class="acciones-fila">
          <a class="boton" routerLink="/celdas">Volver a celdas</a>
        </div>
      } @else {
        <h1>Inactivar celda {{ c.codigo }}</h1>
        <p class="sub">La celda está libre{{ c.historial > 0 ? ', pero conserva movimientos históricos.' : ' y no tiene movimientos.' }}</p>

        <div class="panel form-tarjeta">
          @if (c.historial > 0) {
            <div class="aviso-warn">
              <strong>No se puede retirar físicamente.</strong> {{ c.codigo }} tiene historial asociado.
              Al inactivarla dejará de aparecer para la asignación automática, pero sus movimientos se conservarán.
            </div>
          } @else {
            <div class="aviso-warn">
              Al inactivarla, {{ c.codigo }} dejará de aparecer para la asignación automática. Podrá reactivarse después.
            </div>
          }

          <strong>Confirme el cambio de estado</strong>
          <dl class="resumen">
            <dt>Código</dt><dd>{{ c.codigo }}</dd>
            <dt>Tipo</dt><dd>{{ svc.etiquetaTipo(c.tipo) }}</dd>
            <dt>Estado actual</dt><dd>{{ svc.estadoVisible(c) }}</dd>
            <dt>Historial</dt><dd>{{ c.historial }} movimientos asociados</dd>
          </dl>
          @if (c.ultimoMovimiento; as m) {
            <div class="auditoria">
              <strong>Último movimiento</strong><br />
              {{ m.texto }} · {{ m.fecha | date: 'dd/MM/yyyy HH:mm' }} · Registrada por {{ m.responsable }}
            </div>
          }
        </div>

        <div class="acciones-fila">
          <button class="boton peligro" (click)="confirmar()">
            <span class="material-symbols-outlined">block</span> Inactivar celda
          </button>
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

  constructor() {
    const c = this.svc.obtener(this.codigo);
    // Si no existe o ya está inactiva, no hay nada que hacer aquí
    if (!c || c.estado === 'INACTIVA') this.router.navigate(['/celdas']);
  }

  confirmar() {
    if (this.svc.inactivar(this.codigo)) {
      this.router.navigate(['/celdas'], { queryParams: { inactivada: this.codigo } });
    }
  }
}