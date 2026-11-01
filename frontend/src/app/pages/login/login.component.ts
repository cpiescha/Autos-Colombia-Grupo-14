import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <header class="barra"><strong>Autos Colombia</strong><span>Parqueadero · Acceso de personal</span></header>
    <main class="fondo">
      <form class="tarjeta" [formGroup]="form" (ngSubmit)="entrar()">
        <h1>Iniciar sesión</h1>
        <p class="intro">Ingrese con las credenciales asignadas para registrar movimientos o administrar el parqueadero.</p>

        @if (error()) { <div class="alerta" role="alert">{{ error() }}</div> }

        <label>Usuario
          <input formControlName="usuario" autocomplete="username" />
        </label>
        @if (form.controls.usuario.touched && form.controls.usuario.invalid) {
          <small class="msg">El usuario es obligatorio.</small>
        }

        <label>Contraseña
          <input type="password" formControlName="clave" autocomplete="current-password" />
        </label>
        @if (form.controls.clave.touched && form.controls.clave.invalid) {
          <small class="msg">La contraseña es obligatoria.</small>
        }

        <div class="acciones">
          <button class="boton" type="submit">
            <span class="material-symbols-outlined">login</span> Ingresar
          </button>
          <button class="enlace" type="button" (click)="ayuda.set(!ayuda())">¿Necesita ayuda?</button>
        </div>
        @if (ayuda()) {
          <div class="aviso-ayuda">Si olvidó su contraseña o su usuario, solicite al administrador que revise su cuenta.</div>
        }

        <hr />
        <p class="pie">Las cuentas anuladas no pueden acceder. Si su turno cambió, contacte al administrador.</p>
      </form>
    </main>
  `,
  styles: [`
    :host { display: block; min-height: 100vh; background: #f4f6f8; }
    .barra { background: #2068bd; color: #fff; height: 54px; display: flex; align-items: center; gap: 18px; padding: 0 32px; }
    .barra strong { font-size: 20px; }
    .barra span { font-size: 13px; }
    .fondo { display: grid; place-items: start center; padding-top: 80px; }
    .tarjeta { background: #fff; border: 1px solid #dfe3e8; border-radius: 12px; padding: 32px; width: 470px; max-width: 92vw; display: grid; gap: 10px; box-sizing: border-box; }
    h1 { margin: 0; font-size: 28px; color: #1c2430; }
    .intro { margin: 0 0 8px; color: #5f6b7a; line-height: 1.4; }
    label { display: grid; gap: 6px; font-weight: 600; font-size: 14px; color: #1c2430; }
    input { padding: 12px; border: 1px solid #9aa5b1; border-radius: 6px; font-size: 15px; font-weight: 400; }
    .msg { color: #c62828; }
    .alerta { background: #fdeaea; color: #b71c1c; padding: 10px 12px; border-radius: 6px; font-size: 14px; }
    .acciones { display: flex; align-items: center; gap: 18px; margin-top: 8px; }
    .enlace { background: none; border: 0; color: #1565c0; cursor: pointer; font: inherit; }
    .aviso-ayuda { background: #e3f2fd; color: #0d47a1; padding: 10px 12px; border-radius: 6px; font-size: 14px; }
    hr { border: 0; border-top: 1px solid #e3e7eb; width: 100%; margin: 8px 0 0; }
    .pie { margin: 0; font-size: 13px; color: #5f6b7a; }
  `],
})
export class LoginComponent {
  private fb = inject(FormBuilder).nonNullable;
  private auth = inject(AuthService);
  private router = inject(Router);

  error = signal('');
  ayuda = signal(false);
  form = this.fb.group({
    usuario: ['', Validators.required],
    clave: ['', Validators.required],
  });

  entrar() {
    this.error.set('');
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const { usuario, clave } = this.form.getRawValue();
    const resultado = this.auth.login(usuario, clave);

    if (resultado === 'OK') this.router.navigate([this.auth.rutaInicial()]);
    else if (resultado === 'ANULADA') this.error.set('Su cuenta está anulada y no puede acceder. Contacte al administrador.');
    else this.error.set('Usuario o contraseña incorrectos.');
  }
}