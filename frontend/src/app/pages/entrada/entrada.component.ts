import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AccesoService } from '../../services/acceso.service';
import { ConsultaEntrada, RegistroAcceso } from '../../models/models';
 
type Fase = 'buscar' | 'confirmar' | 'listo';
 
@Component({
  selector: 'app-entrada',
  standalone: true,
  imports: [FormsModule, DatePipe],
  template: `
    @switch (fase()) {
 
      @case ('buscar') {
        <h1>Registrar entrada</h1>
        <p class="ayuda">Ingrese la placa y compare marca, modelo y color con el vehículo presente.</p>
 
        <label class="etiqueta" for="placa">Placa</label>
        <input id="placa" class="entrada-texto" [(ngModel)]="placa" (keyup.enter)="consultar()"
               maxlength="7" autocomplete="off" />
        <div class="bloque"><button type="button" class="btn" (click)="consultar()">Consultar</button></div>
 
        @if (vacio()) {
          <div class="alerta alerta-error" role="alert">Escriba una placa para consultar.</div>
        }
 
        @if (consulta(); as c) {
          @if (c.vehiculo; as v) {
            <div class="tarjeta-info">
              <h2>{{ titulo(c) }}</h2>
              @switch (c.estado) {
                @case ('YA_DENTRO') {
                  <p>Placa: {{ v.placa }}</p>
                  <p>Tipo: {{ v.tipo }}</p>
                  <p>{{ v.marca }} {{ v.color }}</p>
                  <p>Celda actual: {{ c.celdaActual }}</p>
                }
                @case ('SIN_CUPO') {
                  <p>{{ v.marca }} {{ v.color }}</p>
                  <p>Tipo: {{ v.tipo }}</p>
                  <p>Mensualidad vigente</p>
                }
                @default {
                  <p>Placa: {{ v.placa }}</p>
                  <p>Tipo: {{ v.tipo }}</p>
                  <p>Marca / modelo: {{ v.marca }}</p>
                  <p>Color: {{ v.color }}</p>
                  @if (c.estado === 'VENCIDA') {
                    <p>Mensualidad: Vencida el {{ v.mensualidadFin | date: 'dd/MM/yyyy' }}</p>
                  } @else {
                    <p>Mensualidad: Vigente hasta {{ v.mensualidadFin | date: 'dd/MM/yyyy' }}</p>
                  }
                }
              }
            </div>
          }
 
          @if (c.estado === 'AUTORIZADO') {
            <div class="alerta alerta-info">Compare marca, modelo y color con el vehículo presente antes de confirmar.</div>
            <div class="fila">
              <button type="button" class="btn" (click)="fase.set('confirmar')">Continuar a confirmación</button>
              <button type="button" class="btn btn-claro" (click)="reiniciar()">Cancelar (no altera el parqueadero)</button>
            </div>
          } @else {
            <div class="alerta alerta-error" role="alert">{{ c.mensaje }}</div>
            @if (c.estado === 'VENCIDA') {
              <button type="button" class="btn" disabled>Confirmar entrada</button>
            }
          }
        }
      }
 
      @case ('confirmar') {
        <h1>Confirmar entrada</h1>
        @if (consulta()?.vehiculo; as v) {
          <div class="tarjeta-info">
            <h2>{{ v.placa }} · {{ v.marca }} {{ v.color }}</h2>
            <p>Tipo: {{ v.tipo }}</p>
            <p>Mensualidad vigente</p>
            <p>Sin permanencia abierta</p>
          </div>
          <div class="alerta alerta-info">
            La celda la asigna el sistema.
            @if (v.tipo === 'CARRO') { Un carro o camioneta solo puede usar celdas de automóvil (A-01 a A-70). }
            @else { Una moto solo puede usar celdas de moto (M-01 a M-10). }
          </div>
        }
 
        @if (conflicto()) {
          <div class="alerta alerta-aviso" role="alert">
            No hay celdas disponibles: otro operario acaba de asignar la última celda compatible.
            No se duplicó la celda. El parqueadero no se alteró para esta solicitud.
          </div>
          <button type="button" class="btn btn-claro" (click)="volverAConsultar()">Volver a consultar disponibilidad</button>
        } @else {
          <div class="bloque">
            <button type="button" class="btn" (click)="confirmar()">Confirmar entrada y asignar celda</button>
          </div>
          <button type="button" class="btn btn-claro" (click)="reiniciar()">Cancelar</button>
        }
      }
 
      @case ('listo') {
        <h1>Entrada registrada</h1>
        @if (registro(); as r) {
          <div class="alerta alerta-ok">Permanencia abierta. Celda asignada: {{ r.celda }}.</div>
          <div class="tarjeta-info">
            <h2>Comprobante {{ r.comprobanteEntrada.numero }}</h2>
            @if (consulta()?.vehiculo; as v) {
              <p>Placa: {{ r.placa }} · {{ v.marca }} {{ v.color }}</p>
              <p>Celda: {{ r.celda }} ({{ v.tipo === 'MOTO' ? 'moto' : 'automóvil' }})</p>
            } @else {
              <p>Placa: {{ r.placa }}</p>
              <p>Celda: {{ r.celda }}</p>
            }
            <p>Entrada: {{ r.entrada | date: 'dd/MM/yyyy HH:mm' }}</p>
            <p>Operario: {{ r.operario }}</p>
            <p>Entregue este comprobante al conductor. Se exige para la salida.</p>
          </div>
          <div class="fila">
            <button type="button" class="btn" (click)="imprimir()">Imprimir comprobante</button>
            <button type="button" class="btn btn-claro" (click)="reiniciar()">Nueva entrada</button>
          </div>
        }
      }
    }
  `,
  styleUrl: '../paginas.scss',
})
export class EntradaComponent {
  private acceso = inject(AccesoService);
 
  placa = '';
  fase = signal<Fase>('buscar');
  consulta = signal<ConsultaEntrada | null>(null);
  registro = signal<RegistroAcceso | null>(null);
  vacio = signal(false);
  conflicto = signal(false);
 
  titulo(c: ConsultaEntrada): string {
    if (c.estado === 'YA_DENTRO') return 'Vehículo';
    if (c.estado === 'AUTORIZADO' || c.estado === 'SIN_CUPO') {
      return c.vehiculo?.tipo === 'MOTO' ? 'Moto autorizada' : 'Vehículo autorizado';
    }
    return 'Vehículo encontrado';
  }
 
  consultar(): void {
    this.consulta.set(null);
    this.vacio.set(!this.placa.trim());
    if (this.vacio()) return;
    this.consulta.set(this.acceso.consultarEntrada(this.placa));
  }
 
  confirmar(): void {
    const r = this.acceso.confirmarEntrada(this.placa);
    if (!r.ok) {
      this.conflicto.set(true);
      return;
    }
    this.registro.set(r.dato!);
    this.fase.set('listo');
  }
 
  volverAConsultar(): void {
    this.conflicto.set(false);
    this.fase.set('buscar');
    this.consultar();
  }
 
  reiniciar(): void {
    this.placa = '';
    this.consulta.set(null);
    this.registro.set(null);
    this.vacio.set(false);
    this.conflicto.set(false);
    this.fase.set('buscar');
  }
 
  imprimir(): void { window.print(); }
}
 
