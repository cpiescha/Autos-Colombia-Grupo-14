import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { OperadoresService } from '../../../services/operadores.service';

@Component({
  selector: 'app-operador-gestionar',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (svc.pendiente()) { <p role="status">Procesando cuenta…</p> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }
    @if (!svc.pendiente() && !cuenta()) { <p>Cuenta no disponible.</p><a routerLink="/operadores">Volver a operadores</a> }
    @if (cuenta(); as c) {
      <h1>Gestionar cuenta</h1>
      <p class="sub">Una cuenta no se elimina: se anula y puede reactivarse después.</p>

      @if (mensaje()) { <div class="aviso-ok" role="status">{{ mensaje() }}</div> }

      <div class="panel form-tarjeta">
        @if (c.estado === 'ACTIVA') {
          <div class="aviso-warn">
            <strong>Al anular la cuenta</strong>, {{ c.nombre }} no podrá iniciar sesión.
            Sus movimientos históricos se conservan.
          </div>
        } @else {
          <div class="aviso-error">
            <strong>Cuenta anulada.</strong> {{ c.nombre }} no puede iniciar sesión hasta que se reactive.
          </div>
        }

        <strong>Datos de la cuenta</strong>
        <dl class="resumen">
          <dt>Nombre</dt><dd>{{ c.nombre }}</dd>
          <dt>Usuario</dt><dd>{{ c.usuario }}</dd>
          <dt>Perfil</dt><dd>{{ c.rol }}</dd>
          <dt>Estado actual</dt>
          <dd><span class="chip" [class.ok]="c.estado === 'ACTIVA'" [class.bad]="c.estado === 'ANULADA'">{{ c.estado }}</span></dd>
          <dt>Actualización</dt>
          <dd>{{ c.actualizado_en | date: 'dd/MM/yyyy HH:mm' }}</dd>
        </dl>
        <div class="auditoria">
          <strong>Registro de auditoría</strong><br />
          Creada el {{ c.creado_en | date: 'dd/MM/yyyy HH:mm' }} · Operador #{{ codigo }}
        </div>
      </div>

      <div class="acciones-fila">
        @if (c.estado === 'ACTIVA') {
          <button class="boton peligro" (click)="cambiar()" [disabled]="svc.pendiente() || c.rol !== 'OPERADOR'">
            <span class="material-symbols-outlined">block</span> Anular cuenta
          </button>
        } @else {
          <button class="boton" (click)="cambiar()" [disabled]="svc.pendiente() || c.rol !== 'OPERADOR'">
            <span class="material-symbols-outlined">check_circle</span> Reactivar cuenta
          </button>
        }
        <a class="boton claro" routerLink="/operadores">Volver a operadores</a>
      </div>
    }
  `,
})
export class OperadorGestionarComponent {
  svc = inject(OperadoresService);
  private id = Number(inject(ActivatedRoute).snapshot.paramMap.get('id'));

  cuenta = computed(() => this.svc.obtener(this.id));
  codigo = this.svc.codigo(this.id);
  mensaje = signal('');

  constructor() { void this.svc.cargar(); }

  async cambiar() {
    const c = this.cuenta();
    if (!c || c.rol !== 'OPERADOR' || this.svc.pendiente()) return;
    this.mensaje.set('');
    const actualizada = await this.svc.cambiarEstado(c.id, c.estado === 'ACTIVA' ? 'ANULADA' : 'ACTIVA');
    if (actualizada) this.mensaje.set(actualizada.estado === 'ANULADA'
      ? 'Cuenta anulada. El operador ya no puede iniciar sesión.'
      : 'Cuenta reactivada. El operador puede iniciar sesión de nuevo.');
  }
}