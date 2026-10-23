import { Component, OnInit, computed, inject } from '@angular/core';
import { AccesoService } from '../../services/acceso.service';

@Component({
  selector: 'app-reportes',
  standalone: true,
  template: `
    <h1>Reporte de ocupación</h1>
    <div class="aviso">Los totales se derivan de las permanencias abiertas. No hay contador manual.</div>

    <div class="tarjetas">
      <div class="tarjeta"><span>Presentes ahora</span><strong>{{ acceso.activos().length }}</strong><small>Permanencias abiertas</small></div>
      <div class="tarjeta"><span>Capacidad</span><strong>{{ acceso.celdas().length }}</strong><small>10 moto + 70 automóvil</small></div>
      <div class="tarjeta"><span>Libres</span><strong>{{ acceso.libres() }}</strong><small>Disponibles ya</small></div>
    </div>

    <div class="panel">
      <strong>Desglose</strong>
      <div>Motos ocupadas: {{ motos().ocupadas }} / {{ motos().total }}</div>
      <div>Automóviles ocupados: {{ autos().ocupadas }} / {{ autos().total }}</div>
    </div>
  `,
  styles: [`
    h1 { margin: 0 0 12px; font-size: 24px; font-weight: 500; color: #0d2a4d; }
    .aviso { background: #e3f2fd; color: #0d47a1; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
    .tarjetas { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .tarjeta { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 12px 20px; min-width: 170px; display: grid; gap: 2px; }
    .tarjeta span { font-size: 13px; color: #5f6b7a; }
    .tarjeta strong { font-size: 28px; color: #0d47a1; font-weight: 500; }
    .tarjeta small { color: #5f6b7a; }
    .panel { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; padding: 16px; display: grid; gap: 4px; }
  `],
})
export class ReportesComponent implements OnInit {
  acceso = inject(AccesoService);
  ngOnInit(): void { this.acceso.cargarDatos(); }
  private conteo = (tipo: 'MOTO' | 'CARRO') => {
    const lista = this.acceso.celdas().filter((c) => c.tipoVehiculo === tipo);
    return { total: lista.length, ocupadas: lista.filter((c) => c.estado === 'OCUPADA').length };
  };
  motos = computed(() => this.conteo('MOTO'));
  autos = computed(() => this.conteo('CARRO'));
}