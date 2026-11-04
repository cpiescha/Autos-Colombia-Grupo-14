import { Component, inject } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { OperadoresService } from '../../../services/operadores.service';

function clavesIguales(g: AbstractControl): ValidationErrors | null {
  const a = g.get('clave')?.value;
  const b = g.get('confirmar')?.value;
  return a && b && a !== b ? { noCoinciden: true } : null;
}

@Component({
  selector: 'app-operador-crear',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <h1>Crear operador</h1>
    <p class="sub">Registre una cuenta personal para un empleado del parqueadero.</p>

    @if (svc.pendiente()) { <p role="status">Creando cuenta…</p> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }

    <form class="panel form-tarjeta" [formGroup]="form" (ngSubmit)="guardar()">
      <div class="aviso-info">
        La cuenta tendrá perfil <strong>OPERADOR</strong>. Podrá registrar vehículos, entradas y salidas;
        no podrá administrar operadores ni celdas.
      </div>

      <label class="campo">Nombre completo
        <input formControlName="nombre" />
        <small class="ayuda">Se mostrará en la trazabilidad de los movimientos.</small>
        @if (f.nombre.touched && f.nombre.invalid) { <small class="error">Escriba el nombre completo (de 3 a 120 caracteres).</small> }
      </label>

      <div class="form-grid" style="margin-top: 12px">
        <label class="campo">Usuario
          <input formControlName="usuario" autocomplete="off" />
          <small class="ayuda">Debe ser único.</small>
          @if (f.usuario.touched && f.usuario.errors?.['required']) { <small class="error">El usuario es obligatorio.</small> }
          @if (f.usuario.touched && f.usuario.errors?.['pattern']) { <small class="error">Use de 3 a 60 caracteres: empiece con letra y continúe con letras, números, puntos o guion bajo.</small> }
        </label>

        <label class="campo">Contraseña temporal
          <input type="password" formControlName="clave" autocomplete="new-password" />
          <small class="ayuda">Mínimo 8 caracteres.</small>
          @if (f.clave.touched && f.clave.invalid) { <small class="error">La contraseña debe tener mínimo 8 caracteres.</small> }
        </label>

        <label class="campo">Confirmar contraseña
          <input type="password" formControlName="confirmar" autocomplete="new-password" />
          @if (f.confirmar.touched && form.errors?.['noCoinciden']) { <small class="error">Las contraseñas no coinciden.</small> }
        </label>
      </div>

      <div class="acciones-fila">
        <button class="boton" type="submit" [disabled]="svc.pendiente()">
          <span class="material-symbols-outlined">save</span> Crear operador
        </button>
        <a class="boton claro" routerLink="/operadores">Cancelar</a>
      </div>
    </form>
  `,
})
export class OperadorCrearComponent {
  private fb = inject(FormBuilder).nonNullable;
  svc = inject(OperadoresService);
  private router = inject(Router);

  form = this.fb.group(
    {
      nombre: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(120)]],
      usuario: ['', [Validators.required, Validators.pattern(/^[a-z][a-z0-9._]{2,59}$/i)]],
      clave: ['', [Validators.required, Validators.minLength(8)]],
      confirmar: ['', Validators.required],
    },
    { validators: clavesIguales }
  );
  get f() { return this.form.controls; }

  async guardar() {
    if (this.svc.pendiente()) return;
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const v = this.form.getRawValue();
    const nueva = await this.svc.crear({ nombre: v.nombre.trim(), usuario: v.usuario.trim().toLowerCase(), clave: v.clave });
    if (nueva) {
      this.form.reset();
      await this.router.navigate(['/operadores/creado', nueva.id]);
    }
  }
}