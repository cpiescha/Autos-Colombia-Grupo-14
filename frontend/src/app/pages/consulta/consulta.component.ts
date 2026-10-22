import { Component, inject, signal } from '@angular/core';
import { DatePipe, CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AccesoService } from '../../services/acceso.service';
import { ConsultaResultado } from '../../models/models';

@Component({
  selector: 'app-consulta',
  standalone: true,
  imports: [FormsModule, DatePipe, CurrencyPipe, MatCardModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule],
  template: `
    <h1>Consulta de vehículo</h1>
    <p class="ayuda">Escriba la placa para ver la mensualidad y el estado del vehículo. Placas de prueba: ABC123, DEF456, XYZ987, MOT45A.</p>

    <mat-card class="tarjeta">
      <mat-card-content>
        <div class="fila">
          <mat-form-field appearance="outline" class="campo">
            <mat-label>Placa</mat-label>
            <input matInput [(ngModel)]="placa" (keyup.enter)="consultar()" maxlength="7" autocomplete="off" />
          </mat-form-field>
          <button mat-flat-button (click)="consultar()"><mat-icon>search</mat-icon> Consultar</button>
        </div>
        @if (error()) { <p class="error" role="alert">{{ error() }}</p> }
      </mat-card-content>
    </mat-card>

    @if (resultado(); as r) {
      <mat-card class="tarjeta">
        <mat-card-header>
          <mat-card-title>{{ r.vehiculo.placa }} · {{ r.vehiculo.marca }}</mat-card-title>
          <mat-card-subtitle>{{ r.vehiculo.tipo }} · {{ r.vehiculo.color }}</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <dl class="datos">
            <dt>Titular</dt><dd>{{ r.vehiculo.cliente.nombres }} {{ r.vehiculo.cliente.apellidos }}</dd>
            <dt>Documento</dt><dd>{{ r.vehiculo.cliente.numeroDocumento }}</dd>
            <dt>Teléfono</dt><dd>{{ r.vehiculo.cliente.telefono }}</dd>
            <dt>Mensualidad</dt>
            <dd>{{ r.vehiculo.mensualidad.fechaInicio | date: 'dd/MM/yyyy' }} al {{ r.vehiculo.mensualidad.fechaFin | date: 'dd/MM/yyyy' }}
                ({{ r.vehiculo.mensualidad.valor | currency: 'COP' : 'symbol-narrow' : '1.0-0' }})</dd>
          </dl>
          <div class="chips">
            <span class="estado" [class.ok]="r.mensualidadVigente" [class.mal]="!r.mensualidadVigente">
              {{ r.mensualidadVigente ? 'Mensualidad vigente' : 'Mensualidad vencida' }}
            </span>
            <span class="estado" [class.dentro]="r.dentroDelParqueadero">
              {{ r.dentroDelParqueadero ? 'Dentro del parqueadero' : 'Fuera del parqueadero' }}
            </span>
          </div>
        </mat-card-content>
        <mat-card-actions>
          @if (!r.dentroDelParqueadero) {
            <button mat-flat-button [disabled]="!r.mensualidadVigente" (click)="irAIngreso(r)">Registrar ingreso</button>
          } @else {
            <button mat-flat-button (click)="irASalida(r)">Registrar salida</button>
          }
        </mat-card-actions>
      </mat-card>
    }
  `,
  styleUrl: '../paginas.scss',
})
export class ConsultaComponent {
  private acceso = inject(AccesoService);
  private router = inject(Router);
  placa = '';
  resultado = signal<ConsultaResultado | null>(null);
  error = signal('');

  consultar(): void {
    this.error.set('');
    this.resultado.set(null);
    if (!this.placa.trim()) { this.error.set('Escriba una placa para consultar.'); return; }
    const r = this.acceso.consultarPlaca(this.placa);
    if (!r) { this.error.set('La placa no está registrada. Verifique que esté bien escrita.'); return; }
    this.resultado.set(r);
  }

  irAIngreso(r: ConsultaResultado): void { this.router.navigate(['/ingreso'], { queryParams: { placa: r.vehiculo.placa } }); }
  irASalida(r: ConsultaResultado): void { this.router.navigate(['/salida'], { queryParams: { placa: r.vehiculo.placa } }); }
}
