import { Injectable, computed, signal } from '@angular/core';
import {
  Celda, Comprobante, ConsultaResultado, RegistroAcceso, Resultado, TipoComprobante, Vehiculo,
} from '../models/models';

const dias = (n: number): Date => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d;
};
const horasAtras = (h: number): Date => new Date(Date.now() - h * 3_600_000);

/**
 * Servicio con DATOS SIMULADOS (T07 y T11).
 * Cuando el backend de Camilo esté listo, solo se reemplaza el interior
 * de cada método por una llamada HttpClient. Los componentes no cambian.
 */
@Injectable({ providedIn: 'root' })
export class AccesoService {
  private readonly vehiculos: Vehiculo[] = [
    {
      placa: 'ABC123', tipo: 'CARRO', marca: 'Mazda 3', color: 'Rojo',
      cliente: { nombres: 'Laura', apellidos: 'Gómez Pérez', numeroDocumento: '1002345678', telefono: '3001234567' },
      mensualidad: { fechaInicio: dias(-10), fechaFin: dias(20), valor: 180000 },
    },
    {
      placa: 'DEF456', tipo: 'CARRO', marca: 'Chevrolet Spark', color: 'Blanco',
      cliente: { nombres: 'Carlos', apellidos: 'Ríos Mejía', numeroDocumento: '79845612', telefono: '3109876543' },
      mensualidad: { fechaInicio: dias(-5), fechaFin: dias(25), valor: 180000 },
    },
    {
      placa: 'XYZ987', tipo: 'CARRO', marca: 'Renault Logan', color: 'Gris',
      cliente: { nombres: 'Marta', apellidos: 'Suárez Díaz', numeroDocumento: '52123987', telefono: '3205558899' },
      mensualidad: { fechaInicio: dias(-45), fechaFin: dias(-15), valor: 180000 },
    },
    {
      placa: 'MOT45A', tipo: 'MOTO', marca: 'Yamaha FZ', color: 'Negro',
      cliente: { nombres: 'Andrés', apellidos: 'Torres Peña', numeroDocumento: '1090456321', telefono: '3157771122' },
      mensualidad: { fechaInicio: dias(-3), fechaFin: dias(27), valor: 70000 },
    },
  ];

  readonly celdas = signal<Celda[]>([
    { codigo: 'C-01', tipoVehiculo: 'CARRO', estado: 'LIBRE' },
    { codigo: 'C-02', tipoVehiculo: 'CARRO', estado: 'LIBRE' },
    { codigo: 'C-03', tipoVehiculo: 'CARRO', estado: 'OCUPADA' },
    { codigo: 'C-04', tipoVehiculo: 'CARRO', estado: 'LIBRE' },
    { codigo: 'C-05', tipoVehiculo: 'CARRO', estado: 'LIBRE' },
    { codigo: 'C-06', tipoVehiculo: 'CARRO', estado: 'LIBRE' },
    { codigo: 'C-07', tipoVehiculo: 'CARRO', estado: 'LIBRE' },
    { codigo: 'C-08', tipoVehiculo: 'CARRO', estado: 'MANTENIMIENTO' },
    { codigo: 'M-01', tipoVehiculo: 'MOTO', estado: 'LIBRE' },
    { codigo: 'M-02', tipoVehiculo: 'MOTO', estado: 'LIBRE' },
    { codigo: 'M-03', tipoVehiculo: 'MOTO', estado: 'LIBRE' },
    { codigo: 'M-04', tipoVehiculo: 'MOTO', estado: 'LIBRE' },
  ]);

  readonly registros = signal<RegistroAcceso[]>([
    {
      id: 1, placa: 'DEF456', celda: 'C-03', entrada: horasAtras(2.5),
      comprobanteEntrada: { numero: 'ENT-0001', tipo: 'ENTRADA', fechaEmision: horasAtras(2.5) },
    },
  ]);

  readonly activos = computed(() => this.registros().filter((r) => !r.salida));
  readonly libres = computed(() => this.celdas().filter((c) => c.estado === 'LIBRE').length);
  readonly ocupadas = computed(() => this.celdas().filter((c) => c.estado === 'OCUPADA').length);

  private contadorEntradas = 1;
  private contadorSalidas = 0;

  normalizar(placa: string): string {
    return placa.trim().toUpperCase().replace(/\s+/g, '');
  }

  consultarPlaca(placa: string): ConsultaResultado | null {
    const vehiculo = this.vehiculos.find((v) => v.placa === this.normalizar(placa));
    if (!vehiculo) return null;
    return {
      vehiculo,
      mensualidadVigente: vehiculo.mensualidad.fechaFin >= new Date(),
      dentroDelParqueadero: this.activos().some((r) => r.placa === vehiculo.placa),
    };
  }

  registrarIngreso(placa: string): Resultado<RegistroAcceso> {
    const consulta = this.consultarPlaca(placa);
    if (!consulta) return { ok: false, mensaje: 'La placa no está registrada en el sistema.' };
    if (!consulta.mensualidadVigente) return { ok: false, mensaje: 'La mensualidad de este vehículo está vencida.' };
    if (consulta.dentroDelParqueadero) return { ok: false, mensaje: 'Este vehículo ya se encuentra dentro del parqueadero.' };

    const celda = this.celdas().find((c) => c.estado === 'LIBRE' && c.tipoVehiculo === consulta.vehiculo.tipo);
    if (!celda) return { ok: false, mensaje: `No hay celdas libres para ${consulta.vehiculo.tipo === 'CARRO' ? 'carros' : 'motos'}.` };

    const registro: RegistroAcceso = {
      id: this.registros().length + 1,
      placa: consulta.vehiculo.placa,
      celda: celda.codigo,
      entrada: new Date(),
      comprobanteEntrada: this.nuevoComprobante('ENTRADA'),
    };
    this.registros.update((lista) => [...lista, registro]);
    this.cambiarEstadoCelda(celda.codigo, 'OCUPADA');
    return { ok: true, mensaje: 'Ingreso registrado correctamente.', dato: registro };
  }

  registrarSalida(placa: string): Resultado<RegistroAcceso> {
    const p = this.normalizar(placa);
    const activo = this.activos().find((r) => r.placa === p);
    if (!activo) return { ok: false, mensaje: 'No hay un ingreso activo para esta placa.' };

    const cerrado: RegistroAcceso = {
      ...activo,
      salida: new Date(),
      comprobanteSalida: this.nuevoComprobante('SALIDA'),
    };
    this.registros.update((lista) => lista.map((r) => (r.id === activo.id ? cerrado : r)));
    this.cambiarEstadoCelda(activo.celda, 'LIBRE');
    return { ok: true, mensaje: 'Salida registrada. La celda quedó libre.', dato: cerrado };
  }

  permanencia(r: RegistroAcceso): string {
    const fin = r.salida ?? new Date();
    const min = Math.max(0, Math.round((fin.getTime() - r.entrada.getTime()) / 60_000));
    return `${Math.floor(min / 60)} h ${min % 60} min`;
  }

  private cambiarEstadoCelda(codigo: string, estado: Celda['estado']): void {
    this.celdas.update((lista) => lista.map((c) => (c.codigo === codigo ? { ...c, estado } : c)));
  }

  private nuevoComprobante(tipo: TipoComprobante): Comprobante {
    const n = tipo === 'ENTRADA' ? ++this.contadorEntradas : ++this.contadorSalidas;
    return {
      numero: `${tipo === 'ENTRADA' ? 'ENT' : 'SAL'}-${String(n).padStart(4, '0')}`,
      tipo,
      fechaEmision: new Date(),
    };
  }
}
