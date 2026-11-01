import { Component, inject } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CeldasService, TipoCelda } from '../../../services/celdas.service';

@Component({
  selector: 'app-celda-crear',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <h1>Crear celda</h1>
    <p class="sub">Agregue una celda disponible para la asignación automática.</p>

    <form class="panel form-tarjeta" [formGroup]="form" (ngSubmit)="guardar()">
      <div class="aviso-info">
        Las celdas nuevas se crean <strong>activas y libres</strong>. El sistema solo asignará vehículos compatibles con su tipo.
      </div>

      <div class="form-grid">
        <label class="campo">Código de celda
          <input formControlName="codigo" placeholder="A-71" autocomplete="off" />
          <small class="ayuda">Único. Formato sugerido: A-01 o M-01.</small>
          @if (f.codigo.touched && f.codigo.errors?.['required']) { <small class="error">El código es obligatorio.</small> }
          @if (f.codigo.errors?.['pattern']) { <small class="error">Use una letra (A o M), un guion y dos o tres números. Ej: A-71</small> }
          @if (f.codigo.errors?.['repetido']) { <small class="error">Ya existe una celda con ese código.</small> }
          @if (form.errors?.['incompatible']) { <small class="error">{{ form.errors?.['incompatible'] }}</small> }
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
        <button class="boton" type="submit">
          <span class="material-symbols-outlined">save</span> Crear celda
        </button>
        <a class="boton claro" routerLink="/celdas">Cancelar</a>
      </div>
    </form>
  `,
})
export class CeldaCrearComponent {
  private fb = inject(FormBuilder).nonNullable;
  private svc = inject(CeldasService);
  private router = inject(Router);

  private unico = (c: AbstractControl): ValidationErrors | null =>
    c.value && this.svc.existe(c.value.trim()) ? { repetido: true } : null;

  // La letra del código debe coincidir con el tipo (A = automóvil, M = moto)
  private coherente = (g: AbstractControl): ValidationErrors | null => {
    const cod = String(g.get('codigo')?.value ?? '').trim().toUpperCase();
    const tipo = g.get('tipo')?.value as TipoCelda;
    if (!/^[AM]-\d{2,3}$/.test(cod)) return null;
    if (cod.startsWith('A') && tipo !== 'AUTOMOVIL') return { incompatible: 'Los códigos con A son para AUTOMÓVIL.' };
    if (cod.startsWith('M') && tipo !== 'MOTO') return { incompatible: 'Los códigos con M son para MOTO.' };
    return null;
  };

  form = this.fb.group(
    {
      codigo: ['', [Validators.required, Validators.pattern(/^[AM]-\d{2,3}$/i), this.unico]],
      tipo: this.fb.control<TipoCelda>('AUTOMOVIL'),
    },
    { validators: this.coherente }
  );
  get f() { return this.form.controls; }

  guardar() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const { codigo, tipo } = this.form.getRawValue();
    const cod = codigo.trim().toUpperCase();
    this.svc.crear(cod, tipo);
    this.router.navigate(['/celdas'], { queryParams: { creada: cod } });
  }
}