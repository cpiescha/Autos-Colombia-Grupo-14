import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { VehiculosService } from '../../services/vehiculos.service';

@Component({
  selector: 'app-vehiculo-crear',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <h1>Registrar vehículo</h1>
    <p class="sub">Administrador y operador pueden registrar una placa nueva para un cliente existente.</p>
    @if (svc.errorClientes()) { <div class="aviso-error" role="alert">{{ svc.errorClientes() }} <button type="button" class="enlace" (click)="svc.cargarClientes()">Reintentar</button></div> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }
    @if (errorFormulario()) { <div class="aviso-error" role="alert">{{ errorFormulario() }}</div> }
    @if (mensaje()) { <div class="aviso-ok" role="status">{{ mensaje() }}</div> }
    <form class="panel form-tarjeta" [formGroup]="form" (ngSubmit)="guardar()">
      <div class="form-grid">
        <label class="campo">Placa<input formControlName="placa" maxlength="10" /></label>
        <label class="campo">Tipo<select formControlName="tipo"><option value="CARRO">CARRO</option><option value="CAMIONETA">CAMIONETA</option><option value="MOTO">MOTO</option></select></label>
        <label class="campo">Marca<input formControlName="marca" /></label>
        <label class="campo">Modelo<input formControlName="modelo" /></label>
        <label class="campo">Color<input formControlName="color" /></label>
        <label class="campo">Cliente existente
          <select formControlName="cliente_id">
            <option [ngValue]="0">Seleccione un cliente</option>
            @for (cliente of svc.clientes(); track cliente.id) { <option [ngValue]="cliente.id">{{ cliente.nombre }}</option> }
          </select>
        </label>
      </div>
      <div class="acciones-fila">
        <button class="boton" type="submit" [disabled]="svc.pendiente()">{{ svc.pendiente() ? 'Guardando…' : 'Registrar vehículo' }}</button>
        <a class="boton claro" routerLink="/inicio">Volver</a>
      </div>
    </form>
  `,
})
export class VehiculoCrearComponent {
  readonly svc = inject(VehiculosService);
  private readonly fb = inject(FormBuilder).nonNullable;
  readonly mensaje = signal('');
  readonly errorFormulario = signal('');
  readonly form = this.fb.group({
    placa: ['', Validators.required], tipo: this.fb.control<'CARRO' | 'CAMIONETA' | 'MOTO'>('CARRO'),
    marca: ['', Validators.required], modelo: ['', Validators.required], color: ['', Validators.required],
    cliente_id: [0, Validators.min(1)],
  });

  constructor() { void this.svc.cargarClientes(); }

  async guardar(): Promise<void> {
    this.mensaje.set('');
    this.errorFormulario.set('');
    if (this.form.invalid || this.svc.clientes().length === 0) {
      this.form.markAllAsTouched();
      this.errorFormulario.set('Complete todos los campos y seleccione un cliente existente.');
      return;
    }
    if (this.svc.pendiente()) return;
    const creado = await this.svc.crear(this.form.getRawValue());
    if (!creado) return;
    this.mensaje.set(`Vehículo ${creado.placa} registrado correctamente.`);
    this.form.reset({ placa: '', tipo: 'CARRO', marca: '', modelo: '', color: '', cliente_id: 0 });
  }
}
