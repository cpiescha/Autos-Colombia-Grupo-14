import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AccesoService } from '../../services/acceso.service';
import { RegistroAcceso, SalidaPrevia } from '../../models/models';

@Component({
  selector: 'app-salida',
  standalone: true,
  imports: [FormsModule, DatePipe, MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatSnackBarModule],
  template: `
    <h1>Registro de salida</h1>
    <p class="ayuda">Consulte el comprobante entregado al ingreso. Confirme los datos antes de liberar la celda.</p>

    <mat-card class="tarjeta">
      <mat-card-content>
        <div class="fila">
          <mat-form-field appearance="outline" class="campo">
            <mat-label>Comprobante de entrada</mat-label>
            <input matInput [(ngModel)]="comprobante" (keyup.enter)="consultar()"
                   autocomplete="off" [disabled]="cargando() || !!previa()" />
          </mat-form-field>
          @if (!previa()) {
            <button mat-flat-button (click)="consultar()" [disabled]="cargando()">
              <mat-icon>search</mat-icon> {{ cargando() ? 'Consultando…' : 'Consultar' }}
            </button>
          } @else {
            <button mat-stroked-button (click)="reiniciar()" [disabled]="cargando()">Cambiar comprobante</button>
          }
        </div>
        @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
      </mat-card-content>
    </mat-card>

    @if (previa(); as p) {
      <div class="comprobante">
        <h2>Confirmar salida</h2>
        <div>Placa <strong>{{ p.placa }}</strong> · Celda <strong>{{ p.celda }}</strong></div>
        <div>Entrada: {{ p.fechaEntrada | date: 'dd/MM/yyyy HH:mm' }}</div>
        <p>La confirmación cerrará la permanencia y liberará la celda.</p>
        <button mat-flat-button (click)="registrar()" [disabled]="cargando()">
          <mat-icon>logout</mat-icon> {{ cargando() ? 'Registrando…' : 'Confirmar salida' }}
        </button>
      </div>
    }

    @if (registro(); as r) {
      <div class="comprobante">
        <h2>Comprobante de salida {{ r.comprobanteSalida?.numero }}</h2>
        <div>Placa <strong>{{ r.placa }}</strong> · Celda liberada <strong>{{ r.celda }}</strong></div>
        <div>Entrada: {{ r.entrada | date: 'dd/MM/yyyy HH:mm' }}</div>
        <div>Salida: {{ r.salida | date: 'dd/MM/yyyy HH:mm' }}</div>
        <div>Permanencia: <strong>{{ permanencia(r) }}</strong></div>
        <div class="fila">
          <button mat-stroked-button (click)="imprimir()"><mat-icon>print</mat-icon> Imprimir</button>
          <button mat-stroked-button (click)="reiniciar()">Nueva salida</button>
        </div>
      </div>
    }
  `,
  styleUrl: '../paginas.scss',
})
export class SalidaComponent {
  private acceso = inject(AccesoService);
  private aviso = inject(MatSnackBar);

  comprobante = '';
  previa = signal<SalidaPrevia | null>(null);
  registro = signal<RegistroAcceso | null>(null);
  error = signal('');
  cargando = signal(false);

  async consultar(): Promise<void> {
    if (this.cargando()) return;
    this.error.set('');
    this.registro.set(null);
    if (!this.comprobante.trim()) {
      this.error.set('El comprobante es obligatorio.');
      return;
    }
    this.cargando.set(true);
    try {
      const resultado = await this.acceso.consultarSalida(this.comprobante);
      if (!resultado.ok) {
        this.error.set(resultado.mensaje);
        return;
      }
      this.previa.set(resultado.dato!);
    } finally {
      this.cargando.set(false);
    }
  }

  async registrar(): Promise<void> {
    if (!this.previa() || this.cargando()) return;
    this.error.set('');
    this.cargando.set(true);
    try {
      const resultado = await this.acceso.registrarSalida(this.comprobante);
      if (!resultado.ok) {
        this.error.set(resultado.mensaje);
        this.aviso.open(resultado.mensaje, 'Cerrar', { duration: 4000 });
        return;
      }
      this.registro.set(resultado.dato!);
      this.previa.set(null);
      this.aviso.open(resultado.mensaje, 'Cerrar', { duration: 3000 });
    } finally {
      this.cargando.set(false);
    }
  }

  reiniciar(): void {
    this.comprobante = '';
    this.previa.set(null);
    this.registro.set(null);
    this.error.set('');
  }

  permanencia(r: RegistroAcceso): string { return this.acceso.permanencia(r); }
  imprimir(): void { window.print(); }
}
