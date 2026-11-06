import { Component, OnInit, inject, signal } from '@angular/core';
import { AccesoService } from '../../services/acceso.service';
import { MovimientoHistorico, ReporteOcupacion } from '../../models/models';

@Component({
  selector: 'app-reportes',
  standalone: true,
  template: `
    <h1>Reportes e historial</h1>
    <div class="aviso">
      Los datos se consultan en PostgreSQL. Las permanencias cerradas y sus correcciones
      siguen disponibles después de cerrar el movimiento o recargar la aplicación.
    </div>

    @if (error()) {
      <div class="error" role="alert">{{ error() }}</div>
    }

    @if (reporte(); as r) {
      <div class="tarjetas">
        <div class="tarjeta"><span>Vehículos registrados</span><strong>{{ r.vehiculosRegistrados }}</strong><small>Registrados en el sistema</small></div>
        <div class="tarjeta"><span>Presentes ahora</span><strong>{{ r.vehiculosPresentes }}</strong><small>Permanencias abiertas</small></div>
        <div class="tarjeta"><span>Capacidad</span><strong>{{ r.total.capacidad }}</strong><small>{{ r.moto.capacidad }} moto + {{ r.automovil.capacidad }} automóvil</small></div>
        <div class="tarjeta"><span>Libres</span><strong>{{ r.total.disponibles }}</strong><small>Disponibles ahora</small></div>
      </div>

      <div class="panel resumen">
        <strong>Ocupación actual</strong>
        <div>Motos ocupadas: {{ r.moto.ocupadas }} / {{ r.moto.capacidad }}</div>
        <div>Automóviles ocupados: {{ r.automovil.ocupadas }} / {{ r.automovil.capacidad }}</div>
      </div>
    }

    <section class="historial" aria-labelledby="titulo-historial">
      <h2 id="titulo-historial">Permanencias cerradas</h2>
      @if (cargando()) {
        <div class="aviso" role="status">Cargando historial…</div>
      } @else if (historial().length === 0 && !error()) {
        <div class="panel vacio">Todavía no hay permanencias cerradas.</div>
      } @else if (historial().length > 0) {
        <div class="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>Placa</th>
                <th>Celda final</th>
                <th>Entrada</th>
                <th>Salida</th>
                <th>Responsables</th>
                <th>Comprobante</th>
                <th>Correcciones</th>
              </tr>
            </thead>
            <tbody>
              @for (movimiento of historial(); track movimiento.permanenciaId) {
                <tr>
                  <td><strong>{{ movimiento.placa }}</strong></td>
                  <td>{{ movimiento.celdaFinal }}</td>
                  <td>{{ fecha(movimiento.fechaEntrada) }}</td>
                  <td>{{ fecha(movimiento.fechaSalida) }}</td>
                  <td>
                    <span>Entrada: {{ movimiento.operarioEntrada }}</span>
                    <span>Salida: {{ movimiento.operarioSalida }}</span>
                  </td>
                  <td>{{ movimiento.comprobante || 'No disponible' }}</td>
                  <td>
                    @if (movimiento.correcciones.length === 0) {
                      Sin correcciones
                    } @else {
                      @for (correccion of movimiento.correcciones; track correccion.fechaCorreccion) {
                        <div class="correccion">
                          {{ correccion.celdaAnterior }} → {{ correccion.celdaNueva }}<br>
                          <small>{{ correccion.operario }} · {{ fecha(correccion.fechaCorreccion) }}</small>
                        </div>
                      }
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </section>
  `,
  styles: [`
    h1 { margin: 0 0 12px; font-size: 24px; font-weight: 500; color: #0d2a4d; }
    h2 { margin: 28px 0 12px; color: #0d2a4d; font-size: 20px; }
    .aviso { background: #e3f2fd; color: #0d47a1; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
    .error { background: #ffebee; color: #b71c1c; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; }
    .tarjetas { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .tarjeta { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 12px 20px; min-width: 170px; display: grid; gap: 2px; }
    .tarjeta span { font-size: 13px; color: #5f6b7a; }
    .tarjeta strong { font-size: 28px; color: #0d47a1; font-weight: 500; }
    .tarjeta small { color: #5f6b7a; }
    .panel { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 16px; }
    .resumen { display: grid; gap: 4px; }
    .vacio { color: #5f6b7a; }
    .tabla-contenedor { overflow-x: auto; border: 1px solid #dfe3e8; border-radius: 8px; background: #fff; }
    table { width: 100%; border-collapse: collapse; min-width: 980px; }
    th, td { padding: 12px; border-bottom: 1px solid #e7eaee; text-align: left; vertical-align: top; }
    th { background: #f7f9fb; color: #425466; font-size: 12px; text-transform: uppercase; }
    td { color: #263238; font-size: 13px; }
    td span { display: block; white-space: nowrap; }
    .correccion + .correccion { margin-top: 8px; padding-top: 8px; border-top: 1px solid #e7eaee; }
    .correccion small { color: #5f6b7a; }
  `],
})
export class ReportesComponent implements OnInit {
  private acceso = inject(AccesoService);
  reporte = signal<ReporteOcupacion | null>(null);
  historial = signal<MovimientoHistorico[]>([]);
  cargando = signal(true);
  error = signal('');

  async ngOnInit(): Promise<void> {
    const [reporte, historial] = await Promise.all([
      this.acceso.obtenerReporteOcupacion(),
      this.acceso.obtenerHistorialMovimientos(),
    ]);
    if (reporte.ok) {
      this.reporte.set(reporte.dato!);
    }
    if (historial.ok) {
      this.historial.set(historial.dato!);
    }
    if (!reporte.ok || !historial.ok) {
      this.error.set(!historial.ok ? historial.mensaje : reporte.mensaje);
    }
    this.cargando.set(false);
  }

  fecha(value: Date): string {
    return new Intl.DateTimeFormat('es-CO', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(value);
  }
}
