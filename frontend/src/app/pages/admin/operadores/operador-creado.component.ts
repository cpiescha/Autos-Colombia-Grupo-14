import { Component, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { OperadoresService } from '../../../services/operadores.service';

@Component({
  selector: 'app-operador-creado',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (cuenta; as c) {
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
          <dt>Turno</dt><dd>{{ c.turno }}</dd>
          <dt>Estado</dt><dd><span class="chip ok">{{ c.estado }}</span></dd>
        </dl>
        <div class="auditoria">
          <strong>Registro de auditoría</strong><br />
          Creado por {{ c.creadoPor }} · {{ c.creadoEn | date: 'dd/MM/yyyy HH:mm' }} · Operador #{{ codigo }}
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
  private svc = inject(OperadoresService);
  private router = inject(Router);
  private id = Number(inject(ActivatedRoute).snapshot.paramMap.get('id'));

  cuenta = this.svc.obtener(this.id);
  codigo = this.svc.codigo(this.id);

  constructor() {
    if (!this.cuenta) this.router.navigate(['/operadores']);
  }
}