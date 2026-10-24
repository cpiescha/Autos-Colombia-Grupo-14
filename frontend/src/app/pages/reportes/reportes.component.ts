import { Component, OnInit, inject, signal } from '@angular/core';
import { AccesoService } from '../../services/acceso.service';
import { ReporteOcupacion } from '../../models/models';

@Component({
  selector: 'app-reportes',
  standalone: true,
  template: `
    <h1>Reporte de ocupación</h1>
    <div class="aviso">Los totales provienen del reporte de FastAPI y de las permanencias abiertas.</div>

    @if (error()) {
      <div class="error" role="alert">{{ error() }}</div>
    }

    @if (reporte(); as r) {
      <div class="tarjetas">
        <div class="tarjeta"><span>Vehículos registrados</span><strong>{{ r.vehiculosRegistrados }}</strong><small>Con mensualidad en el sistema</small></div>
        <div class="tarjeta"><span>Presentes ahora</span><strong>{{ r.vehiculosPresentes }}</strong><small>Permanencias abiertas</small></div>
        <div class="tarjeta"><span>Capacidad</span><strong>{{ r.total.capacidad }}</strong><small>10 moto + 70 automóvil</small></div>
        <div class="tarjeta"><span>Libres</span><strong>{{ r.total.disponibles }}</strong><small>Disponibles ahora</small></div>
      </div>

      <div class="panel">
        <strong>Desglose</strong>
        <div>Motos ocupadas: {{ r.moto.ocupadas }} / {{ r.moto.capacidad }}</div>
        <div>Automóviles ocupados: {{ r.automovil.ocupadas }} / {{ r.automovil.capacidad }}</div>
      </div>
    } @else if (!error()) {
      <div class="aviso">Cargando reporte…</div>
    }
  `,
  styles: [`
    h1 { margin: 0 0 12px; font-size: 24px; font-weight: 500; color: #0d2a4d; }
    .aviso { background: #e3f2fd; color: #0d47a1; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
    .error { background: #ffebee; color: #b71c1c; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; }
    .tarjetas { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .tarjeta { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 12px 20px; min-width: 170px; display: grid; gap: 2px; }
    .tarjeta span { font-size: 13px; color: #5f6b7a; }
    .tarjeta strong { font-size: 28px; color: #0d47a1; font-weight: 500; }
    .tarjeta small { color: #5f6b7a; }
    .panel { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 16px; display: grid; gap: 4px; }
  `],
})
export class ReportesComponent implements OnInit {
  private acceso = inject(AccesoService);
  reporte = signal<ReporteOcupacion | null>(null);
  error = signal('');

  async ngOnInit(): Promise<void> {
    const resultado = await this.acceso.obtenerReporteOcupacion();
    if (!resultado.ok) {
      this.error.set(resultado.mensaje);
      return;
    }
    this.reporte.set(resultado.dato!);
  }
}
