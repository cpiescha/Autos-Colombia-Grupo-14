import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { VehiculoDetalle } from '../../models/vehicle-admin.model';
import { VehiculosService } from '../../services/vehiculos.service';

@Component({
  selector: 'app-vehiculo-gestionar', standalone: true,
  imports: [FormsModule, ReactiveFormsModule, RouterLink],
  template: `
    <h1>Gestionar vehículo</h1><p class="sub">Solo el administrador puede editar o retirar vehículos guardados.</p>
    <div class="panel"><label class="campo">Placa<input [(ngModel)]="busqueda" (keyup.enter)="buscar()" /></label>
      <button class="boton" type="button" (click)="buscar()" [disabled]="svc.pendiente()">Buscar</button></div>
    @if (svc.errorClientes()) { <div class="aviso-error" role="alert">{{ svc.errorClientes() }} <button type="button" class="enlace" (click)="svc.cargarClientes()">Reintentar</button></div> }
    @if (svc.error()) { <div class="aviso-error" role="alert">{{ svc.error() }}</div> }
    @if (errorFormulario()) { <div class="aviso-error" role="alert">{{ errorFormulario() }}</div> }
    @if (mensaje()) { <div class="aviso-ok" role="status">{{ mensaje() }}</div> }
    @if (vehiculo(); as v) {
      <form class="panel form-tarjeta" [formGroup]="form" (ngSubmit)="actualizar()">
        <div class="form-grid">
          <label class="campo">Placa<input formControlName="placa" /></label>
          <label class="campo">Tipo<select formControlName="tipo"><option value="CARRO">CARRO</option><option value="CAMIONETA">CAMIONETA</option><option value="MOTO">MOTO</option></select></label>
          <label class="campo">Marca<input formControlName="marca" /></label><label class="campo">Modelo<input formControlName="modelo" /></label>
          <label class="campo">Color<input formControlName="color" /></label>
          <label class="campo">Cliente<select formControlName="cliente_id">@for (c of svc.clientes(); track c.id) { <option [ngValue]="c.id">{{ c.nombre }}</option> }</select></label>
        </div>
        <div class="acciones-fila"><button class="boton" type="submit" [disabled]="svc.pendiente()">Guardar cambios</button>
          <button class="boton peligro" type="button" (click)="retirar()" [disabled]="svc.pendiente()">Retirar vehículo</button>
          <a class="boton claro" routerLink="/inicio">Cancelar</a></div>
      </form>
    }
  `,
})
export class VehiculoGestionarComponent {
  readonly svc = inject(VehiculosService); private readonly fb = inject(FormBuilder).nonNullable;
  readonly vehiculo = signal<VehiculoDetalle | null>(null); readonly mensaje = signal(''); readonly errorFormulario = signal(''); busqueda = '';
  readonly form = this.fb.group({ placa: ['', Validators.required], tipo: this.fb.control<'CARRO' | 'CAMIONETA' | 'MOTO'>('CARRO'), marca: ['', Validators.required], modelo: ['', Validators.required], color: ['', Validators.required], cliente_id: [0, Validators.min(1)] });
  constructor() { void this.svc.cargarClientes(); }
  async buscar(): Promise<void> {
    this.mensaje.set(''); this.errorFormulario.set('');
    if (!this.busqueda.trim()) { this.errorFormulario.set('Escriba una placa para buscar.'); return; }
    if (this.svc.pendiente()) return;
    const v = await this.svc.buscar(this.busqueda);
    if (v) { this.vehiculo.set(v); this.form.setValue({ placa: v.placa, tipo: v.tipo, marca: v.marca, modelo: v.modelo, color: v.color, cliente_id: v.cliente_id }); }
  }
  async actualizar(): Promise<void> {
    this.mensaje.set(''); this.errorFormulario.set('');
    const actual = this.vehiculo();
    if (!actual || this.form.invalid || this.svc.clientes().length === 0) { this.form.markAllAsTouched(); this.errorFormulario.set('Complete todos los campos y seleccione un cliente existente.'); return; }
    const v = await this.svc.actualizar(actual.placa, this.form.getRawValue());
    if (v) { this.mensaje.set(`Vehículo ${v.placa} actualizado.`); this.busqueda = v.placa; this.vehiculo.set({ ...actual, ...v, estado_mensualidad: actual.estado_mensualidad, authorized: actual.authorized, rejection_reason: actual.rejection_reason }); }
  }
  async retirar(): Promise<void> {
    this.mensaje.set(''); this.errorFormulario.set('');
    const actual = this.vehiculo(); if (!actual || this.svc.pendiente()) return;
    const v = await this.svc.retirar(actual.placa); if (v) { this.mensaje.set(`Vehículo ${v.placa} retirado.`); this.vehiculo.set(null); }
  }
}
