import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AccesoService } from '../../services/acceso.service';
import { CorreccionAuditoria } from '../../models/models';

type Fase = 'editar' | 'listo';

@Component({
  selector: 'app-correccion',
  standalone: true,
  imports: [FormsModule, DatePipe, RouterLink],
  template: `
    @switch (fase()) {

      @case ('editar') {
        <h1>Corregir celda</h1>

        @if (registro(); as r) {
          <div class="tarjeta-info">
            <h2>Movimiento abierto</h2>
            <p>{{ r.placa }}@if (vehiculo(); as v) { · {{ v.marca }} {{ v.color }} }</p>
            <p>Celda asignada: {{ r.celda }}</p>
            <p>Tipo compatible: {{ tipoLegible() }}</p>
          </div>

          <label class="etiqueta" for="nuevaCelda">Nueva celda (solo libres compatibles)</label>
          <input
            id="nuevaCelda"
            class="entrada-texto"
            [(ngModel)]="nuevaCelda"
            list="celdas-compatibles"
            placeholder="A-02"
            maxlength="6"
            autocomplete="off"
          />
          <datalist id="celdas-compatibles">
            @for (c of compatibles(); track c.codigo) {
              <option [value]="c.codigo"></option>
            }
          </datalist>

          <div class="alerta alerta-info">
            No se listan motos ni celdas ocupadas. La corrección no crea un movimiento extra.
          </div>

          @if (errorMensaje(); as m) {
            <div class="alerta alerta-error" role="alert">{{ m }}</div>
          }

          <div class="fila">
            <button type="button" class="btn" (click)="guardar()" [disabled]="!nuevaCelda.trim()">
              Guardar corrección
            </button>
            <a class="btn btn-claro" routerLink="/presentes">Cancelar</a>
          </div>
        } @else {
          <div class="alerta alerta-error" role="alert">
            No se encontró la permanencia solicitada. Vuelve a Vehículos presentes.
          </div>
          <a class="btn btn-claro" routerLink="/presentes">Volver</a>
        }
      }

      @case ('listo') {
        <h1>Celda actualizada</h1>
        @if (auditoria(); as a) {
          <div class="alerta alerta-ok" role="status">
            Celda actualizada de {{ a.celdaAnterior }} a {{ a.celdaNueva }}.
            Corrigió Operario {{ a.operario }} — {{ a.fecha | date: 'dd/MM/yyyy HH:mm' }}.
          </div>

          <div class="tarjeta-info">
            <h2>Auditoría</h2>
            <p>Vehículo: {{ a.placa }}</p>
            <p>Celda anterior: {{ a.celdaAnterior }}</p>
            <p>Celda nueva: {{ a.celdaNueva }}</p>
            <p>Sin duplicar vehículos ni celdas abiertas</p>
          </div>

          <div class="fila">
            <a class="btn" routerLink="/presentes">Volver a presentes</a>
          </div>
        }
      }
    }
  `,
  styleUrls: ['../paginas.scss'],
})
export class CorreccionComponent {
  private readonly acceso = inject(AccesoService);
  private readonly ruta = inject(ActivatedRoute);

  readonly idRegistro = Number(this.ruta.snapshot.paramMap.get('id'));

  readonly registro = computed(() =>
    this.acceso.activos().find((r) => r.id === this.idRegistro),
  );
  readonly vehiculo = computed(() => {
    const r = this.registro();
    return r ? this.acceso.buscarVehiculo(r.placa) : undefined;
  });
  readonly compatibles = computed(() => this.acceso.celdasCompatibles(this.idRegistro));
  readonly tipoLegible = computed(() => {
    const r = this.registro();
    if (!r) return '';
    return r.celda.startsWith('M') ? 'motocicleta' : 'automóvil';
  });

  readonly fase = signal<Fase>('editar');
  readonly auditoria = signal<CorreccionAuditoria | undefined>(undefined);
  readonly errorMensaje = signal<string>('');

  nuevaCelda = '';

  guardar(): void {
    this.errorMensaje.set('');
    const resultado = this.acceso.corregirCelda(this.idRegistro, this.nuevaCelda);
    if (!resultado.ok || !resultado.dato) {
      this.errorMensaje.set(resultado.mensaje);
      return;
    }
    this.auditoria.set(resultado.dato);
    this.fase.set('listo');
  }
}
