import { Injectable, computed, signal } from '@angular/core';
import {
  Celda, Comprobante, ConsultaEntrada, RegistroAcceso, Resultado, TipoComprobante, Vehiculo,
} from '../models/models';

const OPERARIO = 'Diurno 1';
const horasAtras = (h: number): Date => new Date(Date.now() - h * 3_600_000);
const numero = (i: number): string => String(i + 1).padStart(2, '0');

const crearCeldas = (): Celda[] => [
  ...Array.from({ length: 70 }, (_, i): Celda => ({ codigo: `A-${numero(i)}`, tipoVehiculo: 'CARRO', estado: i === 0 ? 'OCUPADA' : 'LIBRE' })),
  ...Array.from({ length: 10 }, (_, i): Celda => ({ codigo: `M-${numero(i)}`, tipoVehiculo: 'MOTO', estado: 'LIBRE' })),
];

/**
 * Servicio con DATOS SIMULADOS, alineado con los mockups de Paul (HU-01 a HU-09).
 * Cuando el backend esté listo, solo cambia el interior de cada método por una llamada HttpClient.
 */
@Injectable({ providedIn: 'root' })
export class AccesoService {
  private readonly vehiculos: Vehiculo[] = [
    { placa: 'ABC123', tipo: 'CARRO', marca: 'Chevrolet Onix', color: 'Blanco', mensualidadFin: new Date(2026, 10, 21) },
    { placa: 'VEN001', tipo: 'CARRO', marca: 'Renault Logan', color: 'Rojo', mensualidadFin: new Date(2026, 8, 30) },
    { placa: 'INS001', tipo: 'CARRO', marca: 'Kia Rio', color: 'Azul', mensualidadFin: new Date(2026, 11, 31) },
    { placa: 'XYZ99A', tipo: 'MOTO', marca: 'Yamaha FZ', color: 'Negro', mensualidadFin: new Date(2026, 11, 15) },
  ];

  readonly celdas = signal<Celda[]>(crearCeldas());

  readonly registros = signal<RegistroAcceso[]>([
    {
      id: 1, placa: 'INS001', celda: 'A-01', entrada: horasAtras(30), operario: OPERARIO,
      comprobanteEntrada: { numero: 'AC-INS001-OPEN', tipo: 'ENTRADA', fechaEmision: horasAtras(30) },
    },
  ]);

  readonly activos = computed(() => this.registros().filter((r) => !r.salida));
  readonly libres = computed(() => this.celdas().filter((c) => c.estado === 'LIBRE').length);
  readonly ocupadas = computed(() => this.celdas().filter((c) => c.estado === 'OCUPADA').length);

  private contadorSalidas = 0;

  normalizar(placa: string): string {
    return placa.trim().toUpperCase().replace(/\s+/g, '');
  }

  /** Paso 1 de la entrada (HU-01, HU-03): consulta sin modificar nada. */
  consultarEntrada(placa: string): ConsultaEntrada {
    const v = this.vehiculos.find((x) => x.placa === this.normalizar(placa));
    if (!v) {
      return { estado: 'NO_REGISTRADO', mensaje: 'El vehículo no está registrado. No se permite el ingreso. No se modificó la ocupación.' };
    }
    const abierto = this.activos().find((r) => r.placa === v.placa);
    if (abierto) {
      return { estado: 'YA_DENTRO', vehiculo: v, celdaActual: abierto.celda, mensaje: 'Este vehículo ya tiene una permanencia abierta. No se puede registrar otra entrada.' };
    }
    if (v.mensualidadFin < new Date()) {
      return { estado: 'VENCIDA', vehiculo: v, mensaje: 'Mensualidad vencida. El vehículo no está autorizado para ingresar.' };
    }
    const delTipo = this.celdas().filter((c) => c.tipoVehiculo === v.tipo);
    if (!delTipo.some((c) => c.estado === 'LIBRE')) {
      const etiqueta = v.tipo === 'MOTO' ? 'motos' : 'automóviles';
      return { estado: 'SIN_CUPO', vehiculo: v, mensaje: `No hay celdas disponibles para este tipo de vehículo (${etiqueta} ${delTipo.length}/${delTipo.length}).` };
    }
    return { estado: 'AUTORIZADO', vehiculo: v, mensaje: '' };
  }

  /** Paso 2 (HU-02, HU-04): asigna celda y genera el comprobante. */
  confirmarEntrada(placa: string): Resultado<RegistroAcceso> {
    const c = this.consultarEntrada(placa);
    if (c.estado !== 'AUTORIZADO' || !c.vehiculo) return { ok: false, mensaje: c.mensaje };

    const celda = this.celdas().find((x) => x.estado === 'LIBRE' && x.tipoVehiculo === c.vehiculo!.tipo)!;
    const registro: RegistroAcceso = {
      id: this.registros().length + 1,
      placa: c.vehiculo.placa,
      celda: celda.codigo,
      entrada: new Date(),
      operario: OPERARIO,
      comprobanteEntrada: { numero: this.codigoComprobante(), tipo: 'ENTRADA', fechaEmision: new Date() },
    };
    this.registros.update((l) => [...l, registro]);
    this.cambiarEstadoCelda(celda.codigo, 'OCUPADA');
    return { ok: true, mensaje: 'Entrada registrada correctamente.', dato: registro };
  }

  /** Se ajusta en la Etapa 2 (salida por comprobante). */
  registrarSalida(placa: string): Resultado<RegistroAcceso> {
    const activo = this.activos().find((r) => r.placa === this.normalizar(placa));
    if (!activo) return { ok: false, mensaje: 'No hay un ingreso activo para esta placa.' };
    const cerrado: RegistroAcceso = {
      ...activo,
      salida: new Date(),
      comprobanteSalida: this.comprobanteSalida(),
    };
    this.registros.update((l) => l.map((r) => (r.id === activo.id ? cerrado : r)));
    this.cambiarEstadoCelda(activo.celda, 'LIBRE');
    return { ok: true, mensaje: 'Salida registrada. La celda quedó libre.', dato: cerrado };
  }

  permanencia(r: RegistroAcceso): string {
    const fin = r.salida ?? new Date();
    const min = Math.max(0, Math.round((fin.getTime() - r.entrada.getTime()) / 60_000));
    return `${Math.floor(min / 60)} h ${min % 60} min`;
  }

  private cambiarEstadoCelda(codigo: string, estado: Celda['estado']): void {
    this.celdas.update((l) => l.map((c) => (c.codigo === codigo ? { ...c, estado } : c)));
  }

  private codigoComprobante(): string {
    const letras = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const bloque = () => Array.from({ length: 4 }, () => letras[Math.floor(Math.random() * letras.length)]).join('');
    return `AC-${bloque()}-${bloque()}`;
  }

  private comprobanteSalida(): Comprobante {
    this.contadorSalidas++;
    const tipo: TipoComprobante = 'SALIDA';
    return { numero: `SAL-${String(this.contadorSalidas).padStart(4, '0')}`, tipo, fechaEmision: new Date() };
  }
}
