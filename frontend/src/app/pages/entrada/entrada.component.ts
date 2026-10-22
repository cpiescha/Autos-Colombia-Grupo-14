import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AccesoService } from '../../services/acceso.service';
import { ConsultaEntrada, RegistroAcceso } from '../../models/models';

type Fase = 'buscar' | 'confirmar' | 'listo';

@Component({
  selector: 'app-entrada',
  standalone: true,
  imports: [FormsModule, DatePipe, MatFormFieldModule, MatInputModule, MatButtonModule, MatSnackBarModule],
  template: `
    @switch (fase()) {
      @case ('buscar') {
        <h1>Registrar entrada</h1>
        <p class="ayuda">Ingrese la placa y compare marca, modelo y color con el vehículo presente.</p>
        <div class="fila">
          <mat-form-field appearance="outline" class="campo">
            <mat-label>Placa</mat-label>
            <input matInput [(ngModel)]="placa" (keyup.enter)="consultar()" maxlength="7" autocomplete="off" />
          </mat-form-field>
          <button mat-flat-button (click)="consultar()">Consultar</button>
        </div>
        @if (vacio()) { <div class="aviso aviso-error" role="alert">Escriba una placa para consultar.</div> }

        @if (consulta(); as c) {
          @if (c.vehiculo) {
            <div class="panel">
              <strong>{{ titulo(c) }}</strong>
              <div>Placa: {{ c.vehiculo.placa }}</div>
              <div>Tipo: {{ c.vehiculo.tipo }}</div>
              <div>Marca / modelo: {{ c.vehiculo.marca }}</div>
              <div>Color: {{ c.vehiculo.color }}</div>
              @if (c.estado === 'VENCIDA') {
                <div>Mensualidad: Vencida el {{ c.vehiculo.mensualidadFin | date: 'dd/MM/yyyy' }}</div>
              } @else {
                <div>Mensualidad: Vigente hasta {{ c.vehiculo.mensualidadFin | date: 'dd/MM/yyyy' }}</div>
              }
              @if (c.celdaActual) { <div>Celda actual: {{ c.celdaActual }}</div> }
            </div>
          }
          @if (c.estado === 'AUTORIZADO') {
            <div class="aviso aviso-info">Compare marca, modelo y color con el vehículo presente antes de confirmar.</div>
            <div class="fila">
              <button mat-flat-button (click)="fase.set('confirmar')">Continuar a confirmación</button>
              <button mat-stroked-button (click)="reiniciar()">Cancelar (no altera el parqueadero)</button>
            </div>
          } @else {
            <div class="aviso aviso-error" role="alert">{{ c.mensaje }}</div>
            @if (c.estado === 'VENCIDA') {
              <button mat-flat-button disabled>Confirmar entrada</button>
            }
          }
        }
      }

      @case ('confirmar') {
        <h1>Confirmar entrada</h1>
        @if (consulta()?.vehiculo; as v) {
          <div class="panel">
            <strong>{{ v.placa }} · {{ v.marca }} {{ v.color }}</strong>
            <div>Tipo: {{ v.tipo }}</div>
            <div>Mensualidad vigente</div>
            <div>Sin permanencia abierta</div>
          </div>
          <div class="aviso aviso-info">
            La celda la asigna el sistema.
            @if (v.tipo === 'CARRO') { Un carro solo puede usar celdas de automóvil (A-01 a A-70). }
            @else { Una moto solo puede usar celdas de moto (M-01 a M-10). }
          </div>
        }
        <div class="fila">
          <button mat-flat-button (click)="confirmar()">Confirmar entrada y asignar celda</button>
          <button mat-stroked-button (click)="reiniciar()">Cancelar</button>
        </div>
      }

      @case ('listo') {
        <h1>Entrada registrada</h1>
        @if (registro(); as r) {
          <div class="aviso aviso-ok">Permanencia abierta. Celda asignada: {{ r.celda }}.</div>
          <div class="comprobante">
            <h2>Comprobante {{ r.comprobanteEntrada.numero }}</h2>
            <div>Placa: <strong>{{ r.placa }}</strong></div>
            <div>Celda:</div>
            <div class="celda-grande">{{ r.celda }}</div>
            <div>Entrada: {{ r.entrada | date: 'dd/MM/yyyy HH:mm' }}</div>
            <div>Operario: {{ r.operario }}</div>
            <p class="ayuda">Entregue este comprobante al conductor. Se exige para la salida.</p>
          </div>
          <div class="fila" style="margin-top:12px">
            <button mat-flat-button (click)="imprimir()">Imprimir comprobante</button>
            <button mat-stroked-button (click)="reiniciar()">Nueva entrada</button>
          </div>
        }
      }
    }
  `,
  styleUrl: '../paginas.scss',
})
export class EntradaComponent {
  private acceso = inject(AccesoService);
  private aviso = inject(MatSnackBar);

  placa = '';
  fase = signal<Fase>('buscar');
  consulta = signal<ConsultaEntrada | null>(null);
  registro = signal<RegistroAcceso | null>(null);
  vacio = signal(false);

  titulo(c: ConsultaEntrada): string {
    if (c.estado === 'AUTORIZADO') return c.vehiculo?.tipo === 'MOTO' ? 'Moto autorizada' : 'Vehículo autorizado';
    return c.estado === 'YA_DENTRO' ? 'Vehículo' : 'Vehículo encontrado';
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
      this.aviso.open(r.mensaje, 'Cerrar', { duration: 4000 });
      this.fase.set('buscar');
      this.consultar();
      return;
    }
    this.registro.set(r.dato!);
    this.fase.set('listo');
    this.aviso.open(r.mensaje, 'Cerrar', { duration: 3000 });
  }

  reiniciar(): void {
    this.placa = '';
    this.consulta.set(null);
    this.registro.set(null);
    this.vacio.set(false);
    this.fase.set('buscar');
  }

  imprimir(): void { window.print(); }
}
