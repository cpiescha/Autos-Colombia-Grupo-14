import { Component, OnInit, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { AccesoService } from '../../services/acceso.service';

@Component({
  selector: 'app-ocupacion',
  standalone: true,
  imports: [DatePipe, MatCardModule, MatTableModule],
  template: `
    <h1>Ocupación de celdas</h1>
    <p class="ayuda">Estado actual del parqueadero. Se actualiza solo cuando se registra un ingreso o una salida.</p>

    @if (acceso.cargandoDatos()) {
      <p role="status">Cargando ocupación…</p>
    } @else if (acceso.errorDatos()) {
      <p role="alert">{{ acceso.errorDatos() }}</p>
      <button type="button" (click)="acceso.cargarDatos()">Reintentar</button>
    } @else {
    <div class="resumen">
      <span class="estado ok">Libres: {{ acceso.libres() }}</span>
      <span class="estado mal">Ocupadas: {{ acceso.ocupadas() }}</span>
      <span class="estado">Inactivas: {{ inactivas() }}</span>
      <span class="estado">Total activo: {{ acceso.libres() + acceso.ocupadas() }}</span>
    </div>

    <div class="resumen-categorias" aria-label="Resumen por tipo de vehículo">
      <div class="categoria">
        <strong>Motos</strong>
        <span>{{ motos().libres }} libres · {{ motos().ocupadas }} ocupadas · {{ motos().inactivas }} inactivas</span>
      </div>
      <div class="categoria">
        <strong>Automóviles</strong>
        <span>{{ automoviles().libres }} libres · {{ automoviles().ocupadas }} ocupadas · {{ automoviles().inactivas }} inactivas</span>
      </div>
    </div>

    <div class="rejilla">
      @for (c of acceso.celdas(); track c.codigo) {
        <div class="celda" [class.libre]="c.estado === 'LIBRE'" [class.ocupada]="c.estado === 'OCUPADA'"
             [class.mant]="c.estado === 'INACTIVA'">
          <strong>{{ c.codigo }}</strong>
          <small>{{ c.tipoVehiculo === 'CARRO' ? 'Carro' : 'Moto' }}</small>
          <small>{{ etiqueta(c.estado) }}</small>
        </div>
      }
    </div>

    <mat-card class="tarjeta">
      <mat-card-header><mat-card-title>Vehículos dentro</mat-card-title></mat-card-header>
      <mat-card-content>
        @if (acceso.activos().length === 0) {
          <p class="ayuda">No hay vehículos dentro. Registre un ingreso para verlo aquí.</p>
        } @else {
          <table mat-table [dataSource]="acceso.activos()" class="tabla">
            <ng-container matColumnDef="placa"><th mat-header-cell *matHeaderCellDef>Placa</th><td mat-cell *matCellDef="let r">{{ r.placa }}</td></ng-container>
            <ng-container matColumnDef="celda"><th mat-header-cell *matHeaderCellDef>Celda</th><td mat-cell *matCellDef="let r">{{ r.celda }}</td></ng-container>
            <ng-container matColumnDef="entrada"><th mat-header-cell *matHeaderCellDef>Entrada</th><td mat-cell *matCellDef="let r">{{ r.entrada | date: 'dd/MM HH:mm' }}</td></ng-container>
            <ng-container matColumnDef="comprobante"><th mat-header-cell *matHeaderCellDef>Comprobante</th><td mat-cell *matCellDef="let r">{{ r.comprobanteEntrada.numero }}</td></ng-container>
            <tr mat-header-row *matHeaderRowDef="columnas"></tr>
            <tr mat-row *matRowDef="let row; columns: columnas"></tr>
          </table>
        }
      </mat-card-content>
    </mat-card>
    }
  `,
  styleUrl: '../paginas.scss',
  styles: [`
    :host { max-width: 900px; }
    .resumen { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .resumen-categorias { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
    .categoria { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 12px 16px; display: grid; gap: 4px; }
    .categoria strong { color: #0d2a4d; }
    .categoria span { color: #5f6b7a; font-size: 14px; }
    .rejilla { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-bottom: 24px; }
    .celda { display: flex; flex-direction: column; gap: 2px; padding: 12px; border-radius: 8px; border: 2px solid; }
    .celda.libre { background: #e6f6ea; border-color: #2e8b4a; color: #17472a; }
    .celda.ocupada { background: #fdeaea; border-color: #c0392b; color: #7a1d14; }
    .celda.mant { background: #eceff1; border-color: #90a4ae; color: #455a64; }
    .tabla { width: 100%; }
  `],
})
export class OcupacionComponent implements OnInit {
  acceso = inject(AccesoService);
  columnas = ['placa', 'celda', 'entrada', 'comprobante'];
  inactivas = computed(() => this.acceso.celdas().filter((c) => c.estado === 'INACTIVA').length);
  motos = computed(() => this.resumenTipo('MOTO'));
  automoviles = computed(() => this.resumenTipo('CARRO'));

  ngOnInit(): void { this.acceso.cargarDatos(); }

  private resumenTipo(tipo: 'MOTO' | 'CARRO') {
    const celdas = this.acceso.celdas().filter((c) => c.tipoVehiculo === tipo);
    return {
      libres: celdas.filter((c) => c.estado === 'LIBRE').length,
      ocupadas: celdas.filter((c) => c.estado === 'OCUPADA').length,
      inactivas: celdas.filter((c) => c.estado === 'INACTIVA').length,
    };
  }

  etiqueta(e: string): string {
    return e === 'LIBRE' ? 'Libre' : e === 'OCUPADA' ? 'Ocupada' : 'Inactiva';
  }
}
