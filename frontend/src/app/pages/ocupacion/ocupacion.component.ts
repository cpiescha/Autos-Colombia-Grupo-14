import { Component, inject } from '@angular/core';
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

    <div class="resumen">
      <span class="estado ok">Libres: {{ acceso.libres() }}</span>
      <span class="estado mal">Ocupadas: {{ acceso.ocupadas() }}</span>
      <span class="estado">Total: {{ acceso.celdas().length }}</span>
    </div>

    <div class="rejilla">
      @for (c of acceso.celdas(); track c.codigo) {
        <div class="celda" [class.libre]="c.estado === 'LIBRE'" [class.ocupada]="c.estado === 'OCUPADA'"
             [class.mant]="c.estado === 'MANTENIMIENTO'">
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
  `,
  styleUrl: '../paginas.scss',
  styles: [`
    :host { max-width: 900px; }
    .resumen { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
    .rejilla { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-bottom: 24px; }
    .celda { display: flex; flex-direction: column; gap: 2px; padding: 12px; border-radius: 8px; border: 2px solid; }
    .celda.libre { background: #e6f6ea; border-color: #2e8b4a; color: #17472a; }
    .celda.ocupada { background: #fdeaea; border-color: #c0392b; color: #7a1d14; }
    .celda.mant { background: #eceff1; border-color: #90a4ae; color: #455a64; }
    .tabla { width: 100%; }
  `],
})
export class OcupacionComponent {
  acceso = inject(AccesoService);
  columnas = ['placa', 'celda', 'entrada', 'comprobante'];

  etiqueta(e: string): string {
    return e === 'LIBRE' ? 'Libre' : e === 'OCUPADA' ? 'Ocupada' : 'Mantenimiento';
  }
}
