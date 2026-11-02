import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { OperadoresService } from '../../../services/operadores.service';

@Component({
  selector: 'app-operador-gestionar',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
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
          <dt>Turno</dt><dd>{{ c.turno }}</dd>
          <dt>Estado actual</dt>
          <dd><span class="chip" [class.ok]="c.estado === 'ACTIVA'" [class.bad]="c.estado === 'ANULADA'">{{ c.estado }}</span></dd>
          <dt>Último acceso</dt>
          <dd>{{ c.ultimoAcceso ? (c.ultimoAcceso | date: 'dd/MM/yyyy HH:mm') : 'Nunca' }}</dd>
        </dl>
        <div class="auditoria">
          <strong>Registro de auditoría</strong><br />
          Creada por {{ c.creadoPor }} · {{ c.creadoEn | date: 'dd/MM/yyyy HH:mm' }} · Operador #{{ codigo }}
        </div>
      </div>

      <div class="acciones-fila">
        @if (c.estado === 'ACTIVA') {
          <button class="boton peligro" (click)="cambiar()">
            <span class="material-symbols-outlined">block</span> Anular cuenta
          </button>
        } @else {
          <button class="boton" (click)="cambiar()">
            <span class="material-symbols-outlined">check_circle</span> Reactivar cuenta
          </button>
        }
        <a class="boton claro" routerLink="/operadores">Volver a operadores</a>
      </div>
    }
  `,
})
export class OperadorGestionarComponent {
  private svc = inject(OperadoresService);
  private router = inject(Router);
  private id = Number(inject(ActivatedRoute).snapshot.paramMap.get('id'));

  cuenta = computed(() => this.svc.obtener(this.id));
  codigo = this.svc.codigo(this.id);
  mensaje = signal('');

  constructor() {
    const c = this.svc.obtener(this.id);
    // El administrador no puede gestionarse a sí mismo ni a otro administrador
    if (!c || c.rol !== 'OPERADOR') this.router.navigate(['/operadores']);
  }

  cambiar() {
    const c = this.cuenta();
    if (!c) return;
    if (c.estado === 'ACTIVA') {
      this.svc.cambiarEstado(c.id, 'ANULADA');
      this.mensaje.set('Cuenta anulada. El operador ya no puede iniciar sesión.');
    } else {
      this.svc.cambiarEstado(c.id, 'ACTIVA');
      this.mensaje.set('Cuenta reactivada. El operador puede iniciar sesión de nuevo.');
    }
  }
}