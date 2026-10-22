import { Component, inject, signal, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AccesoService } from '../../services/acceso.service';
import { RegistroAcceso } from '../../models/models';

@Component({
  selector: 'app-salida',
  standalone: true,
  imports: [FormsModule, DatePipe, MatCardModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatSnackBarModule],
  template: `
    <h1>Registro de salida</h1>
    <p class="ayuda">Registre la salida del vehículo. El sistema libera la celda y genera el comprobante de salida.</p>

    <mat-card class="tarjeta">
      <mat-card-content>
        <div class="fila">
          <mat-form-field appearance="outline" class="campo">
            <mat-label>Placa</mat-label>
            <input matInput [(ngModel)]="placa" (keyup.enter)="registrar()" maxlength="7" autocomplete="off" />
          </mat-form-field>
          <button mat-flat-button (click)="registrar()"><mat-icon>logout</mat-icon> Registrar salida</button>
        </div>
        @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
      </mat-card-content>
    </mat-card>

    @if (registro(); as r) {
      <div class="comprobante">
        <h2>Comprobante de salida {{ r.comprobanteSalida?.numero }}</h2>
        <div>Placa <strong>{{ r.placa }}</strong> · Celda liberada <strong>{{ r.celda }}</strong></div>
        <div>Entrada: {{ r.entrada | date: 'dd/MM/yyyy HH:mm' }}</div>
        <div>Salida: {{ r.salida | date: 'dd/MM/yyyy HH:mm' }}</div>
        <div>Permanencia: <strong>{{ permanencia(r) }}</strong></div>
        <div class="fila" style="margin-top:12px">
          <button mat-stroked-button (click)="imprimir()"><mat-icon>print</mat-icon> Imprimir</button>
        </div>
      </div>
    }
  `,
  styleUrl: '../paginas.scss',
})
export class SalidaComponent implements OnInit {
  private acceso = inject(AccesoService);
  private ruta = inject(ActivatedRoute);
  private aviso = inject(MatSnackBar);
  placa = '';
  registro = signal<RegistroAcceso | null>(null);
  error = signal('');

  ngOnInit(): void {
    this.placa = this.ruta.snapshot.queryParamMap.get('placa') ?? '';
  }

  registrar(): void {
    this.error.set('');
    this.registro.set(null);
    if (!this.placa.trim()) { this.error.set('Escriba una placa para registrar la salida.'); return; }
    const r = this.acceso.registrarSalida(this.placa);
    if (!r.ok) { this.error.set(r.mensaje); this.aviso.open(r.mensaje, 'Cerrar', { duration: 4000 }); return; }
    this.registro.set(r.dato!);
    this.aviso.open(r.mensaje, 'Cerrar', { duration: 3000 });
  }

  permanencia(r: RegistroAcceso): string { return this.acceso.permanencia(r); }
  imprimir(): void { window.print(); }
}
