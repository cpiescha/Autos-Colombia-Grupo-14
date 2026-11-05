import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CeldasService, TipoCelda } from '../../../services/celdas.service';

@Component({
  selector: 'app-celda-crear',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <h1>Crear celda</h1>
    <p class="sub">Agregue una celda disponible para la asignación automática.</p>

    @if (svc.pendiente()) { <p role="status">Creando celda…</p> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }

    <form class="panel form-tarjeta" [formGroup]="form" (ngSubmit)="guardar()">
      <div class="aviso-info">
        Las celdas nuevas se crean <strong>activas y libres</strong>. El sistema solo asignará vehículos compatibles con su tipo.
      </div>

      <div class="form-grid">
        <label class="campo">Código de celda
          <input formControlName="codigo" placeholder="A-71" autocomplete="off" />
          <small class="ayuda">Único. Formato sugerido: A-01 o M-01.</small>
          @if (f.codigo.touched && f.codigo.errors?.['required']) { <small class="error">El código es obligatorio.</small> }
          @if (f.codigo.errors?.['pattern']) { <small class="error">Use de 2 a 20 letras, números o guiones; empiece por letra o número.</small> }
        </label>

        <label class="campo">Tipo de celda
          <select formControlName="tipo">
            <option value="AUTOMOVIL">AUTOMÓVIL</option>
            <option value="MOTO">MOTO</option>
          </select>
          <small class="ayuda">Carros y camionetas solo usan AUTOMÓVIL.</small>
        </label>
      </div>

      <div class="acciones-fila">
        <button class="boton" type="submit" [disabled]="svc.pendiente()">
          <span class="material-symbols-outlined">save</span> Crear celda
        </button>
        <a class="boton claro" routerLink="/celdas">Cancelar</a>
      </div>
    </form>
  `,
})
export class CeldaCrearComponent {
  private fb = inject(FormBuilder).nonNullable;
  svc = inject(CeldasService);
  private router = inject(Router);

  form = this.fb.group(
    {
      codigo: ['', [Validators.required, Validators.pattern(/^[A-Z0-9][A-Z0-9-]{1,19}$/i)]],
      tipo: this.fb.control<TipoCelda>('AUTOMOVIL'),
    }
  );
  get f() { return this.form.controls; }

  async guardar() {
    if (this.svc.pendiente()) return;
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const { codigo, tipo } = this.form.getRawValue();
    const cod = codigo.trim().toUpperCase();
    const celda = await this.svc.crear(cod, tipo);
    if (celda) await this.router.navigate(['/celdas'], { queryParams: { creada: celda.codigo } });
  }
}