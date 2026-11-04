import { Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { OperadoresService } from '../../../services/operadores.service';

@Component({
  selector: 'app-operador-creado',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (svc.pendiente()) { <p role="status">Cargando cuenta…</p> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }
    @if (!svc.pendiente() && !cuenta()) { <p>Cuenta no disponible.</p><a routerLink="/operadores">Volver a operadores</a> }
    @if (cuenta(); as c) {
      <h1>Operador creado</h1>
      <div class="aviso-ok" role="status">
        <strong>Cuenta creada correctamente.</strong> {{ c.nombre }} ya puede iniciar sesión con su usuario personal.
      </div>

      <div class="panel form-tarjeta">
        <strong>Resumen de la cuenta</strong>
        <dl class="resumen">
          <dt>Nombre</dt><dd>{{ c.nombre }}</dd>
          <dt>Usuario</dt><dd>{{ c.usuario }}</dd>
          <dt>Perfil</dt><dd>{{ c.rol }}</dd>
          <dt>Estado</dt><dd><span class="chip ok">{{ c.estado }}</span></dd>
        </dl>
        <div class="auditoria">
          <strong>Registro de auditoría</strong><br />
          Creada el {{ c.creado_en | date: 'dd/MM/yyyy HH:mm' }} · Operador #{{ codigo }}
        </div>
      </div>

      <div class="acciones-fila">
        <a class="boton" routerLink="/operadores">Ver operadores</a>
        <a class="boton claro" routerLink="/operadores/nuevo">Crear otro operador</a>
      </div>
    }
  `,
})
export class OperadorCreadoComponent {
  svc = inject(OperadoresService);
  private id = Number(inject(ActivatedRoute).snapshot.paramMap.get('id'));

  cuenta = computed(() => this.svc.obtener(this.id));
  codigo = this.svc.codigo(this.id);

  constructor() {
    void this.svc.cargar();
  }
}